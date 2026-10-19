from app.services.analyzer import analyze_files
from app.services.repository import validate_github_repo_url
from fastapi import HTTPException
import pytest


def test_detects_eval_and_shell_true_without_running_code():
    source = b"import subprocess\ndef x(value):\n    eval(value)\n    subprocess.run(value, shell=True)\n"
    result = analyze_files({"sample.py": source})
    rule_ids = {f["rule_id"] for f in result["findings"]}
    assert "PY-SEC-001" in rule_ids
    assert "PY-SEC-002" in rule_ids
    assert result["summary"]["files_analyzed"] == 1


def test_evidence_redacts_secret_values():
    result = analyze_files({"settings.py": b"API_KEY = 'super-secret-token-value-12345'\n"})
    findings = [f for f in result["findings"] if f["rule_id"] == "GEN-SEC-001"]
    assert findings
    assert "super-secret-token-value" not in findings[0]["evidence"]
    assert "REDACTED" in findings[0]["evidence"]


def test_skips_path_traversal_and_binary_files():
    result = analyze_files({"../../outside.py": b"eval('1')", "picture.png": b"\x89PNG\x00"})
    assert result["summary"]["files_analyzed"] == 0
    assert all("outside" not in f.get("path", "") for f in result["findings"])


def test_validates_github_host_and_shape():
    assert validate_github_repo_url("https://github.com/owner/repo")[0:2] == ("owner", "repo")
    with pytest.raises(HTTPException):
        validate_github_repo_url("http://127.0.0.1/private")
    with pytest.raises(HTTPException):
        validate_github_repo_url("https://github.com.evil.example/owner/repo")
    with pytest.raises(HTTPException):
        validate_github_repo_url("https://user:password@github.com/owner/repo")


def test_report_counts_are_derived_from_real_findings():
    result = analyze_files({"app.py": b"def f():\n    return 1\n"})
    assert result["summary"]["findings_total"] == len(result["findings"])
    assert sum(result["severity_counts"].values()) == len(result["findings"])


def test_ollama_provider_uses_structured_json(monkeypatch):
    import json
    from app.services import ai_explainer

    payload = {
        "executive_summary": "The demo has two supported source files.",
        "strengths": ["The source inventory is available."],
        "priority_actions": [],
        "architecture_notes": ["Imports are inferred statically."],
        "limitations": ["No code was executed."],
    }

    class FakeResponse:
        def raise_for_status(self):
            return None
        def json(self):
            return {"message": {"content": json.dumps(payload)}}

    class FakeClient:
        def __init__(self, timeout):
            assert timeout == 120
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def post(self, url, json):
            assert url.endswith("/api/chat")
            assert json["format"] == "json"
            assert json["stream"] is False
            return FakeResponse()

    monkeypatch.setattr(ai_explainer, "AI_PROVIDER", "ollama")
    monkeypatch.setattr(ai_explainer.httpx, "Client", FakeClient)
    result = ai_explainer.explain_analysis({"project": "fixture", "summary": {}, "findings": [], "languages": [], "architecture": {}}, "mentor")
    assert result["provider"] == "ollama"
    assert result["mode"] == "Local AI-assisted"
    assert result["executive_summary"] == payload["executive_summary"]

def test_openrouter_provider_uses_chat_completions_and_parses_json(monkeypatch):
    import json as jsonlib
    from app.services import ai_explainer

    payload = {
        "executive_summary": "Evidence-based summary.",
        "strengths": ["Repeatable source inventory."],
        "priority_actions": [],
        "architecture_notes": ["Imports are inferred statically."],
        "limitations": ["No code was executed."],
    }
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "model": "test/free-model",
                "choices": [{"message": {"content": jsonlib.dumps(payload)}}],
            }

    class FakeClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers, json):
            captured.update(url=url, headers=headers, request=json)
            return FakeResponse()

    monkeypatch.setattr(ai_explainer, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(ai_explainer, "OPENROUTER_API_KEY", "test-only-key")
    monkeypatch.setattr(ai_explainer, "OPENROUTER_BASE_URL", "https://openrouter.example/api/v1")
    monkeypatch.setattr(ai_explainer, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_explainer.httpx, "Client", FakeClient)

    result = ai_explainer.explain_analysis(
        {"project": "fixture", "summary": {}, "findings": [], "languages": [], "architecture": {}},
        "mentor",
    )

    assert captured["url"] == "https://openrouter.example/api/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-only-key"
    assert captured["request"]["model"] == "openrouter/free"
    assert captured["request"]["response_format"] == {"type": "json_object"}
    assert captured["request"]["stream"] is False
    assert result["provider"] == "openrouter"
    assert result["model"] == "test/free-model"
    assert result["mode"] == "Cloud AI-assisted"
    assert result["executive_summary"] == payload["executive_summary"]


def test_ask_question_supports_openrouter_with_bounded_context(monkeypatch):
    from app.services import ai_explainer

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "model": "test/free-model",
                "choices": [{"message": {"content": "Review the high-severity evidence first."}}],
            }

    class FakeClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, headers, json):
            captured.update(url=url, headers=headers, request=json)
            return FakeResponse()

    monkeypatch.setattr(ai_explainer, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(ai_explainer, "OPENROUTER_API_KEY", "test-only-key")
    monkeypatch.setattr(ai_explainer, "OPENROUTER_BASE_URL", "https://openrouter.example/api/v1")
    monkeypatch.setattr(ai_explainer, "OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(ai_explainer.httpx, "Client", FakeClient)

    result = ai_explainer.answer_question(
        {
            "project": "fixture",
            "summary": {"files_analyzed": 1},
            "findings": [],
            "files": [],
            "languages": [],
            "source": {},
            "architecture": {},
        },
        "What should I fix first?",
    )

    assert captured["url"] == "https://openrouter.example/api/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-only-key"
    assert captured["request"]["model"] == "openrouter/free"
    assert captured["request"]["messages"][-1]["content"].endswith("CURRENT QUESTION: What should I fix first?")
    assert result == {
        "answer": "Review the high-severity evidence first.",
        "provider": "openrouter",
        "model": "test/free-model",
    }

