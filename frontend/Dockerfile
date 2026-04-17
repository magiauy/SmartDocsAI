FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir streamlit httpx

COPY index.py /app/index.py
COPY assets /app/assets

EXPOSE 8501

CMD ["streamlit", "run", "index.py", "--server.address=0.0.0.0", "--server.port=8501"]
