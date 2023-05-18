# Use the official Python 3.9 base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Update pip
RUN pip install --no-cache-dir --upgrade pip

# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project code to the container
COPY ./bard_app_api/ .

# Set the environment variables if needed
ENV DJANGO_SETTINGS_MODULE=lol_stats_api.settings

# Expose the port on which Gunicorn will run
EXPOSE 8000

# Start Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lol_stats_api.wsgi"]