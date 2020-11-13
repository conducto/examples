# Flask + Docker
The demo service is built upon an excellent [image from tiangolo](https://hub.docker.com/r/tiangolo/uwsgi-nginx-flask/) that bundles Flask with uWSGI and Nginx. 

The Flask development server used by `flask run` is not suitable for production use. [Sebastián Ramírez](https://github.com/tiangolo) provides several pre-made Docker images for productionizing Python web applications, with Flask and FastAPI.

Special shout out to Sebastián for FastAPI. It's wonderful.