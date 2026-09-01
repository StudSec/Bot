FROM python:3.9-slim

RUN apt-get update && apt-get install -y wget firefox-esr pipx python3-venv
RUN pipx ensurepath
RUN pipx install poetry
RUN pipx list

# Setup the geckodriver for selenium
WORKDIR /tmp
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.37.1/geckodriver-v0.37.1-linux64.tar.gz
RUN tar -xzf geckodriver-v0.37.1-linux64.tar.gz
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin

# Install dependencies
WORKDIR /app
COPY pyproject.toml ./

# Copy over rest of the bot
COPY bot ./bot
RUN /root/.local/bin/poetry install

# Unbuffered to flush stdout
ENTRYPOINT /root/.local/bin/poetry run bot
