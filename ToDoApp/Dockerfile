FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn python-dotenv requests

COPY . .

CMD ["python", "main.py"]
