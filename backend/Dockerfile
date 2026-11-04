FROM python:3.12-slim

# The worker starts sandbox containers through the host's Docker daemon, so it only needs the CLI.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL "https://download.docker.com/linux/static/stable/$(uname -m)/docker-27.5.1.tgz" \
    | tar -xz --strip-components=1 -C /usr/local/bin docker/docker \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Development installs the test tools too; the production compose file passes requirements.txt.
ARG REQUIREMENTS=requirements-dev.txt
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r ${REQUIREMENTS}
COPY . .
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
