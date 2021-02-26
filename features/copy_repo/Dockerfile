FROM python:3.8-alpine

COPY . /usr/local/src/myapp
WORKDIR /usr/local/src/myapp

RUN apk update && apk add tree figlet
RUN pip install -e .

CMD myfiglet
