from fastapi.testclient import TestClient


def test_importing_api():
    from nomad_semantic_web_service.apis import api_entry_point

    assert api_entry_point.prefix == "semantic-web-service"
    assert api_entry_point.name == "SemanticWebServiceAPI"


def test_health():
    from nomad_semantic_web_service.apis.api import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_catalogue_public_datasets():
    from nomad_semantic_web_service.apis.api import app

    client = TestClient(app)
    response = client.get(
        "/catalogue/public/datasets",
        params={
            "startDate": "2021-01-01T00:00:00Z",
            "endDate": "2022-12-31T23:59:59Z",
            "techniquePids": "https://w3id.org/PaN/ESRFET#XAS",
            "instrumentName": "ID21",
        },
    )
    assert response.status_code == 200
    datasets = response.json()
    # Both 1001 and 1002 carry the XAS technique PID in FAKE_DATASETS.
    assert len(datasets) == 2
    assert {d["name"] for d in datasets} == {
        "ID21 XAS catalyst oxidation-state dataset",
        "ID21 energy-dispersive XAS reference scan",
    }


def test_map_panet_to_esrfet():
    from nomad_semantic_web_service.apis.api import app

    client = TestClient(app)
    response = client.get(
        "/map", params={"term": "PaNET01196", "source": "PANET", "target": "ESRFET"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mappings"]
    assert body["targetTerm"] == body["mappings"][0]["targetTerm"]


def test_download_public_dataset(monkeypatch):
    import nomad_semantic_web_service.apis.api as api_module

    monkeypatch.setattr(
        api_module,
        "download_dataset_archive",
        lambda dataset_id, file_extensions=None: b"zip-bytes",
    )

    client = TestClient(api_module.app)
    response = client.get("/catalogue/public/datasets/874478618/download")
    assert response.status_code == 200
    assert response.content == b"zip-bytes"
    assert response.headers["content-type"] == "application/zip"
    assert 'filename="dataset-874478618.zip"' in response.headers["content-disposition"]


def test_download_public_dataset_no_matching_files(monkeypatch):
    import nomad_semantic_web_service.apis.api as api_module

    def raise_no_match(dataset_id, file_extensions=None):
        raise ValueError("No datafiles match the requested file extensions.")

    monkeypatch.setattr(api_module, "download_dataset_archive", raise_no_match)

    client = TestClient(api_module.app)
    response = client.get(
        "/catalogue/public/datasets/874478618/download",
        params={"fileExtensions": "nonexistent"},
    )
    assert response.status_code == 404
