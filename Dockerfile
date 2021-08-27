# Dockerfile
FROM python:3.8-slim-buster
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Setup requirements
COPY . . 
RUN apt-get update && \
    apt-get install -y curl && \
    pip install --upgrade pip && \
    pip install -r requirements.txt 

# Run Flask App
EXPOSE 5000
CMD ["python", "app.py"]
#CMD ["bash"]

