# Use the official Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY aicleaner.py .
COPY run.sh .
RUN chmod a+x run.sh

# Copy the www directory for Lovelace cards
COPY www/ /app/www/

# Start the application
CMD [ "./run.sh" ]