FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir requests

COPY run.sh ./run.sh
COPY campaign.py ./campaign.py
COPY campaign.txt ./campaign.txt

RUN chmod +x run.sh

CMD ["./run.sh"]
