FROM python:3.13-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --root-user-action ignore -r requirements.txt

# Export openphone_exports as a volume
VOLUME openphone_exports

# Run the application
cmd python mondaywrite.py