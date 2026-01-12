FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
RUN pip install fastapi uvicorn psycopg2-binary
COPY main.py .
CMD ["python", "main.py"]
