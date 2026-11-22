"""Google Cloud Vertex AI Model Garden Provider (Model-as-a-Service / MaaS)."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, Optional

import httpx

from credence.pipeline.adapters_base import BaseLLMProvider, LLMResponse


class VertexModelGardenProvider(BaseLLMProvider):
    """Google Cloud Vertex AI Model Garden Provider (Model-as-a-Service / MaaS).

    Requires explicit project_id or GCP environment configuration (GOOGLE_CLOUD_PROJECT,
    GCP_PROJECT_ID, or CLOUDSDK_CORE_PROJECT) plus an OAuth2 Bearer token.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        model_name: str = "meta/llama-3.3-70b-instruct-maas",
        access_token: Optional[str] = None,
        max_output_tokens: int = 1024,
    ):
        self.project_id = (
            project_id
            or os.environ.get("CLOUDSDK_CORE_PROJECT")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
            or os.environ.get("GCP_PROJECT_ID")
            or ""
        )
        self.location = location or os.environ.get("CLOUDSDK_COMPUTE_REGION") or "us-central1"
        self.model_name = model_name
        self.access_token = access_token if access_token is not None else (os.environ.get("VERTEX_BEARER_TOKEN") or "")
        self.max_output_tokens = max_output_tokens

    def has_credentials(self) -> bool:
        return bool(self.project_id and (self.access_token or os.environ.get("VERTEX_BEARER_TOKEN")))

    def _get_bearer_token(self) -> str:
        if self.access_token:
            return self.access_token
        try:
            import google.auth
            from google.auth.transport.requests import Request

            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            credentials.refresh(Request())
            if credentials.token:
                return str(credentials.token)
        except Exception:
            pass

        gcloud_bin = shutil.which("gcloud")
        if gcloud_bin:
            try:
                res = subprocess.run(  # noqa: S603
                    [gcloud_bin, "auth", "print-access-token"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0:
                    token = res.stdout.strip()
                    if token:
                        return token
            except Exception:
                pass
        return ""

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        thinking_budget: int = 0,
        temperature: float = 0.1,
    ) -> LLMResponse:
        token = self._get_bearer_token()
        if not token:
            raise ValueError(
                "GCP OAuth2 Bearer token is required for VertexModelGardenProvider. Run 'gcloud auth login' or set VERTEX_BEARER_TOKEN."
            )
        if not self.project_id:
            raise ValueError(
                "GCP Project ID is required for VertexModelGardenProvider. Set GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID."
            )

        url = (
            f"https://{self.location}-aiplatform.googleapis.com/v1/projects/"
            f"{self.project_id}/locations/{self.location}/publishers/{self.model_name}:rawPredict"
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "max_tokens": self.max_output_tokens,
            "temperature": temperature,
        }
        if system_instruction:
            payload["system"] = system_instruction

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Vertex Model Garden API error ({resp.status_code}): {resp.text[:200]}")
            data = resp.json()
            text = ""
            if "choices" in data and len(data["choices"]) > 0:
                text = data["choices"][0].get("message", {}).get("content", "") or data["choices"][0].get("text", "")
            elif "output" in data:
                text = data["output"]
            elif "text" in data:
                text = data["text"]
            else:
                text = str(data)

            usage = data.get("usage", {})
            in_tok = usage.get("prompt_tokens", len(prompt) // 4)
            out_tok = usage.get("completion_tokens", len(text) // 4)
            return LLMResponse(
                text=text,
                prompt_tokens=in_tok,
                completion_tokens=out_tok,
                thinking_tokens=thinking_budget if "r1" in self.model_name else 0,
                provider_name="vertex_model_garden",
                model_name=self.model_name,
            )
