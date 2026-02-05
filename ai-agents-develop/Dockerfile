# syntax=docker/dockerfile:1.4

FROM public.ecr.aws/docker/library/python:3.11-bookworm

# Install apt dependencies
RUN apt-get update && \
    apt-get install -y jq git curl unzip libzbar0 && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip > /dev/null && \
    ./aws/install > /dev/null && \
    rm -rf awscliv2.zip aws && \
    mkdir -p -m 0600 ~/.ssh && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Copy package files first for better layer caching
COPY pyproject.toml ./

RUN --mount=type=ssh uv sync --active --extra service && . .venv/bin/activate && uv run playwright install && uv run playwright install chromium --with-deps --no-shell

ENV PATH="/app/.venv/bin:$PATH"

# Install Playwright and MCP early to catch dependency errors sooner
RUN npm init playwright@latest
RUN npm install -g @playwright/mcp@0.0.41
RUN npx playwright install chrome

EXPOSE 80

# Copy the rest of the application
COPY . /app

RUN chmod +x start_server.sh

CMD ["./start_server.sh"]
