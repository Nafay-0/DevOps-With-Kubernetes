FROM python:3.11-slim

WORKDIR /app

# Install requests library
RUN pip install --no-cache-dir requests

# Copy the script
COPY random-todo.py .

# Make it executable
RUN chmod +x random-todo.py

# Run the script
CMD ["python", "random-todo.py"]
