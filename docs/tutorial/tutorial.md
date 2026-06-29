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
- `start_date` / `end_date`: leave the defaults (`2021-01-01T00:00:00Z` /
  `2022-12-31T23:59:59Z`), or set your own.
- `instrument_name`: `ID21`

Save the entry. `resolved_technique_term` is resolved (shows
`https://w3id.org/PaN/ESRFET#XAS`) and the search runs in the same save:
`matched_datasets` immediately lists the matching demo records
(`ID21 XAS catalyst oxidation-state dataset` and
`ID21 energy-dispersive XAS reference scan`, both tagged with the XAS
technique).

## 3. Search with a PANET term instead

Create a second entry, this time with:

- `vocabulary`: `PANET`
- `technique_term`: `PaNET01196`

Save: `normalize()` looks up the PANET term in the local ESRFET ontology,
finds its `owl:equivalentClass` mapping, stores the result in
`resolved_technique_term`, and searches using it — all in this one save. If no
mapping is found, `mapping_warning` is set instead and `matched_datasets`
stays empty.

## 4. Download files from a real dataset

This step needs `use_real_icat: true` (step 2/3 with the local demo data has
no real files behind it). On a `MatchedDataset` from a real ICAT+ search,
`file_extensions_filter` already defaults to `h5` (clear it for the whole
dataset, or set e.g. `json` instead); click **Download Files** and save. The
files are extracted into your upload under `downloaded_folder` (the zip is
discarded), listed in `downloaded_files` — anonymously, since ICAT+ allows
unauthenticated downloads for public datasets.

## 5. Query the REST API directly

The same data is reachable without the ELN, for machine clients:

```bash
curl 'http://localhost:8000/nomad-oasis/semantic-web-service/map?term=PaNET01196'

curl 'http://localhost:8000/nomad-oasis/semantic-web-service/catalogue/public/datasets/874478618/download?fileExtensions=json' -o dataset.zip
```

See [How to use this plugin](../how_to/use_this_plugin.md) for more routes.
