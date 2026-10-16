import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from imap_tools import MailBox
from bs4 import BeautifulSoup
from laya import Router

_DIR = Path(__file__).resolve().parent
_ROOT = _DIR.parent
for path in (_ROOT, _DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from classifier import classify

'''
EXAMPLE CRITERIA
CRITERIA = {
    "Backup": "aviso automático de respaldo",
}
''' 

from email_criteria import (
    CAVELIER_MANUAL,
    CRITERIA,
    cavelier_categories,
    cavelier_destinations,
)


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


for _env_path in (_ROOT / ".env", _DIR / ".env"):
    _load_dotenv(_env_path)

IMAP_SERVER = os.environ.get("IMAP_HOST") or os.environ.get("IMAP_SERVER", "")
EMAIL_USER = os.environ.get("IMAP_USER", "")
EMAIL_PASSWORD = os.environ.get("IMAP_PASSWORD", "")

LIMIT = 400
OUTPUT_JSON = Path(__file__).with_name("normalized_emails.json")
OUTPUT_CSV = Path(__file__).with_name("classified_emails.csv")


def ingest_emails():
    if not IMAP_SERVER or not EMAIL_USER or not EMAIL_PASSWORD:
        raise SystemExit(
            "Faltan credenciales IMAP. Define IMAP_HOST, IMAP_USER e IMAP_PASSWORD en .env"
        )
    raw_emails = []
    with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD, initial_folder="INBOX") as mailbox:
        for msg in mailbox.fetch(limit=LIMIT, reverse=True):
            raw_emails.append({
                "from": msg.from_,
                "to": list(msg.to),
                "subject": msg.subject,
                "text": msg.text,
                "html": msg.html,
            })
    return raw_emails


def normalize_emails(raw_emails):
    normalized = []
    for email in raw_emails:
        if email["text"]:
            body = email["text"].strip()
        else:
            body = BeautifulSoup(email["html"] or "", "html.parser").get_text(separator="\n", strip=True)

        normalized.append({
            "from": (email["from"] or "").strip(),
            "to": email["to"],
            "subject": (email["subject"] or "").strip(),
            "body": body,
        })

    OUTPUT_JSON.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return normalized


def classify_emails(normalized_emails, lang: str = "es", criteria_set: str = "cavelier"):
    if criteria_set == "qa":
        criteria = CRITERIA
        destinations = {}
        review_category = None
    else:
        criteria = cavelier_categories
        destinations = cavelier_destinations
        review_category = CAVELIER_MANUAL

    router = Router()
    rows = []
    for email in normalized_emails:
        case = SimpleNamespace(
            subject=email["subject"],
            body=email["body"],
            sender=email["from"],
        )
        started = time.perf_counter()
        data, _routing = classify(
            router, case, lang, criteria=criteria, review_category=review_category,
        )
        segundos = round(time.perf_counter() - started, 3)
        categoria = data["categoria"]
        if categoria not in destinations:
            categoria = review_category or categoria
        destination = destinations.get(categoria, "")
        requiere_revision = data["requiere_revision"]
        if review_category:
            requiere_revision = categoria == review_category
        rows.append({
            "from": email["from"],
            "subject": email["subject"],
            "categoria": categoria,
            "probabilidad": data.get("probabilidad"),
            "destination": destination,
            "segundos": segundos,
            "requiere_revision": requiere_revision,
        })

    fieldnames = [
        "from", "subject", "categoria", "probabilidad",
        "destination", "segundos", "requiere_revision",
    ]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return rows


def classification_pipeline(
    skip_ingest=False,
    skip_normalize=False,
    skip_classify=False,
    lang="es",
    criteria_set="cavelier",
):
    if skip_ingest:
        raw_emails = None
    else:
        raw_emails = ingest_emails()
        # top = raw_emails[0]
        # print(top["text"])
        # print("--------------------------------")
        # print(top["html"])
    if skip_normalize:
        normalized_emails = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
    else:
        if raw_emails is None:
            raise SystemExit("Sin ingest: pasa --skip-ingest junto con --skip-normalize")
        normalized_emails = normalize_emails(raw_emails)

    if not skip_classify:
        classify_emails(normalized_emails, lang=lang, criteria_set=criteria_set)

    return normalized_emails


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingesta, normaliza y clasifica correos con Laya.")
    parser.add_argument("--skip-ingest", action="store_true", help="no leer IMAP")
    parser.add_argument("--skip-normalize", action="store_true", help="usar normalized_emails.json")
    parser.add_argument("--skip-classify", action="store_true", help="no clasificar ni escribir CSV")
    parser.add_argument("--lang", default="es", help="idioma para Laya")
    parser.add_argument(
        "--criteria",
        choices=("cavelier", "qa"),
        default="cavelier",
        help="catálogo de categorías para Laya",
    )
    args = parser.parse_args()
    classification_pipeline(
        skip_ingest=args.skip_ingest,
        skip_normalize=args.skip_normalize,
        skip_classify=args.skip_classify,
        lang=args.lang,
        criteria_set=args.criteria,
    )
