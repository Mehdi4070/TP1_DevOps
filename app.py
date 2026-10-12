import os
import socket

from flask import Flask, jsonify
from redis import Redis
from redis.exceptions import RedisError


def create_redis_client() -> Redis:
    """Create the Redis client from environment variables."""
    return Redis(
        host=os.getenv("REDIS_HOST", "db-service"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def create_app(redis_client=None) -> Flask:
    app = Flask(__name__)
    client = redis_client or create_redis_client()

    @app.get("/")
    def index():
        try:
            hits = client.incr("hits")
        except RedisError:
            app.logger.exception("Redis is unavailable")
            return "Le compteur est temporairement indisponible.\n", 503

        container_id = socket.gethostname()
        return (
            f"Bonjour ! Cette page a été vue {hits} fois. "
            f"Je suis le conteneur {container_id}\n"
        )

    @app.get("/health")
    def health():
        try:
            client.ping()
        except RedisError:
            return jsonify(status="unhealthy"), 503
        return jsonify(status="healthy")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("APP_PORT", "5000")))
