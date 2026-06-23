from fastapi import FastAPI
from nomad.config import config

api_entry_point = config.get_plugin_entry_point(
    'nomad_semantic_web_service.apis:api_entry_point'
)

app = FastAPI(root_path=f'{config.services.api_base_path}/{api_entry_point.prefix}')


@app.get('/')
async def root():
    return {'message': 'Hello World'}
