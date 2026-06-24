# Tutorial

This tutorial walks through searching for ESRF datasets via the ELN schema,
including a PANET→ESRFET term mapping.

## 1. Create a search entry

In your NOMAD upload, create a new entry of type **Dataset search request**
(`DatasetSearchRequest`).

## 2. Search directly with an ESRFET term

Fill in:

- `synchrotron`: `ESRF`
- `vocabulary`: `ESRFET`
- `technique_term`: `XAS`
- `start_date` / `end_date`: leave the defaults (`2024-01-01T00:00:00Z` /
  `2024-12-31T23:59:59Z`), or set your own.
- `instrument_name`: `ID21`

Save the entry. `resolved_technique_term` is resolved automatically on every
save and shows `https://w3id.org/PaN/ESRFET#XAS` — review it now, before
running the search. When it looks right, click the **Run Search** button
(`trigger_search`) and save again. `matched_datasets` then lists the matching
demo records (`ID21 XAS catalyst oxidation-state dataset` and
`ID21 energy-dispersive XAS reference scan`, both tagged with the XAS
technique). This two-step "resolve, then explicitly run" flow mirrors the
confirmation prompt in the original CLI agent, which showed the mapped term
and asked before searching.

## 3. Search with a PANET term instead

Create a second entry, this time with:

- `vocabulary`: `PANET`
- `technique_term`: `PaNET01196`

Save once: `normalize()` looks up the PANET term in the local ESRFET ontology,
finds its `owl:equivalentClass` mapping, and stores the result in
`resolved_technique_term` — without searching yet. If no mapping is found,
`mapping_warning` is set instead. Once you've checked the resolved term, click
**Run Search** and save again to populate `matched_datasets`.

## 4. Query the REST API directly

The same data is reachable without the ELN, for machine clients:

```bash
curl 'http://localhost:8000/nomad-oasis/semantic-web-service/map?term=PaNET01196'
```

See [How to use this plugin](../how_to/use_this_plugin.md) for more routes.
