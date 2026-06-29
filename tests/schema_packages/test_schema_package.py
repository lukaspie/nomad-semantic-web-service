import os.path

import structlog
from nomad.client import normalize_all, parse


def test_dataset_search_request_esrfet():
    test_file = os.path.join("tests", "data", "test.archive.yaml")
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    data = entry_archive.data
    assert data.resolved_technique_term == "https://w3id.org/PaN/ESRFET#XAS"
    assert data.mapping_warning is None
    # Both 1001 and 1002 carry the XAS technique PID in FAKE_DATASETS.
    assert len(data.matched_datasets) == 2
    assert data.matched_datasets[0].name == "ID21 XAS catalyst oxidation-state dataset"
    assert data.matched_datasets[0].technique_pids == "https://w3id.org/PaN/ESRFET#XAS"


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
    assert data.start_date.isoformat() == "2021-01-01T00:00:00+00:00"
    assert data.end_date.isoformat() == "2022-12-31T23:59:59+00:00"
    assert len(data.matched_datasets) == 2


def test_repeated_normalize_does_not_discard_matched_dataset_state():
    """Regression test: removing the old trigger_search confirmation step meant
    the search runs automatically on every save. Without the search_key cache,
    a second normalize() call with unchanged inputs would rebuild
    matched_datasets from scratch, discarding e.g. an in-progress
    trigger_download/file_extensions_filter set on an existing item before
    that item ever got a chance to act on it."""
    test_file = os.path.join("tests", "data", "test.archive.yaml")
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    data = entry_archive.data
    first_key = data.search_key
    data.matched_datasets[0].file_extensions_filter = "json"

    normalize_all(entry_archive)

    assert data.search_key == first_key
    assert data.matched_datasets[0].file_extensions_filter == "json"


def test_matched_dataset_download_skipped_offline():
    """trigger_download on a MatchedDataset is a no-op outside ServerContext,
    matching the use_real_icat guard on the parent DatasetSearchRequest."""
    test_file = os.path.join("tests", "data", "test.archive.yaml")
    entry_archive = parse(test_file)[0]
    normalize_all(entry_archive)

    matched_dataset = entry_archive.data.matched_datasets[0]
    matched_dataset.trigger_download = True
    matched_dataset.normalize(entry_archive, structlog.get_logger())

    assert matched_dataset.trigger_download is False
    assert matched_dataset.downloaded_folder is None
    assert matched_dataset.downloaded_files is None
