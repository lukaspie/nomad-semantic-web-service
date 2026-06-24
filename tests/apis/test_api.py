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
            "startDate": "2024-01-01T00:00:00Z",
            "endDate": "2024-12-31T23:59:59Z",
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
