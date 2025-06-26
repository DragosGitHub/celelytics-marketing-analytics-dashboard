# Use Python 3.11 base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy all backend files
COPY . .

# Expose dynamic port for Render (default is 5000, but Render sets PORT env)
EXPOSE 5000

# Set environment variables if needed
ENV PYTHONUNBUFFERED=1

# Start the app using the dynamic PORT environment variable
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
