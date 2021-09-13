from datetime import datetime
from shapely.geometry import Polygon, mapping

import pystac
import pystac.extensions.eo
import stac_ingest.utils.utils as utils


class StacStaticCatalogBuilder(object):
    def build(self, metadata, catalog_output_path):
        """
        Build static STAC catalog.
        Save to `output/` folder.

        :param metadata:
        :param catalog_output_path:
        :return:
        """
        # Map Collection_name => Collection_items
        all_collection_items = {}

        for i, item in enumerate(metadata):
            stac_collection_item = self.get_collection_item(item)
            stac_collection_name = item["collection_name"]

            if stac_collection_name not in all_collection_items:
                all_collection_items[stac_collection_name] = []

            all_collection_items[stac_collection_name].append({
                "collection_title": item["collection_title"],
                "stac_item": stac_collection_item
            })

        # Get actual collections
        collections = []

        for i, collection_name in enumerate(all_collection_items):
            collection_items = all_collection_items[collection_name]
            collection = self.get_collection(collection_items, collection_name)
            collections.append(collection)

        catalog = self.get_catalog(collections)
        self.persist(catalog, catalog_output_path)


    def persist(self, catalog, catalog_output_path):
        # normalize and save
        print("[INFO] Save path : " + catalog_output_path)
        catalog.describe()
        catalog.normalize_hrefs(catalog_output_path)
        catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)


    def get_collection_item(self, item):
        # get bbox and footprint
        bounds = {
            "left" : -140.99778,
            "bottom" : 41.6751050889,
            "right" : -52.6480987209,
            "top" : 83.23324
        }
        bbox = [bounds["left"], bounds["bottom"], bounds["right"], bounds["top"]]
        footprint = Polygon([
            [bounds["left"], bounds["bottom"]],
            [bounds["left"], bounds["top"]],
            [bounds["right"], bounds["top"]],
            [bounds["right"], bounds["bottom"]]
        ])

        collection_item = pystac.Item(id=item["dataset_name"],
                                      geometry=mapping(footprint),
                                      bbox=bbox,
                                      datetime=datetime.utcnow(),
                                      properties={},
                                      collection=item["collection_name"],
                                      stac_extensions=[pystac.Extensions.DATACUBE])

        # TODO : utils.MockDateTime() has been used since STAC API requires date in %Y-%m-%dT%H:%M:%SZ format while
        #  pystac.Item.datetime include the ms
        collection_item.datetime = utils.MockDateTime()
        collection_item.properties["start_datetime"] = "1950-10-22T13:51:21Z"
        collection_item.properties["end_datetime"] = "2100-10-22T13:51:21Z"
        collection_item.properties["created"] = "2013-11-04T06:15:26Z"
        collection_item.properties["updated"] = "2017-11-04T06:15:26Z"
        collection_item.properties["provenance:provider"] = "Ouranos"
        collection_item.properties["provenance:location"] = "thredds"
        collection_item.properties["cmip5:activity_id"] = item["activity_id"]
        collection_item.properties["cmip5:institute_id"] = item["institute_id"]
        collection_item.properties["cmip5:source_id"] = item["source_id"]
        collection_item.properties["cmip5:experiment_id"] = item["experiment_id"]
        collection_item.properties["cmip5:member_id"] = item["member_id"]
        collection_item.properties["cmip5:table_id"] = item["table_id"]
        collection_item.properties["cmip5:variable_id"] = item["variable_id"]
        collection_item.properties["cmip5:grid_label"] = item["grid_label"]
        collection_item.properties["cmip5:conventions"] = item["conventions"]
        collection_item.properties["cmip5:frequency"] = item["frequency"]
        collection_item.properties["cmip5:modeling_realm"] = item["modeling_realm"]

        # link = pystac.Link(rel="alternate", target="link to TDS", media_type="text/html", title="Data on Thredds")
        # collection_item.add_link(link)

        asset = pystac.Asset(href=item["thumbnail_url"], media_type="image/png", title="Thumbnail", roles=["thumbnail"])
        collection_item.add_asset('thumbnail', asset)

        asset = pystac.Asset(href=item["http_url"], media_type="application/netcdf", title="NetCDF file", roles=["data"])
        collection_item.add_asset('metadata_http', asset)

        asset = pystac.Asset(href=item["iso_url"], media_type="application/xml", title="Metadata ISO", roles=["metadata"])
        collection_item.add_asset('metadata_iso', asset)

        asset = pystac.Asset(href=item["ncml_url"], media_type="application/xml", title="Metadata NcML", roles=["metadata"])
        collection_item.add_asset('metadata_ncml', asset)

        return collection_item


    def get_collection(self, collection_items, collection_name):
        # extents
        sp_extent = pystac.SpatialExtent([-140.99778, 41.6751050889, -52.6480987209, 83.23324])
        capture_date_start = datetime.strptime('1950-10-22', '%Y-%m-%d')
        capture_date_end = datetime.strptime('2100-10-22', '%Y-%m-%d')
        tmp_extent = pystac.TemporalExtent([(capture_date_start, capture_date_end)])
        extent = pystac.Extent(sp_extent, tmp_extent)

        collection = pystac.Collection(id=collection_name,
                                       title=collection_items[0]["collection_title"],
                                       description=collection_name,
                                       extent=extent,
                                       license='n/a',
                                       keywords=["bccaqv2", "anusplin", "cmip5"])

        collection.providers = [
            pystac.Provider(name='PCIC', roles=['producer'], url='https://www.pacificclimate.org/'),
            pystac.Provider(name='Ouranos', roles=['processor', 'host'],
                            url='https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/')
        ]

        collection_items_array = []

        for collection_item in collection_items:
            collection_items_array.append(collection_item["stac_item"])

        collection.add_items(collection_items_array)

        return collection


    def get_catalog(self, collections):
        catalog = pystac.Catalog(id='STAC TDS Climate Data Catalog',
                                 description='List of TDS catalog data represented in a STAC catalog.')

        catalog.clear_items()
        catalog.clear_children()
        catalog.add_children(collections)

        return catalog
