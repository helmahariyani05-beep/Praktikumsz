"""Pengujian format error JSON dan penanganan error global."""

from app.repositories import loan_repository


def test_unknown_route_returns_json_404(client):
    """Route yang tidak dikenal tetap mengembalikan JSON."""
    response = client.get("/tidak-ada")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json() == {"error": "Resource not found"}


def test_disallowed_method_returns_json_405(client):
    """HTTP method yang tidak diizinkan mengembalikan JSON."""
    response = client.delete("/items")

    assert response.status_code == 405
    assert response.is_json
    assert response.get_json() == {"error": "Method not allowed"}


def test_unhandled_error_returns_generic_json_500(
    client, make_item, monkeypatch
):
    """Error tak terduga tidak membocorkan detail internal ke client."""
    app = client.application
    app.config.update(TESTING=False, DEBUG=False)

    item = make_item(total_stock=5)

    def fail_create(*args, **kwargs):
        raise RuntimeError("detail internal rahasia")

    monkeypatch.setattr(loan_repository, "create", fail_create)

    response = client.post(
        "/loans",
        json={"student_id": "20240001", "item_id": item["id"], "quantity": 1},
    )

    assert response.status_code == 500
    assert response.is_json
    assert response.get_json() == {"error": "Internal server error"}
    assert "detail internal rahasia" not in response.get_data(as_text=True)
