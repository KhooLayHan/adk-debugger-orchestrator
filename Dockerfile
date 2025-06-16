FROM python:3.9-slim

# Set working directory in the container
WORKDIR /app

# Copy requirements.txt and install dependencies using uv
COPY requirements.txt .
# uv is installed via pip for simplicity in Dockerfile
RUN pip install uv
# Install into system Python, not in virtual environment container
RUN uv pip install -r requirements.txt --system 

# Copy the rest of the application code
COPY . .

# Set the environment variables for the container
# Will be overridden by Cloud Run service environment
ENV GOOGLE_CLOUD_PROJECT="tenacious-veld-461901-f1" 
ENV GOOGLE_CLOUD_LOCATION="us-central1"     
ENV GOOGLE_GENAI_USE_VERTEXAI="TRUE"

# Command to run the application
# Ensure main.py uses asyncio.run and the agents are properly started 
ENTRYPOINT ["python", "main.py"]