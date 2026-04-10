from openenv.core.env_server import create_fastapi_app
from server.environment import APIDocEnv

app = create_fastapi_app(APIDocEnv)
