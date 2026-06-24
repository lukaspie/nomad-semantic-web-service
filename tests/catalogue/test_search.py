from nomad_semantic_web_service.catalogue.search import technique_pids_of


def test_technique_pids_of():
    dataset = {
        'techniques': [
            {'id': 1, 'pid': 'PaNET:PaNET01012', 'name': 'x-ray probe'},
            {'id': 2, 'pid': None, 'name': 'no pid'},
        ]
    }
    assert technique_pids_of(dataset) == ['PaNET:PaNET01012']


def test_technique_pids_of_missing():
    assert technique_pids_of({}) == []
