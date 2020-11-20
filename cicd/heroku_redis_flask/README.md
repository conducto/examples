### Heroku + Redis + Flask CI/CD Pipeline

This is a CI/CD pipeline that uses Heroku to deploy and test a Flask app
that talks to Redis.

You must have [Heroku](https://signup.heroku.com/) and
[RedisLabs](https://redislabs.com/#signup-modal) accounts (free tier for
both) and specify the following as secrets in the Conducto app, or in the
environment:
* HEROKU_API_KEY
* REDIS_HOST
* REDIS_PORT
* REDIS_PASSWORD

The app uses [Redis](https://redis.io) and
[Flask](https://flask.palletsprojects.com).
- Flask responds to http requests and increments a counter.
- Redis stores the counter.
