# Imagen única: compila el frontend y lo sirve junto a la API en el mismo origen.
FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini seed.py ./
COPY --from=frontend /build/dist frontend/dist
RUN useradd --create-home orqentiva
USER orqentiva
EXPOSE 8000
# DATABASE_URL, AUTH_ALLOWED_ORIGINS y AUTH_COOKIE_SECURE se configuran en el proveedor.
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
