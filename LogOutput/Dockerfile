FROM python:3.12-slim
WORKDIR /app
RUN pip install fastapi uvicorn requests
COPY writer.py reader.py ./
# Default to reader, but can be overridden
CMD ["python", "reader.py"]