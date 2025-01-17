FROM python:3.12.3-slim-bullseye

# Set an environment variable to unbuffer Python output, aiding in logging and debugging
ENV PYTHONBUFFERED=1

# Define an environment variable for the web service's port, commonly used in cloud services
ENV PORT 8080

# Set the working directory within the container to /app for any subsequent commands
WORKDIR /app

# Copy the entire current directory contents into the container at /app
COPY . /app/

# Upgrade pip to ensure we have the latest version for installing dependencies
RUN pip install --upgrade pip

# Install dependencies from the requirements.txt file to ensure our Python environment is ready
RUN pip install -r requirements.txt

RUN python manage.py migrate

RUN python manage.py test

# Set the command to run our web service using Gunicorn, binding it to 0.0.0.0 and the PORT environment variable
#CMD gunicorn --bind 0.0.0.0:"${PORT}" --certfile=/etc/letsencrypt/archive/trashtransit.click/fullchain1.pem --keyfile=/etc/letsencrypt/archive/trashtransit.click/privkey1.pem worsttransit.wsgi:application
CMD gunicorn --bind 0.0.0.0:"${PORT}" kitchentable.wsgi:application

# Inform Docker that the container listens on the specified network port at runtime
EXPOSE ${PORT}