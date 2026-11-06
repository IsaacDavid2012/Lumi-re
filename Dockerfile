FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask requests gunicorn pynacl curl_cffi

COPY . /app

EXPOSE 5000

CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "--timeout", "30", "--limit-request-line", "4094", "--limit-request-fields", "50", "--limit-request-field_size", "8190", "app:app"]
