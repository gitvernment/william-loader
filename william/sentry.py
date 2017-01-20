import os

from raven import Client

sentry_client = Client(os.getenv('SENTRY_URL'))