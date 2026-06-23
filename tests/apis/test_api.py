def test_importing_api():
    from nomad_semantic_web_service.apis import api_entry_point

    assert api_entry_point.prefix == 'newapi'
    assert api_entry_point.name == 'NewAPI'
