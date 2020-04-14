from great_expectations.core.usage_statistics.anonymizers.anonymizer import Anonymizer
from great_expectations.core.usage_statistics.anonymizers.store_backend_anonymizer import (
    StoreBackendAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.site_builder_anonymizer import (
    SiteBuilderAnonymizer,
)


class DataDocsSiteAnonymizer(Anonymizer):
    def __init__(self, salt=None):
        super(DataDocsSiteAnonymizer, self).__init__(salt=salt)
        self._site_builder_anonymizer = SiteBuilderAnonymizer(salt=salt)
        self._store_backend_anonymizer = StoreBackendAnonymizer(salt=salt)

    def anonymize_data_docs_site_info(self, site_name, site_config):
        site_config_module_name = site_config.get("module_name")
        if site_config_module_name is None:
            site_config[
                "module_name"
            ] = "great_expectations.render.renderer.site_builder"

        anonymized_info_dict = self._site_builder_anonymizer.anonymize_site_builder_info(
            site_builder_config=site_config
        )
        anonymized_info_dict["anonymized_name"] = self.anonymize(site_name)

        store_backend_config = site_config.get("store_backend")
        anonymized_info_dict[
            "anonymized_store_backend"
        ] = self._store_backend_anonymizer.anonymize_store_backend_info(
            store_backend_object_config=store_backend_config
        )
        site_index_builder_config = site_config.get("site_index_builder")
        anonymized_site_index_builder = self._site_builder_anonymizer.anonymize_site_builder_info(
            site_builder_config=site_index_builder_config
        )
        if "show_cta_footer" in site_index_builder_config:
            anonymized_site_index_builder[
                "show_cta_footer"
            ] = site_index_builder_config.get("show_cta_footer")
        anonymized_info_dict[
            "anonymized_site_index_builder"
        ] = anonymized_site_index_builder

        return anonymized_info_dict