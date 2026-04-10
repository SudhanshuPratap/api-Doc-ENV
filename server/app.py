from openenv.core.env_server import create_fastapi_app
from .environment import APIDocEnv

app = create_fastapi_app(APIDocEnv)
