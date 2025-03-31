import os
import requests
import geoip2.database
from config import GEOIP_DATABASES_AUTO_UPDATE

DATABASES = ["ASN", "City", "Country"]


def _download_database(database: str) -> bool:
    """
    Download the specified GeoLite2 database from MaxMind.
    """
    url = f"https://git.io/GeoLite2-{database}.mmdb"
    if os.path.exists(os.path.join(os.getcwd(), f"data/GeoLite2-{database}.etag")):
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code != 200:
            return False
        etag = response.headers.get("ETag")
        local_etag = open(
            os.path.join(os.getcwd(), f"data/GeoLite2-{database}.etag"), "r"
        ).read()
        if etag == local_etag:
            return True
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        with open(
            os.path.join(os.getcwd(), f"data/GeoLite2-{database}.mmdb"), "wb"
        ) as file:
            file.write(response.content)
        with open(
            os.path.join(os.getcwd(), f"data/GeoLite2-{database}.etag"), "w"
        ) as file:
            file.write(response.headers["ETag"])
        return True
    return False


def update_databases() -> None:
    """
    Update the GeoLite2 databases.
    """
    print("Updating GeoLite2 databases...(may take a while)")
    for database in DATABASES:
        if (
            os.path.exists(os.path.join(os.getcwd(), f"data/GeoLite2-{database}.etag"))
            and not GEOIP_DATABASES_AUTO_UPDATE
        ):
            print(f"Skipped updating {database} database.")
            continue
        try:
            if _download_database(database):
                print(f"Downloaded {database} database.")
            else:
                print(f"Failed to download {database} database.")
        except Exception as e:
            print(f"Error downloading {database} database: {e}")
    print("Database update completed.")


for database in DATABASES:
    try:
        globals()[f"{database.upper()}_DATABASE"] = geoip2.database.Reader(
            os.path.join(os.getcwd(), f"data/GeoLite2-{database}.mmdb")
        )
    except Exception:
        globals()[f"{database.upper()}_DATABASE"] = None


def get_asn(ip: str) -> dict | None:
    """
    Get ASN information for a given IP address.
    """
    ASN_DATABASE: geoip2.database.Reader = globals()["ASN_DATABASE"]
    if ASN_DATABASE:
        try:
            return ASN_DATABASE.asn(ip).to_dict()
        except Exception:
            return None
    return None


def get_city(ip: str) -> dict | None:
    """
    Get city information for a given IP address.
    """
    CITY_DATABASE: geoip2.database.Reader = globals()["CITY_DATABASE"]
    if CITY_DATABASE:
        try:
            return CITY_DATABASE.city(ip).to_dict()
        except Exception:
            return None
    return None


def get_country(ip: str) -> dict | None:
    """
    Get country information for a given IP address.
    """
    COUNTRY_DATABASE: geoip2.database.Reader = globals()["COUNTRY_DATABASE"]
    if COUNTRY_DATABASE:
        try:
            return COUNTRY_DATABASE.country(ip).to_dict()
        except Exception:
            return None
    return None
