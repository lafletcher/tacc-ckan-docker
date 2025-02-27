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

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'tacc_theme')

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



