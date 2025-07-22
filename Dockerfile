FROM python:3.10-slim

WORKDIR /app

COPY campaign.py .
COPY campaign.txt .
COPY run.sh .

RUN chmod +x run.sh

ENTRYPOINT ["./run.sh"]
