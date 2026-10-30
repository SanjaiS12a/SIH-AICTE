FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements.lock ./
RUN --mount=type=bind,source=.wheels,target=/wheels --mount=type=cache,target=/root/.cache/pip \
    if ls /wheels/torch*.whl >/dev/null 2>&1; then pip install --no-deps /wheels/torch*.whl; \
    else pip install --no-deps --timeout 180 torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu; fi \
    && pip install --find-links=/wheels --timeout 180 -r requirements.txt
COPY manage.py calibration.json ./
COPY config ./config
COPY cases ./cases
COPY templates ./templates
ENV PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
