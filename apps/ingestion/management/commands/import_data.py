import csv, yaml, os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.apps import apps
from apps.ingestion.models import Provenance
from pathlib import Path
import hashlib
from django.core.exceptions import ObjectDoesNotExist

def sha256_path(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def upsert(model, lookup: dict, values: dict):
    obj, created = model.objects.update_or_create(**lookup, defaults=values)
    return obj, created

def _normalize_values(app_label: str, model_name: str, values: dict):
    """
    Light normalization so CSVs import cleanly:
    - Strip whitespace from all string fields
    - Lowercase 'slug' if present
    - Coerce certain JSON-ish fields into lists (e.g., pos_codes)
    """
    # strip strings
    for k, v in list(values.items()):
        if isinstance(v, str):
            values[k] = v.strip()

    # normalize slug
    if "slug" in values and values["slug"]:
        values["slug"] = values["slug"].lower()

    # simple JSON list coercions
    if "pos_codes" in values and values["pos_codes"] not in (None, ""):
        v = values["pos_codes"]
        if isinstance(v, str):
            # allow comma or pipe separated
            parts = [p.strip() for p in v.replace("|", ",").split(",") if p.strip()]
            values["pos_codes"] = parts if parts else [v.strip()]
        elif not isinstance(v, list):
            values["pos_codes"] = [str(v)]

    return values

def _validate_foreign_keys(app_label: str, model_name: str, values: dict, ds_id: str):
    """
    Minimal FK validation for known datasets:
    - codes.Code.system_id must exist in codes.CodeSystem
    - clinical_directory.Clinic.care_setting_id must exist in clinical_directory.CareSetting
    """
    if app_label == "codes" and model_name.lower() == "code":
        if "system_id" not in values:
            raise CommandError(f"[{ds_id}] missing system_id for code {values.get('code')}")
        SysModel = apps.get_model("codes", "CodeSystem")
        sys_id = values.get("system_id")
        if not SysModel.objects.filter(pk=sys_id).exists():
            raise CommandError(f"[{ds_id}] unknown system_id '{sys_id}' for code {values.get('code')}")

    if app_label == "clinical_directory" and model_name.lower() == "clinic":
        if "care_setting_id" not in values:
            raise CommandError(f"[{ds_id}] missing care_setting_id for clinic {values.get('slug') or values.get('name')}")
        CSModel = apps.get_model("clinical_directory", "CareSetting")
        cs = values.get("care_setting_id")
        if not CSModel.objects.filter(pk=cs).exists():
            raise CommandError(f"[{ds_id}] unknown care_setting_id '{cs}' for clinic {values.get('slug') or values.get('name')}")

class Command(BaseCommand):
    help = "Import datasets from a YAML manifest (one-time bootstrap)."

    def add_arguments(self, parser):
        parser.add_argument("manifest", type=str, help="Path to manifest.yaml")

    @transaction.atomic
    def handle(self, *args, **opts):
        manifest_path = opts["manifest"]
        if not os.path.exists(manifest_path):
            raise CommandError(f"Manifest not found: {manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        datasets = manifest.get("datasets", [])
        if not datasets:
            self.stdout.write(self.style.WARNING("No datasets in manifest."))
            return

        for ds in datasets:
            ds_id = ds.get("id")
            desc = ds.get("description", "")
            src = ds.get("source", {})
            local_path = src.get("local_path")
            source_system = src.get("system", "")
            source_url = src.get("url", "")

            if not local_path or not os.path.exists(local_path):
                raise CommandError(f"[{ds_id}] local_path missing or not found: {local_path}")

            file_hash = sha256_path(local_path)
            prov = Provenance.objects.create(
                source_system=source_system or ds_id,
                file_name=os.path.basename(local_path),
                file_hash=file_hash,
                format=ds.get("format", "CSV").upper(),
                notes=f"{desc} | Declared source: {source_url}",
            )

            target = ds.get("target", {})
            app_label = target.get("app")
            model_name = target.get("model")
            mapping = target.get("mapping", {})
            if not app_label or not model_name:
                raise CommandError(f"[{ds_id}] target app/model missing.")

            Model = apps.get_model(app_label, model_name)
            key_fields = target.get("key_fields") or []  # used for upsert

            self.stdout.write(self.style.NOTICE(f"[{ds_id}] importing -> {app_label}.{model_name}"))

            with open(local_path, "r", encoding=ds.get("encoding", "utf-8-sig")) as fcsv:
                reader = csv.DictReader(fcsv)
                count = 0
                for row in reader:
                    # map CSV → model fields
                    values = {}
                    for dst, src_col in mapping.items():
                        raw = row.get(src_col)
                        if isinstance(raw, str):
                            raw = raw.strip()
                        values[dst] = raw

                    # convenience: if slug missing but title present, derive it
                    if "slug" in values and (values["slug"] in (None, "")) and "title" in values:
                        values["slug"] = (values["title"] or "").lower().replace(" ", "-")

                    # normalize common fields
                    values = _normalize_values(app_label, model_name, values)

                    # validate known FKs
                    _validate_foreign_keys(app_label, model_name, values, ds_id)

                    # build lookup for upsert
                    lookup = {k: values[k] for k in key_fields} if key_fields else values

                    obj, created = upsert(Model, lookup, values)
                    count += 1

                self.stdout.write(self.style.SUCCESS(f"[{ds_id}] rows processed: {count}; provenance id={prov.id}"))

        self.stdout.write(self.style.SUCCESS("All datasets imported."))
