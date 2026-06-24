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
| ELN schema | `schema_packages/schema_package.py`, `schema_packages/__init__.py` | No |

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
is an internal ESRF storage path on real records, not a public URL — and there
is no generic, unauthenticated download URL for the underlying files; actual
file streaming requires an authenticated ICAT+ session via `/ids/data/download`).
Keeping the demo data isomorphic to the real shape means `catalogue.search.technique_pids_of()`
and `catalogue.icat.landing_page_for_dataset()` work identically for both, with
no shape-detection branching needed anywhere in the plugin.

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
