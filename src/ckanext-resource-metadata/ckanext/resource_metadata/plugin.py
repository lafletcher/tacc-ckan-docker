# ckanext-resource-metadata/ckanext/resource_metadata/plugin.py

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.logic import validators as validators
from ckan.lib.navl.validators import ignore_missing, not_empty
import json

class ResourceMetadataPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'resource_metadata')

    # IResourceController
    def before_create(self, context, resource):
        # Ensure metadata is stored as a JSON string if it exists
        if 'metadata' in resource and isinstance(resource['metadata'], dict):
            resource['metadata'] = json.dumps(resource['metadata'])
        return resource

    def before_update(self, context, current, resource):
        # Ensure metadata is stored as a JSON string if it exists
        if 'metadata' in resource and isinstance(resource['metadata'], dict):
            resource['metadata'] = json.dumps(resource['metadata'])
        return resource

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'resource_metadata_parse_json': self._parse_json,
            'resource_metadata_fields': self._get_metadata_fields
        }

    def _parse_json(self, metadata_str):
        """Parse JSON string to Python dict"""
        if not metadata_str:
            return {}
        try:
            return json.loads(metadata_str)
        except (ValueError, TypeError):
            return {}

    def _get_metadata_fields(self):
        """Return the configured metadata fields"""
        # You can make this configurable via a CKAN config option
        default_fields = [
            {'name': 'format_version', 'label': 'Format Version'},
            {'name': 'created_by', 'label': 'Created By'},
            {'name': 'last_modified_by', 'label': 'Last Modified By'},
            {'name': 'temporal_coverage_start', 'label': 'Temporal Coverage Start'},
            {'name': 'temporal_coverage_end', 'label': 'Temporal Coverage End'},
            {'name': 'update_frequency', 'label': 'Update Frequency'},
            {'name': 'source_url', 'label': 'Source URL'},
            {'name': 'methodology', 'label': 'Methodology'},
            {'name': 'data_quality', 'label': 'Data Quality'},
            {'name': 'schema', 'label': 'Schema Description'}
        ]

        # Get custom fields from configuration if they exist
        custom_fields_str = toolkit.config.get('ckanext.resource_metadata.fields', '')
        if custom_fields_str:
            try:
                custom_fields = json.loads(custom_fields_str)
                return custom_fields
            except (ValueError, TypeError):
                pass

        return default_fields

