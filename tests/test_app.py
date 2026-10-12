from unittest.mock import Mock

from redis.exceptions import ConnectionError

from app import create_app


def test_index_increments_counter_and_returns_container_id(monkeypatch):
    redis_client = Mock()
    redis_client.incr.return_value = 7
    monkeypatch.setattr("app.socket.gethostname", lambda: "container-abc123")
    client = create_app(redis_client).test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.text == (
        "Bonjour ! Cette page a été vue 7 fois. "
        "Je suis le conteneur container-abc123\n"
    )
    redis_client.incr.assert_called_once_with("hits")


def test_index_returns_503_when_redis_is_unavailable():
    redis_client = Mock()
    redis_client.incr.side_effect = ConnectionError("Redis unavailable")
    client = create_app(redis_client).test_client()

    response = client.get("/")

    assert response.status_code == 503
    assert "temporairement indisponible" in response.text


def test_health_returns_healthy():
    redis_client = Mock()
    client = create_app(redis_client).test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}
    redis_client.ping.assert_called_once_with()


def test_health_returns_503_when_redis_is_unavailable():
    redis_client = Mock()
    redis_client.ping.side_effect = ConnectionError("Redis unavailable")
    client = create_app(redis_client).test_client()

    response = client.get("/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unhealthy"}
