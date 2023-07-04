FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y wget firefox-esr

RUN mkdir -p bot

WORKDIR /tmp
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz
RUN tar xvfz geckodriver-v0.29.1-linux64.tar.gz
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin

WORKDIR /bot
ADD requirements.txt .
RUN pip install -r requirements.txt

ADD main.py .
ADD config.py .
COPY Modules ./Modules

# Unbuffered to flush stdout
ENTRYPOINT python3 -u main.py