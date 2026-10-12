# Alpine provides a much smaller runtime than the full Python image.
FROM python:3.13-alpine

# Avoid .pyc files and immediately forward Python logs to Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Use an unprivileged system user to limit the impact of a compromised process.
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy dependencies before source code so this expensive layer remains cached.
COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=appuser:appgroup app.py ./

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"

# CMD is the default runtime command and can be overridden by docker run.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "app:app"]
