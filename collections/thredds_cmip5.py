from .collection_base import CollectionBase

import tds


class ThreddsCmip5(CollectionBase):
    """
    Implementation of Thredds CMIP5 metadata processing logic.
    """

    def add_metadata(self, ds):
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

    def get_stac_collection(self, item):
        pass

    def get_stac_collection_item(self, collection_items, collection_name):
        pass

