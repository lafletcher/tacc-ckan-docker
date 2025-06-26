"""
ckanext-tapisfilestore

CKAN extension for handling tapis:// protocol files
Similar to ckanext-s3filestore but for Tapis file system

File: ckanext/tapisfilestore/plugin.py
"""

import logging
import requests
import mimetypes
from urllib.parse import quote, unquote
from flask import Response, stream_with_context

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.common import config
import ckan.lib.helpers as h

log = logging.getLogger(__name__)


class TapisFilestorePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'tapisfilestore')

    # IBlueprint
    def get_blueprint(self):
        from flask import Blueprint
        blueprint = Blueprint('tapisfilestore', __name__)

        # Route for serving tapis files
        blueprint.add_url_rule(
            '/tapis-file/<path:file_path>',
            'serve_tapis_file',
            self.serve_tapis_file,
            methods=['GET']
        )

        return blueprint

    def _get_tapis_token(self):
        """
        Get Tapis OAuth2 token using the OAuth2 extension
        """
        # Method 1: Try the OAuth2 helper function
        try:
            token = h.oauth2_get_stored_token()
            if token:
                log.debug(f"Retrieved token via oauth2_get_stored_token: {type(token)}")
                # The token might be an object with access_token attribute
                if hasattr(token, 'access_token'):
                    return token.access_token
                # Or it might be the token string directly
                elif isinstance(token, str):
                    return token
                # Or it might be a dict
                elif isinstance(token, dict):
                    return token.get('access_token')
        except Exception as e:
            log.debug(f"oauth2_get_stored_token failed: {e}")

        # Method 2: Try toolkit.g.usertoken (set by OAuth2 plugin)
        try:
            if hasattr(toolkit.g, 'usertoken') and toolkit.g.usertoken:
                token = toolkit.g.usertoken
                log.debug(f"Retrieved token via toolkit.g.usertoken: {type(token)}")
                print(f"toolkit.g.usertoken: {token}")
                return token
        except Exception as e:
            log.debug(f"toolkit.g.usertoken failed: {e}")

        # Method 3: Try Flask g.usertoken
        try:
            if hasattr(g, 'usertoken') and g.usertoken:
                token = g.usertoken
                log.debug(f"Retrieved token via g.usertoken: {type(token)}")
                if hasattr(token, 'access_token'):
                    return token.access_token
                elif isinstance(token, str):
                    return token
                elif isinstance(token, dict):
                    return token.get('access_token')
        except Exception as e:
            log.debug(f"g.usertoken failed: {e}")

        # Method 4: Try session storage (fallback)
        try:
            for key in ['oauth2_token', 'tapis_token', 'access_token']:
                if key in session:
                    token = session[key]
                    if isinstance(token, dict):
                        return token.get('access_token')
                    elif isinstance(token, str):
                        return token
        except Exception as e:
            log.debug(f"Session token check failed: {e}")

        # Method 5: Try request headers
        try:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                return auth_header[7:]  # Remove 'Bearer ' prefix

            # Check for custom Tapis header
            tapis_token = request.headers.get('X-Tapis-Token', '')
            if tapis_token:
                return tapis_token
        except Exception as e:
            log.debug(f"Request headers check failed: {e}")

        return None
    def serve_tapis_file(self, file_path):
        """
        Serve a file from Tapis file system by proxying the request
        """
        try:
            # Get the user's Tapis token
            token = self._get_tapis_token()
            if not token or not token.access_token:
                return Response('Unauthorized: No Tapis token available', status=401)

            # Construct the Tapis API URL
            tapis_url = f"https://portals.tapis.io/v3/files/content/{file_path}"

            # Headers for the Tapis API request
            headers = {
                'x-tapis-token': token.access_token,
                'Accept': '*/*'
            }

            # Make the request to Tapis API
            response = requests.get(tapis_url, headers=headers, stream=True)

            if response.status_code != 200:
                log.error(f"Tapis API error: {response.status_code} for URL: {tapis_url}")
                return Response(
                    f'Error fetching file from Tapis: {response.status_code}',
                    status=response.status_code
                )

            # Determine content type
            content_type = response.headers.get('content-type')
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'

            # Get filename from path for Content-Disposition header
            filename = file_path.split('/')[-1]

            # Create response headers
            response_headers = {
                'Content-Type': content_type,
                'Content-Disposition': f'inline; filename="{filename}"'
            }

            # Add content length if available
            if 'content-length' in response.headers:
                response_headers['Content-Length'] = response.headers['content-length']

            # Stream the response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

            return Response(
                stream_with_context(generate()),
                headers=response_headers,
                status=200
            )

        except Exception as e:
            log.error(f"Error serving Tapis file {file_path}: {str(e)}")
            return Response('Internal server error', status=500)

    # IResourceController
    def before_show(self, resource_dict):
        """
        Modify resource URLs for tapis:// files before showing them
        """
        url = resource_dict.get('url', '')

        if url.startswith('tapis://'):
            # Extract the path after tapis://
            tapis_path = url[8:]  # Remove 'tapis://' prefix

            # Create the CKAN route URL for serving the file
            resource_dict['url'] = toolkit.url_for(
                'tapisfilestore.serve_tapis_file',
                file_path=tapis_path,
                _external=True
            )

            # Store the original tapis URL for reference
            resource_dict['tapis_original_url'] = url

        return resource_dict

    def after_create(self, context, resource):
        """Handle resource creation - for tapis files, just validate the URL format"""
        url = resource.get('url', '')
        if url.startswith('tapis://'):
            # Validate tapis URL format
            if len(url) <= 8 or not url[8:]:  # Must have content after 'tapis://'
                raise toolkit.ValidationError({'url': ['Invalid tapis:// URL format']})
        return resource

    def after_update(self, context, resource):
        """Handle resource updates - similar validation as create"""
        return self.after_create(context, resource)


def is_tapis_url(url):
    """Check if a URL is a tapis:// URL"""
    return url and url.startswith('tapis://')


def get_tapis_download_url(url):
    """Convert a tapis:// URL to a CKAN download URL"""
    if not is_tapis_url(url):
        return url

    tapis_path = url[8:]  # Remove 'tapis://' prefix
    return toolkit.url_for(
        'tapisfilestore.serve_tapis_file',
        file_path=tapis_path,
        _external=True
    )


def get_tapis_view_url(url):
    """Get view URL for tapis files (same as download for now)"""
    return get_tapis_download_url(url)


# Template helper functions
def tapis_helpers():
    return {
        'is_tapis_url': is_tapis_url,
        'get_tapis_download_url': get_tapis_download_url,
        'get_tapis_view_url': get_tapis_view_url,
    }


# Register template helpers
try:
    toolkit.add_template_directory(config, 'templates')
    h.is_tapis_url = is_tapis_url
    h.get_tapis_download_url = get_tapis_download_url
    h.get_tapis_view_url = get_tapis_view_url
except:
    pass  # Helpers will be registered when plugin loads


