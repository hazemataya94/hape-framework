FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN addgroup -S hape && adduser -S -G hape -u 10001 hape \
    && python -m pip install --upgrade pip

RUN pip install --upgrade hape && pip install --upgrade hape

USER hape
WORKDIR /home/hape

ENTRYPOINT ["hape"]
CMD ["--help"]
