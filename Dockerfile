FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-cloud.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-cloud.txt

COPY . .

RUN sed -i 's/\r$//' deploy/start.sh \
    && chmod +x deploy/start.sh \
    && mkdir -p /app/bootstrap_data /app/bootstrap_models /app/bootstrap_reports \
    && cp -a /app/data/. /app/bootstrap_data/ \
    && FIE_DATA_ROOT=/app/bootstrap_data \
       FIE_MODEL_DIR=/app/bootstrap_models \
       FIE_REPORTS_DIR=/app/bootstrap_reports \
       python setup_phase1_storage.py --min-count 10000 \
    && FIE_DATA_ROOT=/app/bootstrap_data \
       FIE_MODEL_DIR=/app/bootstrap_models \
       FIE_REPORTS_DIR=/app/bootstrap_reports \
       python build_phase1_data.py --min-count 10000 \
    && FIE_DATA_ROOT=/app/bootstrap_data \
       FIE_MODEL_DIR=/app/bootstrap_models \
       FIE_REPORTS_DIR=/app/bootstrap_reports \
       python train_phase1_models.py \
    && FIE_DATA_ROOT=/app/bootstrap_data \
       FIE_MODEL_DIR=/app/bootstrap_models \
       FIE_REPORTS_DIR=/app/bootstrap_reports \
       python index_phase1_rag.py

ENV FIE_ENV=cloud \
    FIE_HOST=0.0.0.0 \
    FIE_DATA_ROOT=/var/data \
    FIE_MODEL_DIR=/var/data/models \
    FIE_REPORTS_DIR=/var/data/reports \
    FIE_GENAI_PROVIDER=local \
    PORT=10000

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:10000/health', timeout=3)"

CMD ["sh", "deploy/start.sh"]
