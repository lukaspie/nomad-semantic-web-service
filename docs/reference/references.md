# References

## REST API routes

Mounted under `{api_base_path}/semantic-web-service`.

| Route | Method | Description |
|---|---|---|
| `/catalogue/public/datasets` | GET | Search the local demo dataset records by date range, technique PID, and instrument. |
| `/icat/catalogue/public/datasets` | GET | Proxy the same query to the real ESRF ICAT+ `/catalogue/public/datasets` endpoint. Response shape is unmapped/raw JSON from ICAT+. |
| `/catalogue/public/datasets/{dataset_id}/download` | GET | Downloads a real ICAT+ dataset as a zip archive, anonymously. Optional `fileExtensions` query param (comma-separated, e.g. `h5,edf`) restricts the archive to matching files. 404 if a filter matches nothing. |
| `/map` | GET | Map a PANET term to its equivalent ESRFET term(s) via the local ontology. |
| `/health` | GET | Health check. |

## `DatasetSearchRequest` ELN schema fields

| Field | Type | Editable | Description |
|---|---|---|---|
| `synchrotron` | enum (`ESRF`, `Diamond Light Source`, `MAX IV`) | Yes | Only `ESRF` is wired to a live endpoint. |
| `vocabulary` | enum (`ESRFET`, `PANET`) | Yes | Vocabulary used for `technique_term`. |
| `technique_term` | string | Yes | Term, IRI, or compact curie in the selected vocabulary. |
| `start_date` / `end_date` | datetime | Yes | Search window. Default `2021-01-01T00:00:00Z`/`2022-12-31T23:59:59Z`. |
| `instrument_name` | string | Yes | Optional beamline/instrument filter. |
| `use_real_icat` | bool | Yes | Search the real ICAT+ endpoint instead of local demo data. |
| `resolved_technique_term` | string | No | The ESRFET IRI actually used for the search, resolved automatically on every save. |
| `mapping_warning` | string | No | Set if a PANET→ESRFET mapping could not be resolved. |
| `search_key` | string | No | Internal cache key of the last completed search (date window, resolved term, instrument, `use_real_icat`). Search only re-runs when this changes, so that saving for an unrelated reason (e.g. setting `file_extensions_filter` on a `matched_datasets` item) doesn't rebuild `matched_datasets` and discard that item's state. |
| `matched_datasets` | repeated section | No | Matching dataset records, populated automatically once `technique_term`/dates are set — see `MatchedDataset` fields below. |

## `MatchedDataset` fields (items of `matched_datasets`)

| Field | Type | Editable | Description |
|---|---|---|---|
| `dataset_id`, `name`, `start_date`, `end_date`, `instrument_name`, `sample_name` | various | No | Mirror the underlying dataset record. |
| `technique_pids` | string | No | Comma-separated ESRFET technique IRIs. |
| `landing_page` | string | No | DOI-based link (`https://doi.org/<doi>`), if the dataset record has one. |
| `file_extensions_filter` | string | Yes | Comma-separated file extensions, e.g. `h5,edf`. Defaults to `h5`; clear it to download the whole dataset (can be much larger). |
| `trigger_download` (action button "Download Files") | bool | Yes (action) | Anonymously downloads this dataset (filtered by `file_extensions_filter`, if set) from ICAT+, extracts it into the upload under `downloaded_folder`, and discards the zip. Only works against real ICAT+ data (`use_real_icat=True`); a no-op for local demo data, which has no real files behind it. Resets to `False` once the download runs. |
| `downloaded_folder` | string | No | Path (within the upload) where the downloaded dataset files were extracted, once `trigger_download` has run. |
| `downloaded_files` | string | No | Comma-separated names of the extracted files, relative to `downloaded_folder`. |

## Configuration

Both entry points are registered under `[project.entry-points.'nomad.plugin']`
in `pyproject.toml`:

- `nomad_semantic_web_service.apis:api_entry_point`
- `nomad_semantic_web_service.schema_packages:schema_package_entry_point`

They must also be listed in the consuming NOMAD instance's `nomad.yaml` under
`plugins.entry_points.include` if that list is a non-empty explicit allowlist.
