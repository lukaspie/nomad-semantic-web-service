from nomad_semantic_web_service.catalogue.icat import landing_page_for_dataset


def test_landing_page_for_dataset_with_doi():
    dataset = {
        "id": 2008212345,
        "investigation": {"doi": "10.15151/ESRF-ES-750932592"},
    }
    assert (
        landing_page_for_dataset(dataset)
        == "https://doi.org/10.15151/ESRF-ES-750932592"
    )


def test_landing_page_for_dataset_without_investigation():
    # FAKE_DATASETS records have no "investigation" key at all.
    assert landing_page_for_dataset({"id": 1001, "name": "demo"}) is None


def test_landing_page_for_dataset_without_doi():
    dataset = {"id": 2008212345, "investigation": {"id": 750932592}}
    assert landing_page_for_dataset(dataset) is None
