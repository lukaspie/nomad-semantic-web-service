import os.path

from nomad.client import normalize_all, parse


def test_dataset_search_request_esrfet():
    test_file = os.path.join("tests", "data", "test.archive.yaml")
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    data = entry_archive.data
    assert data.resolved_technique_term == "https://w3id.org/PaN/ESRFET#XAS"
    assert data.mapping_warning is None
    # trigger_search resets to False once the search has run.
    assert data.trigger_search is False
    # Both 1001 and 1002 carry the XAS technique PID in FAKE_DATASETS.
    assert len(data.matched_datasets) == 2
    assert data.matched_datasets[0].name == "ID21 XAS catalyst oxidation-state dataset"


def test_dataset_search_request_panet():
    test_file = os.path.join("tests", "data", "test_panet.archive.yaml")
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    data = entry_archive.data
    # query_panet_to_esrfet() returns the target IRI in the ontology's own
    # purl.org namespace; canonical_technique_pid() converts it to the
    # w3id.org form internally when matching against dataset records.
    assert data.resolved_technique_term == "http://purl.org/pan-science/ESRFET#XAS"
    assert data.mapping_warning is None
    # Both 1001 and 1002 carry the XAS technique PID in FAKE_DATASETS.
    assert len(data.matched_datasets) == 2


def test_dataset_search_request_resolves_mapping_without_searching():
    """Without trigger_search, the mapping is resolved but no search runs."""
    test_file = os.path.join("tests", "data", "test_panet.archive.yaml")
    entry_archive = parse(test_file)[0]
    entry_archive.data.trigger_search = False

    normalize_all(entry_archive)

    data = entry_archive.data
    assert data.resolved_technique_term == "http://purl.org/pan-science/ESRFET#XAS"
    assert not data.matched_datasets


def test_dataset_search_request_uses_default_dates():
    """start_date/end_date are left unset, relying on the Quantity defaults.

    Regression test: an unset Quantity default is returned as the raw literal
    (a str here) rather than coerced through the Datetime type, which crashed
    search_local_datasets()'s `dataset['endDate'] <= end_date` comparison
    until normalize() started re-assigning start_date/end_date to themselves
    to force the coercion.
    """
    test_file = os.path.join("tests", "data", "test_default_dates.archive.yaml")
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    data = entry_archive.data
    assert data.start_date.isoformat() == "2024-01-01T00:00:00+00:00"
    assert data.end_date.isoformat() == "2024-12-31T23:59:59+00:00"
    assert len(data.matched_datasets) == 2
