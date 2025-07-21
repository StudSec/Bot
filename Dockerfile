FROM python:3.9-slim

# Copy over rest of the bot
COPY bot ./bot
RUN /root/.local/bin/poetry install

# Unbuffered to flush stdout
ENTRYPOINT /root/.local/bin/poetry run bot

FROM python:3.9-slim AS base

ARG DEV=false
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

RUN apt update && \
    apt install -y firefox-esr

# ------------------ #
# Builder Setup      #
# ------------------ #

FROM base AS builder

RUN apt update && \
    apt install -y wget

WORKDIR /tmp
RUN wget -qO- \
    https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz | tar xvz \
    && chmod +x geckodriver \
    && mv geckodriver /usr/local/bin

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app
COPY pyproject.toml ./
RUN pip install poetry==1.8.3
RUN if [ $DEV ]; then \
    poetry install --with dev --no-root && rm -rf $POETRY_CACHE_DIR; \
    else \
    poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR; \
    fi

# ------------------ #
# Runtime Stage      #
# ------------------ #

FROM base AS runtime

WORKDIR /app
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY .env ./
COPY bot ./bot

ENTRYPOINT ["python", "-m", "bot.main"]
