# Use the official Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set the working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Make run.sh executable
RUN chmod a+x run.sh

# Expose the Flask port
EXPOSE 8099

# Start the application
CMD [ "./run.sh" ]