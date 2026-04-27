FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/main.py /app/main.py
COPY run.sh /run.sh

RUN chmod +x /run.sh

CMD ["/run.sh"]
