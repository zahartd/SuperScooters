FROM python:3.13-slim

WORKDIR /app

COPY stubs/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PYTHONPATH=/app

CMD ["python", "fastapi_stubs.py"]
