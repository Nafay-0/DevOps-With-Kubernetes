FROM python:3.12-alpine

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Knative uses PORT environment variable (defaults to 8080)
ENV PORT=8080

CMD ["python", "-u", "main.py"]

