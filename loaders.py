import json

import requests
import os
import h3
from pathlib import Path
import pandas as pd
import parse
from settings import Settings


def geo_index(h):
    # properly format the geospatial index in geoJSON format from the hex
    try:
        coordinates = h3.h3_to_geo(h)
    except TypeError:
        coordinates = [0, 0]
    return {"type": "Point", "coordinates": [coordinates[1], coordinates[0]]}


def get_latest_inventory_height(settings: Settings) -> int:
    url = settings.latest_inventories_url
    inventories = requests.get(url).json()
    inventory_height = int(parse.parse("gateway_inventory_{0}.csv.gz", inventories["gateway_inventory"].split("/")[-1])[0])
    return inventory_height


def process_gateway_inventory(settings: Settings) -> (pd.DataFrame, int):
    gz_path = Path("gateway_inventory_latest.csv.gz")
    csv_path = Path("gateway_inventory_latest.csv")

    url = settings.latest_inventories_url
    inventories = requests.get(url).json()

    inventory_raw = requests.get(inventories["gateway_inventory"]).content
    with open(gz_path, "wb") as f:
        f.write(inventory_raw)

    data = pd.read_csv(gz_path, compression="gzip")
    data = data.drop(["Unnamed: 0"], axis=1)
    data = data.dropna()
    data = data.set_index("address")

    try:
        os.remove(gz_path)
        os.remove(csv_path)
    except FileNotFoundError:
        pass

    inventory_height = int(parse.parse("gateway_inventory_{0}.csv.gz", inventories["gateway_inventory"].split("/")[-1])[0])

    return data, inventory_height


def get_denylist(settings: Settings) -> pd.DataFrame:

    denylist = pd.DataFrame(requests.get(settings.denylist_url).text.split(",\n"))
    denylist.columns = ["address"]
    denylist.set_index("address")
    return denylist


def get_latest_denylist_tag() -> str:

    r = requests.get("https://api.github.com/repos/helium/denylist/releases/latest")
    return r.json()["tag_name"]


def get_frequency_plans() -> list[dict]:
    regions_url = "https://raw.githubusercontent.com/dewi-alliance/hplans/main/regions.geojson"
    regions_path = "static/regions.geojson"
    if os.path.exists(regions_path) is False:
        if os.path.isdir("static") is False:
            os.mkdir("static")
        regions_json = requests.get(regions_url).json()
        with open(regions_path, "w") as f:
            json.dump(regions_json, f)

    else:
        with open(regions_path, "r") as f:
            regions_json = json.load(f)

    return regions_json

