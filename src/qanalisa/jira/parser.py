from __future__ import annotations

import re
from typing import Any

_BLOCK_TYPES = {
    "paragraph",
    "heading",
    "blockquote",
    "codeBlock",
    "listItem",
    "bulletList",
    "orderedList",
    "panel",
    "tableRow",
}


def _render_adf(node: Any) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_render_adf(item) for item in node)
    if not isinstance(node, dict):
        return str(node)

    node_type = node.get("type")
    if node_type == "text":
        return str(node.get("text", ""))
    if node_type == "hardBreak":
        return "\n"

    content = node.get("content", [])
    rendered = "".join(_render_adf(item) for item in content)
    if node_type in _BLOCK_TYPES and rendered and not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def parse_description(value: object) -> str:
    """Normalize Jira plain text or Atlassian Document Format to text."""
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, (dict, list)):
        text = _render_adf(value)
    else:
        text = str(value)

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
