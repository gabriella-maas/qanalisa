from qanalisa.jira.parser import parse_description


def test_parse_plain_text_description():
    assert parse_description("Regra simples") == "Regra simples"


def test_parse_adf_description():
    adf = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Regra A"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Regra B"}]},
        ],
    }
    assert parse_description(adf) == "Regra A\nRegra B"


def test_parse_empty_description():
    assert parse_description(None) == ""
