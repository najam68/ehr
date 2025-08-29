# Data Sources (Bootstrap Samples)

This folder contains **sample** CSVs and a **manifest** to demonstrate one-time import.
Replace the `source.url` fields with your official sources and point `local_path` to your full CSVs when ready.

## Included samples
- `nucc_sample.csv` — few rows from NUCC taxonomy (for demonstration only).
- `cms_pos_sample.csv` — few Place of Service (POS) codes from CMS (demo only).
- `payers_sample.csv` — placeholder payer directory (demo only).

Each dataset is declared in `manifest.yaml` with:
- `id`, `description`
- `source.system`, `source.url`, `source.local_path`
- `format`, `target` (app/model), `mapping` (CSV column → model field), `key_fields`

Provenance of each import is recorded in the DB (see admin or `ingestion_provenance` table).
