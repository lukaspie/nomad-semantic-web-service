# How to Use This Plugin

This plugin can be used in a NOMAD Oasis installation.

## Add This Plugin to Your NOMAD installation

Read the [NOMAD plugin documentation](https://nomad-lab.eu/prod/v1/staging/docs/plugins/plugins.html#add-a-plugin-to-your-nomad) for all details on how to deploy the plugin on your NOMAD instance.

## Using the REST API

The API is mounted at `{api_base_path}/semantic-web-service` (in this repo's dev
setup, `http://localhost:8000/nomad-oasis/semantic-web-service`):

```bash
curl 'http://localhost:8000/nomad-oasis/semantic-web-service/health'

curl 'http://localhost:8000/nomad-oasis/semantic-web-service/catalogue/public/datasets?startDate=2024-01-01T00:00:00Z&endDate=2024-12-31T23:59:59Z&techniquePids=https://w3id.org/PaN/ESRFET%23XAS&instrumentName=ID21'

curl 'http://localhost:8000/nomad-oasis/semantic-web-service/map?term=PaNET01196&source=PANET&target=ESRFET'
```

See the [reference](../reference/references.md) for all routes, or open
`.../semantic-web-service/docs` for the interactive Swagger UI.

## Using the ELN schema

1. In the NOMAD GUI, create a new entry of type **Dataset search request**.
2. Fill in `synchrotron` (only `ESRF` is currently wired to a live endpoint),
   `vocabulary` (`ESRFET` or `PANET`), `technique_term`, `start_date`, `end_date`,
   and optionally `instrument_name`.
3. Save the entry. `resolved_technique_term` is resolved automatically on every
   save (after PANET→ESRFET mapping, if applicable) — review it before searching.
4. Click the **Run Search** action button and save again. `matched_datasets` is
   then populated with the matching dataset records, including a DOI-based
   `landing_page` where available.
5. Toggle `use_real_icat` to query the real ESRF ICAT+ endpoint instead of the
   local demo data (requires network access to `icatplus.esrf.fr`).
