# Stage 1: Build Python environment
FROM python:3.12-slim as builder

# Install uv, our package manager
RUN pip install uv

# Set up the working directory
WORKDIR /app

# Copy only the dependency definitions
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
# We use sync to ensure we use the locked versions
RUN uv sync

# ---

# Stage 2: Final runtime image
FROM python:3.12-slim

# Set up non-root user for security
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Install Google Chrome and necessary dependencies
# Based on official Google Chrome for Linux repository
RUN apt-get update && apt-get install -y curl gnupg --no-install-recommends \
    && curl -sS https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy the rest of the application code
COPY . .

# Change ownership to the non-root user
RUN chown -R appuser:appuser /home/appuser

# Switch to the non-root user
USER appuser

# Command to run the application, based on your Procfile
CMD ["uv", "run", "python", "scheduler.py"]
