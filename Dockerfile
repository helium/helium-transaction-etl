FROM python:3.8-slim-buster

WORKDIR /usr/src/app

COPY . .

# libpq-dev and gcc are needed for pycopg2 dependency
RUN apt-get update \
    && apt-get -y install libpq-dev gcc

RUN pip3 install -r requirements.txt

RUN python3 etl.py --migrate

CMD ["python3", "etl.py", "--start"]
