from workers import asgi

from services.api.main import api

Default = asgi.entrypoint(api)
