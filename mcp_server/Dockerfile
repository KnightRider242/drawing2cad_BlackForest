# Build from repository root:
# docker build -f mcp_server/Dockerfile -t drawing2cad-mcp:local .
ARG MAMBA_DOCKERFILE_ACTIVATE=1
FROM mambaorg/micromamba:1.5.8

COPY --chown=$MAMBA_USER:$MAMBA_USER mcp_server/environment.yml /tmp/environment.yml
RUN micromamba install --yes --name base --file /tmp/environment.yml && \
    micromamba clean --all --yes

WORKDIR /app/backend
COPY --chown=$MAMBA_USER:$MAMBA_USER backend/app ./app
RUN mkdir -p /app/backend/outputs

ENV PYTHONDONTWRITEBYTECODE=1
CMD ["python", "-m", "app.mcp_server"]
