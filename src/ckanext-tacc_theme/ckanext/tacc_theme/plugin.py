import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from typing import (
    Any, Callable, Match, NoReturn, cast, Dict,
    Iterable, Optional, TypeVar, Union)
from markupsafe import Markup, escape
from markdown import markdown
import re

class TaccThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'tacc_theme')

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_dynamo_dashboard_url': self.get_dynamo_dashboard_url,
        }

    def get_dynamo_dashboard_url(self):
        """Get the DYNAMO Dashboard URL from CKAN configuration"""
        return toolkit.config.get('ckanext.tacc_theme.dynamo_dashboard_url', 'https://mint.tacc.utexas.edu')

    def markdown_extract_paragraphs(text: str, extract_length: int = 190) -> Union[str, Markup]:
        ''' return the plain text representation of markdown (ie: text without any html tags)
        as a list of paragraph strings.'''
        if not text:
            return ''

        # find all tags but ignore < in the strings so that we can use it correctly
        # in markdown
        RE_MD_HTML_TAGS = re.compile('<[^><]*>')
        plain = RE_MD_HTML_TAGS.sub('', markdown(text))
        return plain.splitlines()



