import intake
import satsearch
from dotenv import load_dotenv

import os

load_dotenv()

stac_host = os.getenv("STAC_HOST")

def main():
    test_consume_stac_api(stac_host, "BCCAQv2_tx_mean_allrcps_ensemble_stats_YS")


def test_consume_stac_api(stac_host, collection):
    dates = '1949-02-12T00:00:00Z/2122-03-18T12:31:12Z'

    results = satsearch.Search.search(url=stac_host,
                                      collections=[collection],
                                      datetime=dates,
                                      sort=['<datetime'])

    if results.found() > 0:
        items = results.items(limit=5)
        catalog = intake.open_stac_item_collection(items)

        print()
        print("[INFO] Printing STAC catalog")
        print(catalog)
        print()

        print("[INFO] Printing first STAC item")
        item = catalog[list(catalog)[0]]
        print(item)
        print(item.metadata)
    else:
        print("[INFO] No results")


if __name__ == "__main__":
    main()