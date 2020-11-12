# Use awesome image with uWSGI and Nginx for Flask web applications.
# Documentation: https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/
FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine
RUN pip install flask
COPY ./app /app
