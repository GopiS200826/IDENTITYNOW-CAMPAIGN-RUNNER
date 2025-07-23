FROM python:3.10-slim

WORKDIR /app

# Install required Python packages
RUN pip install --no-cache-dir requests

# Copy your scripts
COPY run.sh ./run.sh
COPY campaign.py ./campaign.py
COPY campaign.txt ./campaign.txt

# Make sure your script is executable
RUN chmod +x run.sh

# Default command
CMD ["./run.sh"]
