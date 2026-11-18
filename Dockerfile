FROM python:3.11-slim

RUN useradd -m -u 1000 user
WORKDIR /app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

RUN mkdir -p /app/data && chown -R user:user /app/data

USER user
ENV HOME=/home/user

EXPOSE 7860

# Render (and most PaaS) injects $PORT; default to 7860 for local/HF Spaces.
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"
