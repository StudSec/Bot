FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y wget firefox-esr pipx python3-venv
RUN pipx ensurepath
RUN pipx install poetry
RUN pipx list

# Setup the geckodriver for selenium
WORKDIR /tmp
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz
RUN tar xvfz geckodriver-v0.29.1-linux64.tar.gz
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin

# Copy over the bot and install
RUN mkdir -p app
WORKDIR /app
COPY pyproject.toml .env ./
COPY bot ./bot
RUN /root/.local/bin/poetry install

# Unbuffered to flush stdout
ENTRYPOINT /root/.local/bin/poetry run bot