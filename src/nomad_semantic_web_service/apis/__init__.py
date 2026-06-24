from nomad.config.models.plugins import APIEntryPoint


class SemanticWebServiceAPIEntryPoint(APIEntryPoint):
    def load(self):
        from nomad_semantic_web_service.apis.api import app

        return app


api_entry_point = SemanticWebServiceAPIEntryPoint(
    prefix='semantic-web-service',
    name='SemanticWebServiceAPI',
    description=(
        'ESRF-style public dataset catalogue endpoint with PANET/ESRFET '
        'semantic OpenAPI annotations.'
    ),
)
