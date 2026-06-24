from __future__ import annotations

from datetime import date, datetime
from typing import Any

from nomad_semantic_web_service.catalogue.demo_data import FAKE_DATASETS
from nomad_semantic_web_service.catalogue.icat import fetch_icat_public_datasets

# Note: this is the w3id.org IRI used in dataset records, distinct from
# catalogue.ontology.ESRFET_PURL_PREFIX (the purl.org namespace used internally
# by ESRFET.owl). canonical_technique_pid() translates purl.org -> w3id.org so
# user-supplied PURL-form IRIs match the w3id-form IRIs stored on datasets.
ESRFET = "https://w3id.org/PaN/ESRFET#"
ESRFET_PURL = "http://purl.org/pan-science/ESRFET#"


def normalize_esrfet_term(term: str) -> str:
    """Normalizes a user-supplied ESRFET term to the w3id.org IRI form used by
    dataset records (e.g. "XAS" or "ESRFET:XAS" -> "https://w3id.org/PaN/ESRFET#XAS")."""
    cleaned = term.strip()
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned
    if cleaned.startswith("ESRFET:"):
        cleaned = cleaned.split(":", 1)[1]
    if cleaned.startswith("#"):
        cleaned = cleaned[1:]
    return ESRFET + cleaned


def canonical_technique_pid(technique_pid: str) -> str:
    if technique_pid.startswith(ESRFET_PURL):
        return ESRFET + technique_pid.removeprefix(ESRFET_PURL)
    return technique_pid


def parse_technique_pids(technique_pids: str | None) -> set[str]:
    if not technique_pids:
        return set()
    return {
        canonical_technique_pid(pid.strip())
        for pid in technique_pids.split(",")
        if pid.strip()
    }


def technique_pids_of(dataset: dict[str, Any]) -> list[str]:
    """Extracts technique PIDs from a dataset record's `techniques` list
    (the shape used by both FAKE_DATASETS and real ICAT+ records)."""
    return [
        technique["pid"]
        for technique in dataset.get("techniques", [])
        if technique.get("pid")
    ]


def search_local_datasets(
    start_date: date | datetime,
    end_date: date | datetime,
    technique_pids: str | None,
    instrument_name: str | None,
) -> list[dict[str, Any]]:
    requested_techniques = parse_technique_pids(technique_pids)
    requested_instrument = instrument_name.lower() if instrument_name else None

    return [
        dataset
        for dataset in FAKE_DATASETS
        if dataset["startDate"] >= start_date
        and dataset["endDate"] <= end_date
        and (
            not requested_techniques
            or requested_techniques.intersection(
                canonical_technique_pid(pid) for pid in technique_pids_of(dataset)
            )
        )
        and (
            requested_instrument is None
            or dataset["instrumentName"].lower() == requested_instrument
        )
    ]


def search_icat_datasets(
    start_date: date | datetime,
    end_date: date | datetime,
    technique_pids: str | None,
    instrument_name: str | None,
) -> Any:
    return fetch_icat_public_datasets(
        start_date=start_date,
        end_date=end_date,
        technique_pids=technique_pids,
        instrument_name=instrument_name,
    )
