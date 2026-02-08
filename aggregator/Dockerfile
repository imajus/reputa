# Use official Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the source code into the container
COPY . /app

# Install dependencies
# Assuming you have a requirements.txt; if not, create one with: requests, numpy, scipy, pandas, etc.
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
