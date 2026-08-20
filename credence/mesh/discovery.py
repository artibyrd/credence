"""4-Tier Multi-Source P2P Bootstrap Discovery Client for Credence Mesh.

Executes a prioritized fallback discovery chain:
1. Tier 1: Local SQLite Peer Cache (from prior runs)
2. Tier 2: Local Subnet UDP Beacon / mDNS Discovery
3. Tier 3: HTTPS Signed Seed File (https://seeds.credence.nexus/peers.json)
4. Tier 4: Static Fallback Gateway Seeds (PEER_SEEDS)

Resilient against network partitions, DNS failures, 404/500 HTTP errors,
and forged Sybil cartel signatures.
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
from pathlib import Path
from typing import List, Optional

import httpx
from sqlmodel import col, select

from credence.config import settings
from credence.db import get_async_session
from credence.mesh.seed import BootstrapSeedFile, verify_seed_file
from credence.models import PeerMetric

logger = logging.getLogger("credence.mesh.discovery")


class BootstrapDiscovery:
    """Multi-tier fallback peer discovery client."""

    def __init__(
        self,
        seed_url: Optional[str] = None,
        trusted_root_pubkey: Optional[str] = None,
        enable_local_beacon: bool = True,
        beacon_port: Optional[int] = None,
        timeout_sec: float = 2.0,
    ) -> None:
        self.seed_url = seed_url or settings.DEFAULT_SEED_URL
        self.trusted_root_pubkey = trusted_root_pubkey or settings.TRUSTED_ROOT_PUBKEY
        self.enable_local_beacon = enable_local_beacon and settings.ENABLE_LOCAL_DISCOVERY
        self.beacon_port = beacon_port or settings.DISCOVERY_BEACON_PORT
        self.timeout_sec = timeout_sec

    async def discover_peers(self) -> List[str]:
        """Execute 4-tier discovery fallback chain and return prioritized peer WebSocket URLs."""
        discovered: List[str] = []

        # Tier 1: Local Cache
        discovered.extend(await self._try_tier1())
        if len(discovered) >= 4:
            return self._deduplicate(discovered)

        # Tier 2: UDP Beacon
        if self.enable_local_beacon:
            discovered.extend(await self._try_tier2())
            if len(discovered) >= 4:
                return self._deduplicate(discovered)

        # Tier 3: HTTPS Seed File
        discovered.extend(await self._try_tier3())

        # Tier 4: Static Fallback Seeds
        discovered.extend(self._discover_from_static_seeds())

        return self._deduplicate(discovered)

    async def _try_tier1(self) -> List[str]:
        try:
            cached = await self._discover_from_local_cache()
            if cached:
                logger.info(f"Tier 1 (Local Cache): Discovered {len(cached)} cached peer(s).")
            return cached
        except Exception as e:
            logger.debug(f"Tier 1 skipped: {e}")
            return []

    async def _try_tier2(self) -> List[str]:
        try:
            beacon = await self._discover_from_local_beacon()
            if beacon:
                logger.info(f"Tier 2 (UDP Beacon): Discovered {len(beacon)} local peer(s).")
            return beacon
        except Exception as e:
            logger.debug(f"Tier 2 error: {e}")
            return []

    async def _try_tier3(self) -> List[str]:
        try:
            seeds = await self._discover_from_seed_file(self.seed_url)
            if seeds:
                logger.info(f"Tier 3 (Seed File): Discovered {len(seeds)} verified seed peer(s).")
            return seeds
        except Exception as e:
            logger.warning(f"Tier 3 error from {self.seed_url}: {e}")
            return []

    async def _discover_from_local_cache(self) -> List[str]:
        """Query top-quality peers recorded in local SQLite database."""
        async with get_async_session() as session:
            stmt = (
                select(PeerMetric)
                .where(PeerMetric.quality_score >= 0.70)
                .order_by(col(PeerMetric.quality_score).desc())
                .limit(10)
            )
            results = await session.exec(stmt)
            records = results.all()
            return [r.ws_url for r in records if r.ws_url]
        return []

    async def _discover_from_local_beacon(self) -> List[str]:
        """Listen briefly for UDP broadcast beacons on local subnet."""
        peers: List[str] = []

        def _listen_udp() -> List[str]:
            discovered_urls: List[str] = []
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(self.timeout_sec)
            try:
                sock.bind(("", self.beacon_port))
                while True:
                    try:
                        data, _addr = sock.recvfrom(2048)
                        msg = json.loads(data.decode("utf-8"))
                        if msg.get("protocol") == "credence-mesh/1.0" and "ws_url" in msg:
                            discovered_urls.append(msg["ws_url"])
                    except socket.timeout:
                        break
                    except Exception:
                        break
            except Exception as ex:
                logger.debug(f"UDP beacon listen socket error: {ex}")
            finally:
                sock.close()
            return discovered_urls

        loop = asyncio.get_running_loop()
        try:
            peers = await asyncio.wait_for(loop.run_in_executor(None, _listen_udp), timeout=self.timeout_sec + 0.5)
        except asyncio.TimeoutError:
            pass

        return peers

    async def _discover_from_seed_file(self, url_or_path: str) -> List[str]:
        """Fetch, parse, and cryptographically verify remote or local seed manifest."""
        raw_text: str = ""

        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                response = await client.get(url_or_path)
                if response.status_code != 200:
                    logger.warning(f"Seed manifest fetch returned HTTP {response.status_code} from {url_or_path}")
                    return []
                raw_text = response.text
        else:
            file_path = Path(url_or_path)
            if not file_path.exists():
                logger.warning(f"Local seed manifest path does not exist: {file_path}")
                return []
            raw_text = file_path.read_text(encoding="utf-8")

        # Parse and validate schema
        data = json.loads(raw_text)
        seed_manifest = BootstrapSeedFile.model_validate(data)

        # Cryptographically verify root Ed25519 signature
        is_valid = verify_seed_file(seed_manifest, trusted_root_pubkey=self.trusted_root_pubkey)
        if not is_valid:
            logger.error(
                f"❌ REJECTED SEED MANIFEST: Invalid cryptographic root signature or expired manifest from {url_or_path}"
            )
            return []

        logger.info(
            f"✅ Validated signed seed manifest ({len(seed_manifest.seed_nodes)} nodes, expires: {seed_manifest.expires_at.isoformat()})"
        )

        return [node.ws_url for node in seed_manifest.seed_nodes if node.ws_url]

    def _discover_from_static_seeds(self) -> List[str]:
        """Extract static fallback peer seed URLs from configuration."""
        if not settings.PEER_SEEDS:
            return []
        return [s.strip() for s in settings.PEER_SEEDS.split(",") if s.strip()]

    def _deduplicate(self, urls: List[str]) -> List[str]:
        """Remove duplicates while preserving original order."""
        seen = set()
        deduped = []
        for url in urls:
            if url and url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped
