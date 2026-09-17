from __future__ import annotations

import httpx

from qanalisa.jira.parser import parse_description
from qanalisa.models import JiraIssue


class JiraError(RuntimeError):
    """Safe Jira read error that never includes credentials."""


class JiraClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        token: str,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            auth=(email, token),
            transport=transport,
            timeout=timeout_seconds,
            headers={"Accept": "application/json"},
        )

    def get_issue(self, issue_key: str) -> JiraIssue:
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}"
        try:
            response = self._client.get(url, params={"fields": "summary,description"})
        except httpx.HTTPError as exc:
            raise JiraError(f"Falha ao consultar {issue_key} no Jira: erro de conexão.") from exc

        if response.status_code != 200:
            raise JiraError(
                f"Não foi possível carregar {issue_key} no Jira (HTTP {response.status_code})."
            )

        try:
            payload = response.json()
            fields = payload.get("fields") or {}
            return JiraIssue(
                key=str(payload.get("key") or issue_key),
                title=str(fields.get("summary") or ""),
                description=parse_description(fields.get("description")),
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise JiraError(f"Resposta inválida do Jira ao carregar {issue_key}.") from exc
