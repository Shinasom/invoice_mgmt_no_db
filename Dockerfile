# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system-level dependencies required by your Python libraries
RUN apt-get update && apt-get install -y poppler-utils

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at the root of the app directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code into the container
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# Command to run your app
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]