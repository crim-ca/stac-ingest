from stac_ingest.stac_static_catalog_builder import StacStaticCatalogBuilder
from stac_ingest.tds_crawler import TDSCrawler
from stac_ingest.stac_dynamic_catalog_builder import StacDynamicCatalogBuilder
from dotenv import load_dotenv

import json
import os
import shutil

load_dotenv()


def main():
    CACHE_FILEPATH = "../tds_cache.json"
    TEST_DATA = False
    tds_catalog_url = os.getenv("THREDDS_CATALOG")
    catalog_output_path = os.path.join(os.getcwd(), "../output")
    stac_host = os.getenv("STAC_HOST")

    # add feat. toggle in config - only for test, we always clean the STAC API
    from stac_ingest.stac_api_data_eraser import destroy_stac_data
    destroy_stac_data()
    shutil.rmtree(catalog_output_path, ignore_errors=True)

    # PHASE I - TDS Crawler
    if os.path.exists(CACHE_FILEPATH):
        print("[INFO] Use cache")
        with open(CACHE_FILEPATH, 'r') as file:
            tds_ds = json.load(file)
    # elif not TEST_DATA:
    # if True:
    #     print("[INFO] Build and use cache")
    #     tds_crawler = TDSCrawler()
    #     tds_ds = tds_crawler.run(tds_catalog_url)
    #     with open(CACHE_FILEPATH, "w") as data_file:
    #         json.dump(tds_ds, data_file, indent=4)
    # else:
    if False:
        print("[INFO] Use testdata")
        tds_ds = [
            {
                "dataset_name": "BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS",
                "collection_name": "BCCAQv2_txgt_37",
                "collection_title": "BCCAQv2 txgt_37",
                "http_url": "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/fileServer/birdhouse/cccs_portal/indices/Final/BCCAQv2/txgt_37/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS.nc",
                "odap_url": "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/birdhouse/cccs_portal/indices/Final/BCCAQv2/txgt_37/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS.nc",
                "ncml_url": "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/ncml/birdhouse/cccs_portal/indices/Final/BCCAQv2/txgt_37/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS.nc",
                "uddc_url": "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/uddc/birdhouse/cccs_portal/indices/Final/BCCAQv2/txgt_37/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS.nc",
                "iso_url": "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/iso/birdhouse/cccs_portal/indices/Final/BCCAQv2/txgt_37/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS.nc",
                "wcs_url": "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/wcs/birdhouse/cccs_portal/indices/Final/BCCAQv2/txgt_37/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS.nc",
                "wms_url": "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/wms/birdhouse/cccs_portal/indices/Final/BCCAQv2/txgt_37/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS.nc",
                "provider": "pavics-thredds",
                "activity_id": "CMIP5",
                "institute_id": "CCCS",
                "source_id": "n/a",
                "experiment_id": "historical,rcp26,rcp45,rcp85",
                "member_id": "n/a",
                "table_id": "n/a",
                "variable_id": "n/a",
                "grid_label": "n/a",
                "conventions": "CF-1.4",
                "frequency": "day",
                "modeling_realm": "atmos",
                "model_id": "n/a",
                "thumbnail": "BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS_rcp26_txgt_37_p10.png",
                "thumbnail_url": "http://localhost:9050/blob/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_txgt_37_YS_rcp26_txgt_37_p10.png"
            }
        ]

    # PHASE II - STAC Static Catalog Builder
    stacStaticCatalogBuilder = StacStaticCatalogBuilder()
    stacStaticCatalogBuilder.build(tds_ds, catalog_output_path)

    # PHASE III - STAC API Dynamic Catalog Builder
    stacDynamicCatalogBuilder = StacDynamicCatalogBuilder()
    stacDynamicCatalogBuilder.build(catalog_output_path, stac_host)


if __name__ == "__main__":
    main()
