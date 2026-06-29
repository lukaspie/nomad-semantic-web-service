import zipfile
from io import BytesIO

import httpx
import pytest

from nomad_semantic_web_service.catalogue.icat import (
    download_dataset_archive,
    extract_zip_members,
    get_anonymous_session_id,
    landing_page_for_dataset,
    list_datafiles,
    matches_file_extensions,
)


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


def test_matches_file_extensions():
    assert matches_file_extensions({"name": "/scan/35602_average.asc"}, {"asc"})
    assert not matches_file_extensions({"name": "/scan/35602.h5"}, {"asc"})
    assert not matches_file_extensions({}, {"asc"})


def test_get_anonymous_session_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/ids/data/download"
        assert request.url.params["datasetIds"] == "874478618"
        return httpx.Response(
            302,
            headers={
                "location": (
                    "https://ids.esrf.fr/ids/getData"
                    "?sessionId=425addb1-2281-4c21-851d-51775a8b0046"
                    "&datasetIds=874478618"
                )
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    session_id = get_anonymous_session_id(874478618, client=client)
    assert session_id == "425addb1-2281-4c21-851d-51775a8b0046"


def test_get_anonymous_session_id_no_location():
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(401))
    )
    with pytest.raises(ValueError, match="anonymous ICAT\\+ session"):
        get_anonymous_session_id(874478618, client=client)


def test_list_datafiles():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            "/catalogue/425addb1-2281-4c21-851d-51775a8b0046/dataset/id/874478618/datafile"
        )
        return httpx.Response(
            200,
            json=[
                {"Datafile": {"id": 1, "name": "/35602_args.json", "fileSize": 1648}},
                {"Datafile": {"id": 2, "name": "/35602.h5", "fileSize": 2587376}},
            ],
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    datafiles = list_datafiles(
        874478618, "425addb1-2281-4c21-851d-51775a8b0046", client=client
    )
    assert [df["name"] for df in datafiles] == ["/35602_args.json", "/35602.h5"]


def test_download_dataset_archive_whole_dataset():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/ids/data/download"
        assert request.url.params["datasetIds"] == "874478618"
        assert "datafileIds" not in request.url.params
        return httpx.Response(200, content=b"PK\x03\x04fake-zip-bytes")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    content = download_dataset_archive(874478618, client=client)
    assert content == b"PK\x03\x04fake-zip-bytes"


def test_download_dataset_archive_with_extension_filter():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if (
            request.url.path == "/ids/data/download"
            and "datafileIds" not in request.url.params
        ):
            # the call inside get_anonymous_session_id()
            return httpx.Response(
                302,
                headers={
                    "location": (
                        "https://ids.esrf.fr/ids/getData?sessionId=session-1&datasetIds=874478618"
                    )
                },
            )
        if request.url.path.endswith("/datafile"):
            return httpx.Response(
                200,
                json=[
                    {"Datafile": {"id": 1, "name": "/35602_args.json"}},
                    {"Datafile": {"id": 2, "name": "/35602.h5"}},
                ],
            )
        if (
            request.url.path == "/ids/data/download"
            and "datafileIds" in request.url.params
        ):
            assert request.url.params["datafileIds"] == "1"
            return httpx.Response(200, content=b"filtered-zip-bytes")
        raise AssertionError(f"unexpected request: {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    content = download_dataset_archive(
        874478618, file_extensions=["json"], client=client
    )
    assert content == b"filtered-zip-bytes"


def test_download_dataset_archive_no_matching_extension():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/datafile"):
            return httpx.Response(
                200, json=[{"Datafile": {"id": 1, "name": "/35602.h5"}}]
            )
        return httpx.Response(
            302,
            headers={
                "location": (
                    "https://ids.esrf.fr/ids/getData?sessionId=session-1&datasetIds=874478618"
                )
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError, match="No datafiles"):
        download_dataset_archive(874478618, file_extensions=["json"], client=client)


def _make_zip(files: dict[str, bytes], dirs: tuple[str, ...] = ()) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for dir_name in dirs:
            zf.writestr(zipfile.ZipInfo(f"{dir_name}/"), "")
        for name, data in files.items():
            zf.writestr(name, data)
    return buffer.getvalue()


def test_extract_zip_members_flat():
    content = _make_zip({"args.json": b'{"a": 1}', "average.asc": b"1 2 3"})
    members = dict(extract_zip_members(content))
    assert members == {"args.json": b'{"a": 1}', "average.asc": b"1 2 3"}


def test_extract_zip_members_skips_directory_entries():
    content = _make_zip({"gallery/snapshot.png": b"\x89PNG"}, dirs=("gallery",))
    members = dict(extract_zip_members(content))
    assert members == {"gallery/snapshot.png": b"\x89PNG"}
    assert "gallery/" not in members


def test_extract_zip_members_collapses_doubled_slashes():
    # Regression test: real ICAT+ archives have been observed to contain
    # entries like "poi28997_35602//35602_args.json" (doubled slash), which
    # nomad.common.is_safe_relative_path() rejects outright ('//' in path).
    content = _make_zip({"poi28997_35602//35602_args.json": b"{}"})
    members = dict(extract_zip_members(content))
    assert members == {"poi28997_35602/35602_args.json": b"{}"}


def test_extract_zip_members_strips_leading_slash():
    content = _make_zip({"/35602_args.json": b"{}"})
    members = dict(extract_zip_members(content))
    assert members == {"35602_args.json": b"{}"}
