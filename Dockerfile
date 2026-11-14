# syntax=docker/dockerfile:1
#
# Medical AI evidence workbench - engineering-alpha container image (chunk C3).
#
# Status: proposed deployment asset. Building this image is not a deployment, and
# no public, pilot, commercial or clinical release is authorised by it.
#
# The base image is pinned by digest. Refresh the digest deliberately (and record
# it in the C3 evidence record) when the base image is updated.
ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

FROM ${PYTHON_IMAGE} AS build
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /src
COPY deploy/requirements.lock.txt deploy/requirements.lock.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r deploy/requirements.lock.txt
COPY pyproject.toml README.md ./
COPY src ./src
RUN /opt/venv/bin/pip install --no-deps .

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    MEDICAL_AI_HOST=0.0.0.0 \
    MEDICAL_AI_PORT=8000 \
    MEDICAL_AI_TRACE_DB=/var/lib/medical-ai/medical_ai_traces.sqlite3 \
    MEDICAL_AI_PILOT_SESSION_DB=/var/lib/medical-ai/pilot_sessions.sqlite3
RUN groupadd --system --gid 10001 medical-ai \
    && useradd --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin medical-ai \
    && install -d -o 10001 -g 10001 -m 0700 /var/lib/medical-ai
COPY --from=build /opt/venv /opt/venv
VOLUME /var/lib/medical-ai
EXPOSE 8000
USER 10001:10001
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('MEDICAL_AI_PORT', '8000') + '/health', timeout=3).status == 200 else 1)"]
ENTRYPOINT ["medical-ai-serve"]
