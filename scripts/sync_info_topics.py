#!/usr/bin/env python3
"""Automated Synchronizer for Workstation Info Modals and Documentation Topic Index.

Governed by Invariant: Universal 4-Way Feature Parity & Anti-Drift Architecture.
Architecture: Single-Responsibility CLI Tool (<120 LOC).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def sync_topics() -> int:
    """Parse INFO_TOPICS from credence-workstation.js and update topic-index.md."""
    repo_root = Path(__file__).resolve().parents[1]
    ws_js_path = repo_root / "web" / "assets" / "credence-workstation.js"
    docs_topic_index_path = repo_root.parent / "credence-docs" / "docs" / "topic-index.md"

    if not ws_js_path.exists():
        print(f"❌ Error: Could not find {ws_js_path}", file=sys.stderr)
        return 1

    if not docs_topic_index_path.exists():
        print(f"❌ Error: Could not find {docs_topic_index_path}", file=sys.stderr)
        return 1

    ws_content = ws_js_path.read_text(encoding="utf-8")
    start = ws_content.find("const INFO_TOPICS = {")
    end = ws_content.find(
        "};\n\n// -----------------------------------------------------------------------------", start
    )
    if end == -1:
        end = ws_content.find("};\n\n//", start)

    block = ws_content[start:end]
    topic_matches = re.findall(r"^\s{2}([a-z0-9_]+):\s*\{([^}]+(?:\{[^}]+\}[^}]+)*)\},?", block, re.MULTILINE)

    if not topic_matches:
        print("❌ Error: No topic definitions found in INFO_TOPICS block", file=sys.stderr)
        return 1

    rows = []
    rows.append(
        "| Topic Key | Topic Name & Domain | Classification | Bound Invariant Slugs | CLI Tool | Authoritative Blueprint / Essay |"
    )
    rows.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    for key, body in topic_matches:
        title_m = re.search(r"title:\s*\"([^\"]+)\"", body)
        icon_m = re.search(r"icon:\s*\"([^\"]+)\"", body)
        tag_m = re.search(r"tag:\s*\"([^\"]+)\"", body)
        cli_m = re.search(r"cli:\s*\"([^\"]+)\"", body)
        invar_m = re.findall(r"\"(inv-[a-z0-9-]+)\"", body)
        link_m = re.search(r"\{\s*label:\s*\"([^\"]+)\",\s*url:\s*\"([^\"]+)\"", body)

        title = title_m.group(1) if title_m else key.replace("_", " ").title()
        icon = icon_m.group(1) if icon_m else "ℹ️"
        tag = tag_m.group(1) if tag_m else "SYSTEM"
        cli = cli_m.group(1) if cli_m else f"credence {key}"

        inv_links = ", ".join(f"[`{inv}`](invariants.md#{inv})" for inv in invar_m) if invar_m else "—"

        if link_m:
            lbl, url = link_m.group(1), link_m.group(2)
            lbl_clean = re.sub(r"^[📘🧪✍️📰🔬🚀\s]+", "", lbl)
            if "docs.credence.run/" in url:
                doc_path = url.split("docs.credence.run/")[-1]
                author_link = f"[{lbl_clean}]({doc_path}.md)"
            elif "docs.credence.run#" in url:
                doc_path = url.split("#")[-1]
                author_link = f"[{lbl_clean}]({doc_path}.md)"
            elif "blog.credence.run/" in url:
                blog_slug = url.split("blog.credence.run/")[-1]
                author_link = f"[{lbl_clean}](../blog/{blog_slug}.md)"
            elif "blog.credence.run#" in url:
                blog_slug = url.split("#")[-1]
                author_link = f"[{lbl_clean}](../blog/{blog_slug}.md)"
            else:
                author_link = f"[{lbl_clean}]({url})"
        else:
            author_link = "[The Invariant Bible](invariants.md)"

        rows.append(f"| `{key}` | {icon} {title} | `{tag}` | {inv_links} | `{cli}` | {author_link} |")

    new_table_str = "\n".join(rows)

    doc_content = docs_topic_index_path.read_text(encoding="utf-8")
    marker_start = "<!-- BEGIN_MODAL_REGISTRY -->"
    marker_end = "<!-- END_MODAL_REGISTRY -->"

    if marker_start in doc_content and marker_end in doc_content:
        pre = doc_content[: doc_content.find(marker_start) + len(marker_start)]
        post = doc_content[doc_content.find(marker_end) :]
        updated_doc = f"{pre}\n{new_table_str}\n{post}"
    else:
        heading = "## 🗂️ 11. Workstation & Dashboard Knowledge Modal Registry"
        if heading in doc_content:
            head_idx = doc_content.find(heading)
            table_start = doc_content.find("| Topic Key |", head_idx)
            table_end = doc_content.find("\n\n---", table_start)
            if table_end == -1:
                table_end = doc_content.find("\n---", table_start)

            pre = doc_content[:table_start]
            post = doc_content[table_end:] if table_end != -1 else ""
            updated_doc = f"{pre}{marker_start}\n{new_table_str}\n{marker_end}{post}"
        else:
            print("❌ Error: Could not locate Section 11 header in topic-index.md", file=sys.stderr)
            return 1

    docs_topic_index_path.write_text(updated_doc, encoding="utf-8")
    print(f"✅ Successfully synchronized {len(topic_matches)} info modal topics into {docs_topic_index_path.name}!")
    return 0


if __name__ == "__main__":
    sys.exit(sync_topics())
