# Explanation

## Provenance

This plugin is built on top of [`oscarsSemanticWebService`](https://github.com/gkoum/oscarsSemanticWebService),
a FastAPI proof-of-concept by Giannis Koumoutsos for an ESRF-style catalogue
endpoint with semantic OpenAPI annotations. Its routes, models, and PANET/ESRFET
ontology mapping logic were ported into `catalogue/`, `apis/`, and exposed
additionally as the `DatasetSearchRequest` ELN schema described below.

## Architecture

This plugin has three layers, mirroring the repository's "schemas ≠ runtime logic"
principle:

| Layer | Module | Depends on FastAPI? |
|---|---|---|
| Domain logic | `catalogue/icat.py`, `catalogue/ontology.py`, `catalogue/search.py` | No |
| REST API | `apis/api.py`, `apis/__init__.py` | Yes |
| ELN schema | `schema_packages/schema.py`, `schema_packages/__init__.py` | No |

The domain layer has no FastAPI dependency, so both the mounted REST API and the
ELN schema's `normalize()` import and call its plain Python functions directly.
Earlier work on a related ontology service in `pynxtools` (commit `abad72f1`,
later reverted in `ab6deb48`) had a schema's `normalize()` call its own mounted
API over `http://localhost:8000` loopback — this plugin deliberately avoids that
pattern.

## `catalogue.demo_data.FAKE_DATASETS` mirrors the real ICAT+ response shape

`catalogue/demo_data.py` holds the local demo dataset records, kept deliberately
separate from `catalogue/search.py`'s actual search/filter logic. Its records are
shaped like real `/catalogue/public/datasets` responses from `icatplus.esrf.fr`
(confirmed against the live endpoint and its `swagger.json`, even though that
specific public route isn't itself documented there): `techniques` is a list of
`{..., "pid": str}` objects rather than a flat PID list, and a public landing
page comes from `investigation.doi` (resolved via
`catalogue.icat.landing_page_for_dataset()`), not a top-level `location` (which
is an internal ESRF storage path on real records, not itself a public URL).
Keeping the demo data isomorphic to the real shape means `catalogue.search.technique_pids_of()`
and `catalogue.icat.landing_page_for_dataset()` work identically for both, with
no shape-detection branching needed anywhere in the plugin.

`FAKE_DATASETS`' dates are 2021–2022, matching `DatasetSearchRequest.start_date`/
`end_date`'s defaults, so the demo data is found without changing anything
just by saving a new entry.

## Anonymous file download for public datasets

`GET /ids/data/download?datasetIds=<id>` works **without authentication** for
public datasets: its swagger security scheme is `[{bearerAuth: []}, {}]` — the
empty alternative means auth is optional — and ICAT+ auto-issues an anonymous
session, redirecting to `ids.esrf.fr/ids/getData?sessionId=...` with the real
file content (confirmed empirically by downloading a real public dataset's zip
archive with no credentials at all). `data.esrf.fr` ("Data Portal") is a nicer
UI over the same backend, but its download/reprocess actions are gated behind
login for convenience/attribution, not because anonymous IDS access is blocked.

`catalogue.icat.download_dataset_archive()` implements this: it always
downloads anonymously, optionally filtered to specific file extensions
(`file_extensions_filter` on `MatchedDataset` defaults to `h5`, since whole
datasets can be much larger than a typical text/metadata file). Format
filtering needs the dataset's individual files first (`list_datafiles()`, via
the anonymous session minted by `get_anonymous_session_id()`), since
`/ids/data/download` only accepts `datasetIds` (whole dataset) or `datafileIds`
(an explicit id list), not a format/extension parameter directly. This is
exposed both as a REST route
(`GET /catalogue/public/datasets/{id}/download?fileExtensions=...`, which
returns the zip as-is) and as a `trigger_download` action on `MatchedDataset`
in the ELN schema, which goes a step further: `catalogue.icat.extract_zip_members()`
unpacks the downloaded zip in memory, and each member is written into the
upload under `dataset-<id>/` via `archive.m_context.raw_file(name, 'wb')`
(after `archive.m_context.upload_files.raw_create_directory(...)` for any
intermediate directories — `raw_file()` does not auto-create them), then the
zip itself is discarded rather than kept alongside the extracted copy. This
makes individual files browsable/downloadable in the GUI and means other
parsers could in principle pick them up, neither of which a single opaque zip
blob would allow. Both download paths only work against real ICAT+ data
(`use_real_icat=True`); the local demo data has no real files behind it.

Real ICAT+ archives have been observed to contain zip entries with doubled
slashes (e.g. `"poi28997_35602//35602_args.json"`) and/or a leading slash.
`nomad.common.is_safe_relative_path()` rejects both outright (`'//' in path`,
or starting with `'/'`), which would otherwise crash the `raw_file()`/
`raw_create_directory()` calls above. `extract_zip_members()` normalizes every
member name (`normalize_zip_member_name()`, collapsing repeated slashes and
stripping any leading one) before it's used as a path.

## Two IRI namespaces for ESRFET

The plugin works with technique terms in two distinct namespaces that look similar
but are not interchangeable:

- `https://w3id.org/PaN/ESRFET#` — the published namespace used on dataset
  records (`Dataset.techniquePids`, `catalogue.demo_data.FAKE_DATASETS`).
- `http://purl.org/pan-science/ESRFET#` — the namespace used internally by
  `ESRFET.owl` for `owl:equivalentClass` axioms against PANET terms.

`catalogue.search.canonical_technique_pid()` converts the `purl.org` form to the
`w3id.org` form so a PANET→ESRFET mapping result can be matched against dataset
records. `catalogue.search.normalize_esrfet_term()` normalizes user-typed ESRFET
terms (e.g. `"XAS"`, `"ESRFET:XAS"`) directly to the `w3id.org` form.

## The search runs automatically, but `search_key` prevents redundant reruns

`DatasetSearchRequest.normalize()` runs the catalogue search on every save
once `technique_term`/dates are set — there's no separate "confirm and run"
action button. An earlier version gated this behind a `trigger_search` action
(mirroring the original CLI's confirmation prompt before searching), but in
practice this just meant an extra mandatory save before anything useful
appeared, for limited benefit; it was removed.

Auto-running on every save creates a real hazard, though: `_run_search()`
rebuilds `matched_datasets` from scratch. Saving for an unrelated reason — e.g.
setting `file_extensions_filter` and clicking **Download Files** on an
existing `MatchedDataset` item — would otherwise discard that item (and its
in-progress download state) before it ever got a chance to run, since the
parent's `normalize()` runs first and replaces the whole list. `search_key`
caches a fingerprint of the actual search inputs (date window, resolved term,
instrument, `use_real_icat`) and skips re-running the search when it hasn't
changed, so `matched_datasets` is only rebuilt when the search itself should
actually change.

## External (ICAT+) failures are logged as warnings, not errors

`_run_search()` and `MatchedDataset.normalize()` both catch failures from
their respective ICAT+ calls and log them — deliberately via `logger.warning()`,
not `logger.error()`. `EntryProc.get_logger()`
(`nomad/processing/data.py`) appends every `logger.error()` call to
`entry_metadata.processing_errors`, which marks the entry with a processing
error badge in the GUI. An ICAT+ outage (e.g. `/catalogue/public/datasets`
returning a bare 404 — it isn't in `swagger.json`, so it's evidently
undocumented/unofficial and was observed to disappear without warning) is an
external dependency being unavailable, not a defect in the entry's own data;
`use_real_icat`'s results being temporarily empty shouldn't read as "this
entry is broken."

## `technique_pids` is a string, not a `shape=['*']` array

`MatchedDataset.technique_pids` was originally `Quantity(type=str,
shape=['*'])` (an array of IRIs). In practice, saving an entry from the GUI
after a search occasionally persisted this field as `{}` instead of a list,
which crashed reprocessing entirely with `ValueError: Cannot identify type for
{}.` (raised by the array-handling branch of `nomad.metainfo.data_type
.Primitive.normalize()`, reached because the quantity has a shape — i.e. is
not "scalar" — and `{}` is neither `list`, `tuple`, nor `ndarray`). The
`shape=['*']` was unnecessary for a read-only field with no array-specific
GUI editor; it's now a single comma-joined string, which sidesteps the array
code path entirely.

## Why `ServerContext` only guards the ICAT+ call

`DatasetSearchRequest.normalize()` only skips the real ESRF ICAT+ HTTP call when
`archive.m_context` is not a `ServerContext` (i.e. running offline, such as in
tests). The local fake-dataset search and the PANET/ESRFET ontology mapping run
unconditionally, since both are local, fast, and deterministic — only the
outbound network call to `icatplus.esrf.fr` needs guarding.

## A note on the `rdflib` SPARQL dependency

PANET↔ESRFET mapping (`catalogue/ontology.py`) queries `ESRFET.owl` with SPARQL
via `rdflib`. `nomad-lab`'s own `infrastructure` extra pins `rdflib==5` across
this uv workspace; that version's bundled SPARQL parser is incompatible with
`pyparsing>=3` (any query fails with
`AttributeError: 'NoneType' object has no attribute 'name'`). This plugin pins
`pyparsing<3` in its own dependencies to restore working SPARQL support
workspace-wide, since nothing else in the workspace constrains `pyparsing` to a
specific version.
