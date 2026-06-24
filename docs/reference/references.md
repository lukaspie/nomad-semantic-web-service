# References

## REST API routes

Mounted under `{api_base_path}/semantic-web-service`.

| Route | Method | Description |
|---|---|---|
| `/catalogue/public/datasets` | GET | Search the local demo dataset records by date range, technique PID, and instrument. |
| `/icat/catalogue/public/datasets` | GET | Proxy the same query to the real ESRF ICAT+ `/catalogue/public/datasets` endpoint. Response shape is unmapped/raw JSON from ICAT+. |
| `/map` | GET | Map a PANET term to its equivalent ESRFET term(s) via the local ontology. |
| `/health` | GET | Health check. |

## `DatasetSearchRequest` ELN schema fields

| Field | Type | Editable | Description |
|---|---|---|---|
| `synchrotron` | enum (`ESRF`, `Diamond Light Source`, `MAX IV`) | Yes | Only `ESRF` is wired to a live endpoint. |
| `vocabulary` | enum (`ESRFET`, `PANET`) | Yes | Vocabulary used for `technique_term`. |
| `technique_term` | string | Yes | Term, IRI, or compact curie in the selected vocabulary. |
| `start_date` / `end_date` | datetime | Yes | Search window. Default `2024-01-01T00:00:00Z`/`2024-12-31T23:59:59Z`. |
| `instrument_name` | string | Yes | Optional beamline/instrument filter. |
| `use_real_icat` | bool | Yes | Search the real ICAT+ endpoint instead of local demo data. |
| `resolved_technique_term` | string | No | The ESRFET IRI actually used for the search, resolved automatically on every save. |
| `mapping_warning` | string | No | Set if a PANET→ESRFET mapping could not be resolved. |
| `trigger_search` (action button "Run Search") | bool | Yes (action) | Runs the catalogue search using `resolved_technique_term`. Kept as an explicit step — separate from automatic mapping resolution — so a PANET mapping can be reviewed before it's used to search. Resets to `False` once the search runs. |
| `matched_datasets` | repeated section | No | Matching dataset records (`dataset_id`, `name`, `start_date`, `end_date`, `instrument_name`, `technique_pids`, `sample_name`, `landing_page`). `landing_page` is a DOI-based link (`https://doi.org/<doi>`), not a direct file download — ICAT+ has no generic, unauthenticated download URL for the underlying files. |

## Configuration

Both entry points are registered under `[project.entry-points.'nomad.plugin']`
in `pyproject.toml`:

- `nomad_semantic_web_service.apis:api_entry_point`
- `nomad_semantic_web_service.schema_packages:schema_package_entry_point`

They must also be listed in the consuming NOMAD instance's `nomad.yaml` under
`plugins.entry_points.include` if that list is a non-empty explicit allowlist.
