import httpx
import pytest

from qanalisa.jira.client import JiraClient, JiraError


def test_get_issue_requests_only_summary_and_description():
    captured = {}

    def handler(request: httpx.Request):
        captured["url"] = str(request.url)
        return httpx.Response(
            200,
            json={
                "key": "FN-14",
                "fields": {"summary": "Teste", "description": None},
            },
        )

    client = JiraClient(
        base_url="https://example.atlassian.net",
        email="qa@example.com",
        token="secret",
        transport=httpx.MockTransport(handler),
    )
    issue = client.get_issue("FN-14")

    assert issue.key == "FN-14"
    assert issue.title == "Teste"
    assert issue.description == ""
    assert "fields=summary%2Cdescription" in captured["url"]


@pytest.mark.parametrize("status", [401, 403, 404])
def test_get_issue_raises_safe_error_without_secret(status: int):
    def handler(request: httpx.Request):
        return httpx.Response(status, json={"errorMessages": ["failure"]})

    client = JiraClient(
        base_url="https://example.atlassian.net",
        email="qa@example.com",
        token="super-secret-token",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(JiraError) as exc_info:
        client.get_issue("FN-14")

    message = str(exc_info.value)
    assert "FN-14" in message
    assert str(status) in message
    assert "super-secret-token" not in message
