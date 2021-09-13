from siphon.catalog import TDSCatalog
from stac_ingest.metadata_validator import MetadataValidator, REGISTERED_SCHEMAS, OBJECT_TYPE, SCHEMAS
from colorlog import ColoredFormatter
from botocore.client import Config
from owslib.wms import WebMapService

import stac_ingest.utils.tds as tds
import logging
import re
import boto3
import os

from dotenv import load_dotenv
load_dotenv()


# setup logger
LOGGER = logging.getLogger(__name__)
LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setFormatter(formatter)
LOGGER.addHandler(stream)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False

TMP_PATH = "../tmp"
DEFAULT_CANADA_BBOX = (-140.99778,41.6751050889,-52.6480987209,83.23324)


class TDSCrawler(object):
    iter_obj = 0
    iter_item = 0

    def run(self, tds_catalog_url):
        """
        Crawl TDS.

        :param tds_catalog_url:
        :return:
        """
        # create the temp thumbnail path
        if not os.path.exists(TMP_PATH):
            os.makedirs(TMP_PATH)

        top_cat = TDSCatalog(tds_catalog_url)
        tds_ds = self.parse_datasets(top_cat)

        os.rmdir(TMP_PATH)

        print("[INFO] Finished crawling TDS")

        return tds_ds

    def parse_datasets(self, catalog):
        """
        Collect all available datasets.
        """
        datasets = []

        for dataset_name, dataset_obj in catalog.datasets.items():
            http_url = dataset_obj.access_urls.get("httpserver", "")
            odap_url = dataset_obj.access_urls.get("opendap", "")
            ncml_url = dataset_obj.access_urls.get("ncml", "")
            uddc_url = dataset_obj.access_urls.get("uddc", "")
            iso_url = dataset_obj.access_urls.get("iso", "")
            wcs_url = dataset_obj.access_urls.get("wcs", "")
            wms_url = dataset_obj.access_urls.get("wms", "")

            # obtain the collection name
            # TODO : hardcoded BCCAQv2 string
            m = re.search('\/BCCAQv2\/([^\/]+)', catalog.catalog_url)
            if m:
                collection_name = m.group(1)
            else:
                collection_name = "undefined"
                # collection_name = catalog.catalog_url[97:-12].replace("/", "_")       # eg: BCCAQv2_tx_mean_allrcps_ensemble_stats_YS

            item = {
                "dataset_name" : dataset_name.split(".")[0],
                "collection_name" : "BCCAQv2_" + collection_name,
                "collection_title": "BCCAQv2 " + collection_name,
                "http_url" : http_url,
                "odap_url" : odap_url,
                "ncml_url" : ncml_url,
                "uddc_url" : uddc_url,
                "iso_url" : iso_url,
                "wcs_url" : wcs_url,
                "wms_url" : wms_url
            }

            LOGGER.info("[INFO] Found TDS dataset [%s]", dataset_name)
            item = self.add_tds_ds_metadata(item)
            item_metadata_schema_uri = REGISTERED_SCHEMAS[SCHEMAS.CMIP5][OBJECT_TYPE.SCHEMA]
            item_metadata_root = REGISTERED_SCHEMAS[SCHEMAS.CMIP5][OBJECT_TYPE.ROOT]
            metadata_validator = MetadataValidator()
            is_valid = metadata_validator.is_valid(item, item_metadata_schema_uri, item_metadata_root)

            if is_valid:
                datasets.append(item)
                LOGGER.info("[INFO] Valid dataset [%s]", dataset_name)
            else:
                LOGGER.warning("[WARNING] Invalid dataset [%s]", dataset_name)

            # retrieve thumbnail
            if os.getenv("GENERATE_THUMBNAILS", 'False') == 'True':
                ds_meta = self.get_wms_meta_first_layer(wms_url)

                if ds_meta is not None:
                    item["thumbnail"] = item["dataset_name"] + "_" + ds_meta["layer_name"] + ".png"
                    item["thumbnail_url"] = os.getenv("BLOB_HOST") + "/" + os.getenv("BLOB_BUCKET") + "/" + item["thumbnail"]
                    item["title"] = ds_meta["layer_title"]
                    image_path = TMP_PATH + item["thumbnail"]
                    self.get_thumbnail(wms_url, image_path, ds_meta["layer_name"], ds_meta["layer_srs"], DEFAULT_CANADA_BBOX)
                    self.store_thumbnail_blob(image_path, item["thumbnail"])
                    os.remove(image_path)
                else:
                    default_thumbnail = "https://app.flourish.studio/template/300/thumbnail"
                    item["thumbnail"] = default_thumbnail
                    item["thumbnail_url"] = default_thumbnail
                    item["title"] = "undefined"

            self.iter_item += 1
            if self.iter_item > int(os.getenv("CRAWL_MAX_ITEM")) and os.getenv("CRAWL_LIMIT_RESULTS", 'False') == 'True':
                break

        for catalog_name, catalog_obj in catalog.catalog_refs.items():
            d = self.parse_datasets(catalog_obj.follow())
            datasets.extend(d)

            self.iter_obj += 1
            if self.iter_obj > int(os.getenv("CRAWL_MAX_OBJ")) and os.getenv("CRAWL_LIMIT_RESULTS", 'False') == 'True':
                break

        return datasets


    def add_tds_ds_metadata(self, ds):
        """
        Add extra metadata to item.
        """
        # TODO : hardcoded, replace with regexes
        # TODO : Extract metadata from ncml_url and iso_url
        url_attrs = ds["http_url"].split("/")
        ds_attrs = ds["dataset_name"].split("_")
        ncml_attrs = tds.attrs_from_ncml(ds["ncml_url"])

        # cmip5 sample
        extra_meta = {
            "provider": "pavics-thredds",
            "activity_id": ncml_attrs.get("project_id", "n/a"),
            "institute_id": ncml_attrs.get("institute_id", "n/a"),
            "source_id": "n/a",
            "experiment_id": ncml_attrs.get("driving_experiment", "n/a"),
            "member_id": "n/a",
            "table_id": "n/a",
            "variable_id": "n/a",
            "grid_label": "n/a",
            "conventions": ncml_attrs.get("Conventions", "n/a"),
            "frequency": ncml_attrs.get("frequency", "n/a"),
            "modeling_realm": ncml_attrs.get("modeling_realm", "n/a"),
            "model_id": ncml_attrs.get("model_id", "n/a")
        }

        return dict(ds, **extra_meta)


    def get_wms_meta_first_layer(self, url):
        wms = WebMapService(url, version='1.3.0')

        if len(list(wms.contents)) == 0:
            return None

        layer_name = list(wms.contents)[0]

        meta = {
            "layer_name": layer_name,
            "layer_srs": wms[layer_name].crs_list[0][4],    # in the GetMap operation the srs parameter is called crs in 1.3.0. GeoServer supports both keys regardless of version.
            "layer_title": wms[layer_name].title
        }

        return meta


    def get_thumbnail(self, url, output_file, layer, srs, bbox):
        # sample query, via url
        # https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/wms/birdhouse/cccs_portal/indices/Final/BCCAQv2/tx_mean/allrcps_ensemble_stats/YS/BCCAQv2+ANUSPLIN300_ensemble-percentiles_historical+allrcps_1950-2100_tx_mean_YS.nc?service=WMS&version=1.3.0&request=GetMap&format=image/png&transparent=true&layers=%20rcp26_tx_mean_p10&hints=quality&width=740&height=420&crs=CRS:84&bbox=-140.99778,41.6751050889,-52.6480987209,83.23324&styles=boxfill/ncview

        wms = WebMapService(url, version='1.3.0')
        img = wms.getmap(layers=[layer],
                         styles=['boxfill/ncview'],
                         srs=srs,
                         bbox=bbox,
                         size=(256, 256),
                         format='image/png',
                         transparent=True
                         )
        out = open(output_file, 'wb')
        out.write(img.read())
        out.close()


    def store_thumbnail_blob(self, file_src, file_dst):
        s3 = boto3.resource('s3',
                            endpoint_url=os.getenv("BLOB_HOST"),
                            aws_access_key_id='minio',
                            aws_secret_access_key='minio123',
                            config=Config(signature_version='s3v4'),
                            region_name='us-east-1')

        s3.Bucket(os.getenv("BLOB_BUCKET")).upload_file(file_src, file_dst)