# api/Dockerfile (y web/Dockerfile)
FROM python:3.13-slim-bookworm

# Instalamos herramientas básicas
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copiamos uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# --- CAMBIO CRUCIAL ---
# Creamos el entorno virtual en /opt/venv (fuera de /app)
# Esto evita que el volumen de tu código local lo oculte o lo rompa
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
ENV UV_COMPILE_BYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Instalamos dependencias
COPY pyproject.toml uv.lock* ./

# uv instalará todo en /opt/venv gracias a la variable de entorno
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]