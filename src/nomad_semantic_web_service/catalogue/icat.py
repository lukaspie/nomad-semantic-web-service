from __future__ import annotations

import re
import zipfile
from datetime import date, datetime, timezone
from io import BytesIO
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

ICAT_BASE_URL = "https://icatplus.esrf.fr"
ICAT_PUBLIC_DATASETS_PATH = "/catalogue/public/datasets"
ICAT_PUBLIC_DATASETS_URL = ICAT_BASE_URL + ICAT_PUBLIC_DATASETS_PATH
IDS_DOWNLOAD_URL = ICAT_BASE_URL + "/ids/data/download"


def serialize_date_for_icat_query(value: date | datetime) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    return value.isoformat()


def serialize_datetime_for_query(value: datetime) -> str:
    serialized = value.isoformat()
    if value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value):
        return serialized.replace("+00:00", "Z")
    return serialized


def build_icat_public_dataset_params(
    start_date: date | datetime,
    end_date: date | datetime,
    technique_pids: str | None,
    instrument_name: str | None,
) -> dict[str, str]:
    params = {
        "startDate": serialize_date_for_icat_query(start_date),
        "endDate": serialize_date_for_icat_query(end_date),
    }
    if technique_pids:
        params["techniquePids"] = technique_pids
    if instrument_name:
        params["instrumentName"] = instrument_name
    return params


def landing_page_for_dataset(dataset: dict[str, Any]) -> str | None:
    """Resolves a public landing-page URL for a real ICAT+ dataset record.

    `dataset['location']` is an internal ESRF storage path, not a public URL.
    `dataset['investigation']['doi']` (e.g. "10.15151/ESRF-ES-750932592") is the
    durable, public identifier ICAT+ itself uses for datasets (see the
    `/doi/{prefix}/{suffix}/datasets` route in https://icatplus.esrf.fr/swagger.json),
    so it's resolved through the standard DOI resolver instead.
    """
    doi = dataset.get("investigation", {}).get("doi")
    return f"https://doi.org/{doi}" if doi else None


def fetch_icat_public_datasets(
    start_date: date | datetime,
    end_date: date | datetime,
    technique_pids: str | None = None,
    instrument_name: str | None = None,
    client: httpx.Client | None = None,
) -> Any:
    close_client = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.get(
            ICAT_PUBLIC_DATASETS_URL,
            params=build_icat_public_dataset_params(
                start_date=start_date,
                end_date=end_date,
                technique_pids=technique_pids,
                instrument_name=instrument_name,
            ),
            headers={"accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    finally:
        if close_client:
            client.close()


def get_anonymous_session_id(dataset_id: int, client: httpx.Client) -> str:
    """Obtains an anonymous ICAT+ session id for a public dataset.

    ICAT+ has no dedicated "create anonymous session" endpoint (`POST /session`
    requires real credentials). `GET /ids/data/download` accepts unauthenticated
    requests for public datasets and redirects to `ids.esrf.fr` with a freshly
    minted, anonymous `sessionId` query param (confirmed empirically: the
    route's swagger security scheme is `[{bearerAuth: []}, {}]`, i.e. auth is
    optional) - this extracts that session id so it can also be used to list
    a dataset's individual files (`/catalogue/{sessionId}/dataset/id/.../datafile`)
    for extension-based filtering.
    """
    response = client.get(
        IDS_DOWNLOAD_URL,
        params={"datasetIds": dataset_id, "inline": "false"},
        follow_redirects=False,
    )
    location = response.headers.get("location", "")
    session_ids = parse_qs(urlparse(location).query).get("sessionId")
    if not session_ids:
        raise ValueError(
            f"Could not obtain an anonymous ICAT+ session (status {response.status_code})."
        )
    return session_ids[0]


def list_datafiles(
    dataset_id: int, session_id: str, client: httpx.Client
) -> list[dict[str, Any]]:
    """Lists the individual files of a dataset, e.g. to filter by extension
    before downloading. Each entry has `id`, `name` (includes the extension),
    `fileSize`, and `location` (an internal storage path, not a public URL)."""
    response = client.get(
        f"{ICAT_BASE_URL}/catalogue/{session_id}/dataset/id/{dataset_id}/datafile"
    )
    response.raise_for_status()
    return [item["Datafile"] for item in response.json() if "Datafile" in item]


def matches_file_extensions(
    datafile: dict[str, Any], file_extensions: set[str]
) -> bool:
    name = datafile.get("name") or ""
    return any(name.lower().endswith(f".{ext}") for ext in file_extensions)


def download_dataset_archive(
    dataset_id: int,
    file_extensions: list[str] | None = None,
    client: httpx.Client | None = None,
) -> bytes:
    """Downloads a public ICAT+ dataset as a zip archive, anonymously.

    If `file_extensions` is given (e.g. `["h5", "edf"]`), only datafiles whose
    name ends with one of them (case-insensitive) are included; otherwise the
    whole dataset is downloaded. Raises `ValueError` if a filter matches no
    files.
    """
    close_client = client is None
    client = client or httpx.Client(timeout=120)
    try:
        if file_extensions:
            extensions = {ext.lower().lstrip(".") for ext in file_extensions}
            session_id = get_anonymous_session_id(dataset_id, client=client)
            datafiles = list_datafiles(dataset_id, session_id, client=client)
            datafile_ids = [
                datafile["id"]
                for datafile in datafiles
                if matches_file_extensions(datafile, extensions)
            ]
            if not datafile_ids:
                raise ValueError(
                    f"No datafiles in dataset {dataset_id} match extensions "
                    f"{sorted(extensions)}."
                )
            params = {
                "datafileIds": ",".join(str(i) for i in datafile_ids),
                "inline": "false",
            }
        else:
            params = {
                "datasetIds": str(dataset_id),
                "inline": "false",
            }

        response = client.get(IDS_DOWNLOAD_URL, params=params, follow_redirects=True)
        response.raise_for_status()
        return response.content
    finally:
        if close_client:
            client.close()


def normalize_zip_member_name(name: str) -> str:
    """Normalizes a zip member name into a safe relative path.

    Real ICAT+ archives have been observed to contain entries with doubled
    slashes (e.g. "poi28997_35602//35602_args.json") and leading slashes,
    either of which `nomad.common.is_safe_relative_path()` rejects outright
    (it requires no leading "/" and no "//"), which would otherwise crash
    `archive.m_context.raw_file()`/`raw_create_directory()` calls.
    """
    collapsed = re.sub(r"/+", "/", name)
    return collapsed.lstrip("/")


def extract_zip_members(content: bytes) -> list[tuple[str, bytes]]:
    """Extracts a zip archive's regular files (skipping directory entries) in
    place, in memory. Returns `(member_name, data)` pairs, in archive order,
    with member names normalized via `normalize_zip_member_name()`.

    Separated from any actual upload/filesystem writing so it can be tested
    without a NOMAD upload context.
    """
    members = []
    with zipfile.ZipFile(BytesIO(content)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            with archive.open(info) as member_file:
                members.append(
                    (normalize_zip_member_name(info.filename), member_file.read())
                )
    return members
