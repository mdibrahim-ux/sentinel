import re

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["name"] == "Sentinal"


def test_rejects_non_github_url_before_job_creation():
    response = client.post("/api/analysis", json={"repository_url":"http://localhost:8000/admin"})
    assert response.status_code == 422


def test_demo_analysis_completes_and_report_is_a_real_pdf():
    submitted = client.post("/api/analysis/demo")
    assert submitted.status_code == 200
    job_id = submitted.json()["id"]
    completed = client.get(f"/api/analysis/{job_id}")
    assert completed.status_code == 200
    body = completed.json()
    assert body["status"] == "completed"
    assert body["analysis"]["summary"]["findings_total"] == len(body["analysis"]["findings"])
    pdf = client.get(f"/api/analysis/{job_id}/report.pdf")
    assert pdf.status_code == 200
    assert pdf.content[:5] == b"%PDF-"
    assert len(pdf.content) > 30_000
    page_objects = re.findall(rb"/Type\s*/Page(?!s)\b", pdf.content)
    assert len(page_objects) == 4


def test_upload_rejects_non_zip():
    response = client.post("/api/analysis/upload", files={"file": ("notes.txt", b"not a zip", "text/plain")})
    assert response.status_code == 415


def test_ask_sentinal_is_disabled_without_local_ollama(monkeypatch):
    import app.main as main_module
    monkeypatch.setattr(main_module, "AI_PROVIDER", "disabled")
    response = client.post(
        "/api/analysis/not-a-real-job/ask",
        json={"question": "What should I fix first?"},
    )
    assert response.status_code == 503
    assert "AI_PROVIDER" in response.json()["detail"] and "ollama" in response.json()["detail"]


def test_ask_sentinal_uses_the_selected_completed_analysis(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "AI_PROVIDER", "ollama")
    captured = {}

    def fake_answer(analysis, question, selected_path=None, history=None):
        captured.update(
            analysis=analysis,
            question=question,
            selected_path=selected_path,
            history=history,
        )
        return {"answer": "Review the high-severity evidence first.", "provider": "ollama", "model": "test-model"}

    monkeypatch.setattr(main_module, "answer_question", fake_answer)
    submitted = client.post("/api/analysis/demo")
    assert submitted.status_code == 200
    job_id = submitted.json()["id"]
    job = client.get(f"/api/analysis/{job_id}").json()
    assert job["status"] == "completed"
    selected_path = job["analysis"]["files"][0]["path"]

    response = client.post(
        f"/api/analysis/{job_id}/ask",
        json={
            "question": "What should I fix first?",
            "selected_path": selected_path,
            "history": [{"role": "user", "content": "Explain this project."}],
        },
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "Review the high-severity evidence first."
    assert captured["question"] == "What should I fix first?"
    assert captured["selected_path"] == selected_path
    assert captured["analysis"]["project"] == job["analysis"]["project"]
    assert captured["history"][0]["role"] == "user"


def test_profile_round_trips_through_persistent_store():
    payload = {
        "full_name": "Profile Test",
        "username": "profile_test_user",
        "headline": "Codebase analyst",
        "bio": "Evidence-led development",
        "location": "",
        "website": "https://example.com",
        "email": "profile-test@example.com",
        "email_public": False,
        "github_username": "octocat",
        "github_url": "https://github.com/octocat",
        "preferred_languages": ["Python", "TypeScript"],
        "technical_skills": ["FastAPI", "React"],
        "interests": ["Developer tools"],
        "role": "Student developer",
        "avatar_data_url": "",
        "default_dashboard": "Home",
        "notifications_enabled": True,
        "privacy_profile_public": False,
    }
    saved = client.put("/api/profile", json=payload)
    assert saved.status_code == 200
    assert saved.json()["full_name"] == "Profile Test"
    assert saved.json()["created_at"]

    loaded = client.get("/api/profile")
    assert loaded.status_code == 200
    assert loaded.json()["github_username"] == "octocat"
    assert loaded.json()["preferred_languages"] == ["Python", "TypeScript"]
    assert loaded.json()["created_at"] == saved.json()["created_at"]


def test_profile_rejects_non_http_urls():
    response = client.put("/api/profile", json={"website": "javascript:alert(1)"})
    assert response.status_code == 422


def test_ask_sentinal_accepts_openrouter_provider(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(main_module, "OPENROUTER_API_KEY", "test-only-key")
    monkeypatch.setattr(
        main_module,
        "answer_question",
        lambda analysis, question, selected_path=None, history=None: {
            "answer": "Review the highest-priority finding first.",
            "provider": "openrouter",
            "model": "test/free-model",
        },
    )

    submitted = client.post("/api/analysis/demo")
    assert submitted.status_code == 200
    job_id = submitted.json()["id"]

    response = client.post(
        f"/api/analysis/{job_id}/ask",
        json={"question": "What should I fix first?"},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "openrouter"
    assert response.json()["model"] == "test/free-model"
