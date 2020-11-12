FROM python:3.8-alpine
RUN apk add bash jq ttf-liberation zlib-dev jpeg-dev gcc musl-dev freetype-dev imagemagick
RUN pip install conducto
COPY . /life
RUN cd /life && python setup.py develop
