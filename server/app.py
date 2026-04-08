import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv_core.env_server.http_server import create_fastapi_app
from .environment import DocEnvironment
from models import DocAction, DocObservation

env = DocEnvironment()
app = create_fastapi_app(env, DocAction, DocObservation)