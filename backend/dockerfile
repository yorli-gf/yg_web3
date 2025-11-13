# Light based image for python 3.13
FROM python:3.13-slim

# Install system-level dependencies for packages like mysqlclient, cryptography, Pillow, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
    
# Set the working directory in the container
WORKDIR /app

# Copy the requirements
COPY requirements.txt .

# Install depencencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code of the app
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]