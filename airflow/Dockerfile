FROM apache/airflow:3.1.8-python3.12

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils libgl1 && \
    rm -rf /var/lib/apt/lists/*
USER airflow

RUN pip install --no-cache-dir \
    torch torchvision --index-url https://download.pytorch.org/whl/cu121

RUN pip install --no-cache-dir \
    easyocr \
    pdf2image \
    minio \
    apache-airflow-providers-fab

RUN pip install --no-cache-dir spacy pymongo
RUN python -m spacy download fr_core_news_md

# Pré-télécharger les modèles EasyOCR français au build
RUN python -c "import easyocr; easyocr.Reader(['fr'], gpu=True)"
