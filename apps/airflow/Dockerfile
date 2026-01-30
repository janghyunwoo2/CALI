# Base Image: Apache Airflow 2.9.3
FROM apache/airflow:2.9.3

LABEL maintainer="CALI Project Team"

# Copy requirements file
COPY requirements.txt /requirements.txt

# Install additional dependencies
# The base image already has airflow installed in a virtualenv
# We just add our extra packages to it
RUN pip install --no-cache-dir -r /requirements.txt
