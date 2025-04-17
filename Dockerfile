FROM python:3.9-slim

WORKDIR /app

# Install curl for webhook management
RUN apt-get update && apt-get install -y curl && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create data directory for persistent storage
RUN mkdir -p /app/data && chmod 777 /app/data

# Ensure the start script is executable
RUN chmod +x start.sh

# Volume for persistent storage
VOLUME ["/app/data"]

# Set environment variable to indicate we're in a Docker container
ENV IS_DOCKER=true

# Port for webhook server
EXPOSE 10000
# Port for health check
EXPOSE 8080

# Command to run the bot
CMD ["./start.sh"] 