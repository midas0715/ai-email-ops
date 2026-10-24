import io

import pytest
from docx import Document
from pypdf import PdfWriter

from ai_email_ops.app.security import ROLE_ORG, create_access_token


def org_auth(org):
    return {"Authorization": f"Bearer {create_access_token(org.id, ROLE_ORG)}"}


@pytest.fixture
def fake_knowledge(monkeypatch):
    """Replace the slow AI storage with fakes that just remember what they were asked."""
    calls = {"ingested": [], "deleted": []}

    def fake_ingest(organization_id, document_id, filename, content):
        calls["ingested"].append(
            {"org": organization_id, "doc": document_id, "name": filename, "text": content}
        )
        return 3

    def fake_delete(document_id, organization_id):
        calls["deleted"].append((document_id, organization_id))

    monkeypatch.setattr("ai_email_ops.app.routes_knowledge.ingest_text", fake_ingest)
    monkeypatch.setattr("ai_email_ops.app.routes_knowledge.delete_document_chunks", fake_delete)
    return calls


def upload(client, org, filename, data, content_type="application/octet-stream"):
    return client.post(
        "/orgs/me/knowledge",
        files={"file": (filename, data, content_type)},
        headers=org_auth(org),
    )


def blank_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def make_docx(text):
    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_upload_txt_stores_document_and_chunks(client, org, fake_knowledge):
    response = upload(client, org, "policy.txt", b"Refunds within 30 days.", "text/plain")

    assert response.status_code == 201
    assert response.json()["filename"] == "policy.txt"
    assert response.json()["chunk_count"] == 3
    assert fake_knowledge["ingested"][0]["org"] == org.id
    assert "Refunds" in fake_knowledge["ingested"][0]["text"]
    listed = client.get("/orgs/me/knowledge", headers=org_auth(org)).json()
    assert [d["filename"] for d in listed] == ["policy.txt"]


def test_upload_docx_text_is_extracted(client, org, fake_knowledge):
    data = make_docx("Duplicate charges are refunded in 5 to 7 days.")

    response = upload(client, org, "refunds.docx", data)

    assert response.status_code == 201
    assert "refunded in 5 to 7 days" in fake_knowledge["ingested"][0]["text"]


def test_unsupported_file_type_is_415(client, org, fake_knowledge):
    assert upload(client, org, "virus.exe", b"MZ...").status_code == 415


def test_fake_pdf_is_422(client, org, fake_knowledge):
    assert upload(client, org, "fake.pdf", b"this is not really a pdf").status_code == 422


def test_pdf_without_text_is_422(client, org, fake_knowledge):
    response = upload(client, org, "scan.pdf", blank_pdf())

    assert response.status_code == 422
    assert "OCR" in response.json()["detail"]


def test_empty_text_file_is_422(client, org, fake_knowledge):
    assert upload(client, org, "empty.txt", b"  \n ").status_code == 422


def test_too_big_file_is_413(client, org, fake_knowledge, monkeypatch):
    monkeypatch.setattr("ai_email_ops.app.routes_knowledge.MAX_UPLOAD_BYTES", 10)

    assert upload(client, org, "big.txt", b"x" * 11).status_code == 413


def test_same_filename_twice_is_409(client, org, fake_knowledge):
    assert upload(client, org, "policy.txt", b"First version").status_code == 201
    assert upload(client, org, "policy.txt", b"Second version").status_code == 409


def test_failed_embedding_saves_nothing(client, org, fake_knowledge, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("Ollama is down")

    monkeypatch.setattr("ai_email_ops.app.routes_knowledge.ingest_text", broken)

    response = upload(client, org, "policy.txt", b"Refunds within 30 days.")

    assert response.status_code == 503
    assert client.get("/orgs/me/knowledge", headers=org_auth(org)).json() == []
    assert len(fake_knowledge["deleted"]) == 1  # leftovers were cleaned up


def test_delete_removes_chunks_and_row(client, org, fake_knowledge):
    document_id = upload(client, org, "policy.txt", b"Refunds within 30 days.").json()["id"]

    response = client.delete(f"/orgs/me/knowledge/{document_id}", headers=org_auth(org))

    assert response.status_code == 204
    assert (document_id, org.id) in fake_knowledge["deleted"]
    assert client.get("/orgs/me/knowledge", headers=org_auth(org)).json() == []


def test_other_organization_cannot_delete_or_see_documents(
    client, org, other_org, fake_knowledge
):
    document_id = upload(client, org, "policy.txt", b"Refunds within 30 days.").json()["id"]

    assert client.delete(f"/orgs/me/knowledge/{document_id}", headers=org_auth(other_org)).status_code == 404
    assert client.get("/orgs/me/knowledge", headers=org_auth(other_org)).json() == []


def test_two_organizations_can_use_the_same_filename(client, org, other_org, fake_knowledge):
    assert upload(client, org, "policy.txt", b"Org one text").status_code == 201
    assert upload(client, other_org, "policy.txt", b"Org two text").status_code == 201


def test_agent_token_cannot_upload(client, login, make_agent, fake_knowledge):
    asha = make_agent("asha")

    response = client.post(
        "/orgs/me/knowledge",
        files={"file": ("policy.txt", b"hello", "text/plain")},
        headers=login(asha),
    )

    assert response.status_code == 401