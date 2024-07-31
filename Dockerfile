# Use the official Python 3.12 Alpine image from the Docker Hub
FROM python:3.12-alpine as builder

# Set the working directory in the container
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev curl

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ---

# Use a smaller image for the final runtime environment
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy the rest of the application code into the container
COPY . .

# Add health check script
COPY health_check.py .

# Health check command
HEALTHCHECK --interval=1m --timeout=10s --start-period=30s --retries=3 CMD ["python", "health_check.py"]

# Command to run the bot
CMD ["python", "bot.py"]
