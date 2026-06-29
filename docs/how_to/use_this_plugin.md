# How to Use This Plugin

This plugin can be used in a NOMAD Oasis installation.

## Add This Plugin to Your NOMAD installation

Read the [NOMAD plugin documentation](https://nomad-lab.eu/prod/v1/staging/docs/plugins/plugins.html#add-a-plugin-to-your-nomad) for all details on how to deploy the plugin on your NOMAD instance.

## Using the REST API

The API is mounted at `{api_base_path}/semantic-web-service` (in this repo's dev
setup, `http://localhost:8000/nomad-oasis/semantic-web-service`):

```bash
curl 'http://localhost:8000/nomad-oasis/semantic-web-service/health'

curl 'http://localhost:8000/nomad-oasis/semantic-web-service/catalogue/public/datasets?startDate=2021-01-01T00:00:00Z&endDate=2022-12-31T23:59:59Z&techniquePids=https://w3id.org/PaN/ESRFET%23XAS&instrumentName=ID21'

curl 'http://localhost:8000/nomad-oasis/semantic-web-service/map?term=PaNET01196&source=PANET&target=ESRFET'

# Download a real public dataset anonymously, optionally filtered by file extension:
curl 'http://localhost:8000/nomad-oasis/semantic-web-service/catalogue/public/datasets/874478618/download?fileExtensions=json' -o dataset.zip
```

See the [reference](../reference/references.md) for all routes, or open
`.../semantic-web-service/docs` for the interactive Swagger UI.

## Using the ELN schema

1. In the NOMAD GUI, create a new entry of type **Dataset search request**.
2. Fill in `synchrotron` (only `ESRF` is currently wired to a live endpoint),
   `vocabulary` (`ESRFET` or `PANET`), `technique_term`, `start_date`, `end_date`,
   and optionally `instrument_name`.
3. Save the entry. `resolved_technique_term` is resolved (after PANET→ESRFET
   mapping, if applicable) and the search runs automatically in the same save —
   `matched_datasets` is populated immediately, including a DOI-based
   `landing_page` where available. Editing the search fields and saving again
   re-runs the search; saving for an unrelated reason (e.g. step 4 below)
   does not, so it won't discard work in progress on `matched_datasets` items.
4. Toggle `use_real_icat` to query the real ESRF ICAT+ endpoint instead of the
   local demo data (requires network access to `icatplus.esrf.fr`).
5. To download a matched dataset's files: open it in `matched_datasets`,
   optionally adjust `file_extensions_filter` (defaults to `h5`; clear it to
   get the whole dataset), then click the **Download Files** action button
   and save. The files are extracted into the upload under `downloaded_folder`
   (e.g. `dataset-874478618/`), listed in `downloaded_files`; the zip itself is
   discarded. This only works for real ICAT+ results (step 4) — the local
   demo data has no real files behind it.
