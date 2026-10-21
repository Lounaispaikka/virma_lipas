"""Settings of the importer.

The settings are read from the environment. During development the values can
be kept in a .env file in the project root, see .env.example. Environment
variables always take precedence over the values in the .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# The .env file is a convenience for development and for the docker container,
# the settings are always read from the environment.
load_dotenv(Path.cwd() / ".env")
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _str(name, default=""):
    return os.environ.get(name, default)


def _bool(name, default=False):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _int(name, default):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return int(value)


def _int_list(name, default):
    value = os.environ.get(name)
    if value is None or value == "":
        return list(default)
    return [int(item) for item in value.split(",") if item.strip()]


username = _str("DB_USER", "postgres")
password = _str("DB_PASSWORD", "postgres")
db = _str("DB_NAME", "virma")
host = _str("DB_HOST", "127.0.0.1")
port = _int("DB_PORT", 5432)

epsg = _int("EPSG", 3067)

DEBUG = _bool("DEBUG", False)
onlyFreeUse = _bool("ONLY_FREE_USE", False)
FULL_UPDATE = _bool("FULL_UPDATE", False)
SENTRY_DSN = _str("SENTRY_DSN", "")

cityCodes = _int_list(
    "CITY_CODES",
    [19, 284, 430, 480, 561, 636, 734, 761, 202, 423, 481, 503, 529, 538, 577, 680, 704, 738, 853, 322, 445, 304, 400, 631, 833, 895, 918],
)

LIPAS_DATETIME_FORMAT = _str("LIPAS_DATETIME_FORMAT", "%Y-%m-%d %H:%M:%S.%f")
LIPAS_DATETIME_DELETE_FORMAT = _str("LIPAS_DATETIME_DELETE_FORMAT", "%Y-%m-%d %H:%M:%S")
