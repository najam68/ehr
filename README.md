# Django EHR Starter (Clean-Room) — v0.2

Adds **one-time data bootstrap** with a **manifest-driven importer** so you can fetch/import once now and swap to your own APIs later.

## What's new in v0.2
- `ingestion` app now has a `import_data` management command that reads a **YAML manifest** (see `data/manifest.yaml`).
- Sample datasets under `data/sources/` with **provenance**: NUCC taxonomy (sample), CMS POS codes (sample), and a small payer seed.
- Each import records a `Provenance` row with file hash + declared source.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate

# Load initial fixtures (optional)
python manage.py loaddata clinical_directory/fixtures/care_settings.yaml
python manage.py loaddata clinical_directory/fixtures/specialties.yaml
python manage.py loaddata intake_catalog/fixtures/catalogue_global.yaml

# Import bootstrap data from manifest (NUCC/CMS samples)
python manage.py import_data data/manifest.yaml

python manage.py runserver 0.0.0.0:8000
```

## Data path clarity (catalogue-based)
- The **manifest** declares: dataset id, description, source system, source URL (for your records), local path, format, target model, and mapping logic.
- Every imported file is hashed (SHA-256) and stored in `ingestion_provenance` with the dataset id, so you always know **where the CSV came from**.

See `data/README_DATA_SOURCES.md` for notes and official-source pointers you can replace later with your own APIs.
# ehr
