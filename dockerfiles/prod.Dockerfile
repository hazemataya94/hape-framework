FROM python:3.9-bullseye

RUN apt update && apt install -y openssh-client git \
    && mkdir -p /root/.ssh
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt 
RUN pip install -r /app/requirements.txt

COPY ./src /app/src
COPY ./github-migrator.py /app/github-migrator.py

RUN rm -f /root/.ssh/*

CMD ["python", "/app/src/controllers/github-migrator.py"]
