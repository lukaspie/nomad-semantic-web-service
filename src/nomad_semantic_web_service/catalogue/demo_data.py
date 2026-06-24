from datetime import datetime, timezone
from typing import Any

# Shaped like a real ICAT+ /catalogue/public/datasets record (see
# https://icatplus.esrf.fr/swagger.json, schema `dataset`, and
# catalogue.icat.landing_page_for_dataset): `techniques` is a list of
# {..., "pid": str} objects, not a flat list of PIDs, and a dataset's public
# landing page comes from `investigation.doi`, not a top-level `location`
# (which is an internal storage path on real records).
FAKE_DATASETS: list[dict[str, Any]] = [
    {
        "id": 1001,
        "name": "ID21 XAS catalyst oxidation-state dataset",
        "startDate": datetime(2024, 3, 18, 9, 15, tzinfo=timezone.utc),
        "endDate": datetime(2024, 3, 18, 11, 45, tzinfo=timezone.utc),
        "location": "/data/demo/id21/xas-catalyst",
        "investigation": {"doi": "10.0000/DEMO-ID21-1001"},
        "instrumentName": "ID21",
        "sampleName": "ceria-supported platinum catalyst",
        "techniques": [
            {
                "id": 1,
                "datasetId": 1001,
                "pid": "https://w3id.org/PaN/ESRFET#XAS",
                "name": "XAS",
            },
        ],
    },
    {
        "id": 1002,
        "name": "ID21 energy-dispersive XAS reference scan",
        "startDate": datetime(2024, 3, 19, 14, 0, tzinfo=timezone.utc),
        "endDate": datetime(2024, 3, 19, 18, 30, tzinfo=timezone.utc),
        "location": "/data/demo/id21/ed-xas-reference",
        "investigation": {"doi": "10.0000/DEMO-ID21-1002"},
        "instrumentName": "ID21",
        "sampleName": "iron oxide calibration foil",
        "techniques": [
            {
                "id": 2,
                "datasetId": 1002,
                "pid": "https://w3id.org/PaN/ESRFET#ED-XAS",
                "name": "ED-XAS",
            },
            {
                "id": 3,
                "datasetId": 1002,
                "pid": "https://w3id.org/PaN/ESRFET#XAS",
                "name": "XAS",
            },
        ],
    },
    {
        "id": 1003,
        "name": "ID24 dispersive XAS battery electrode dataset",
        "startDate": datetime(2024, 5, 2, 8, 30, tzinfo=timezone.utc),
        "endDate": datetime(2024, 5, 2, 15, 10, tzinfo=timezone.utc),
        "location": "/data/demo/id24/dispersive-xas-electrode",
        "investigation": {"doi": "10.0000/DEMO-ID24-1003"},
        "instrumentName": "ID24",
        "sampleName": "lithium nickel manganese cobalt oxide electrode",
        "techniques": [
            {
                "id": 4,
                "datasetId": 1003,
                "pid": "https://w3id.org/PaN/ESRFET#ED-XAS",
                "name": "ED-XAS",
            },
        ],
    },
    {
        "id": 1004,
        "name": "High-resolution tomography of heritage material",
        "startDate": datetime(2024, 9, 12, 7, 45, tzinfo=timezone.utc),
        "endDate": datetime(2024, 9, 12, 12, 20, tzinfo=timezone.utc),
        "location": "/data/demo/id19/tomography-heritage",
        "investigation": {"doi": "10.0000/DEMO-ID19-1004"},
        "instrumentName": "ID19",
        "sampleName": "painted ceramic fragment",
        "techniques": [
            {
                "id": 5,
                "datasetId": 1004,
                "pid": "https://w3id.org/PaN/ESRFET#TOMO",
                "name": "TOMO",
            },
        ],
    },
]
