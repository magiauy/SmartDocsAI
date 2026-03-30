FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-libmysqlclient-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/dev.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
