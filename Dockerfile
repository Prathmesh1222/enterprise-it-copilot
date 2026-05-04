# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install system dependencies (needed for compiling some python packages)
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# We also install the newly added dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir flask flask-cors langgraph sentence-transformers rank_bm25 networkx

# Copy the current directory contents into the container
COPY . .

# Expose port 5000 for Flask backend
EXPOSE 5000

# Run the migration script if needed
# RUN python migrate_db.py

# Create an entrypoint script to run Flask.
CMD ["python", "backend.py"]
