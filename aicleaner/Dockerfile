# Use the official Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set the working directory
WORKDIR /app

# Copy the application files
COPY aicleaner.py .
COPY run.sh .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make run.sh executable
RUN chmod a+x run.sh

# Start the application
CMD [ "./run.sh" ]