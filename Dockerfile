FROM node:22-bookworm-slim AS interface
WORKDIR /interface
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini start.py ./
COPY scripts ./scripts
COPY --from=interface /interface/dist ./frontend/dist
EXPOSE 8000
CMD ["python", "start.py"]
