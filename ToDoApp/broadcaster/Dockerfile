FROM python:3.11-slim
WORKDIR /app
RUN pip install nats-py aiohttp
COPY main.py .
CMD ["python", "main.py"]
