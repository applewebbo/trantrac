# pull official base image
FROM python:3.14-slim-bookworm

# set work directory
WORKDIR /app

# set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/srv
ENV PYTHONUNBUFFERED=1

# install uv and other dependencies (including WeasyPrint system libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip uv
RUN python -m uv venv

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash

# Copy project files
COPY . /app

# # Install DaisyUI using Bun
RUN ~/.bun/bin/bun install

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
