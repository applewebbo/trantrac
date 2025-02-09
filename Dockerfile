# pull official base image
FROM python:3.12-slim-bookworm

# set work directory
WORKDIR /app

# set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/srv
ENV PYTHONUNBUFFERED=1

# install uv and other dependencies
RUN apt-get update && apt-get install -y curl unzip
RUN pip install --upgrade pip uv
RUN python -m uv venv

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash

# Copy project files
COPY . /app

# Install DaisyUI using Bun in the project directory
RUN ~/.bun/bin/bun add -D daisyui@latest

# activate virtual env
ENV PATH=/app/.venv/bin:$PATH

# install Python dependencies
COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --frozen --no-dev --group prod --no-install-project

# expose port for granian
EXPOSE 80

# run entrypoint.sh
CMD ["sh", "./entrypoint.sh"]
