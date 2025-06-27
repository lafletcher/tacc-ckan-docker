[![Tests](https://github.com/mosoriob/ckanext-tapisfilestore/workflows/Tests/badge.svg?branch=main)](https://github.com/mosoriob/ckanext-tapisfilestore/actions)

# ckanext-tapisfilestore

A CKAN extension that enables serving files from the Tapis file system through CKAN resources. This extension handles `tapis://` protocol URLs by proxying requests to the Tapis API, allowing CKAN to serve files stored in Tapis file systems as if they were local resources.

## Overview

The Tapis Filestore extension integrates CKAN with the Tapis file system, enabling:

- **Seamless file serving**: Serve files from Tapis file systems through CKAN's resource interface
- **OAuth2 integration**: Automatic authentication using Tapis OAuth2 tokens
- **Streaming support**: Efficient streaming of large files without loading them entirely into memory
- **MIME type detection**: Automatic content-type detection for proper file handling
- **Error handling**: User-friendly error messages for authentication and access issues

## Features

- **Protocol Support**: Handles `tapis://` URLs in CKAN resources
- **Authentication**: Integrates with Tapis OAuth2 authentication system
- **File Streaming**: Streams file content for efficient memory usage
- **MIME Type Detection**: Automatically detects and sets appropriate content types
- **Error Handling**: Provides clear error messages for common issues (404, 401, 403)
- **Template Helpers**: Provides helper functions for templates to work with Tapis URLs

## Requirements

### CKAN Compatibility

| CKAN version    | Compatible? |
| --------------- | ----------- |
| 2.9+            | yes         |
| 2.8             | not tested  |
| 2.7             | not tested  |
| 2.6 and earlier | not tested  |

### Dependencies

- CKAN 2.9 or higher
- Python 3.7+
- `requests` library
- Tapis OAuth2 extension (for authentication)

## Installation

### 1. Activate your CKAN virtual environment

```bash
. /usr/lib/ckan/default/bin/activate
```

### 2. Install the extension

```bash
git clone https://github.com/mosoriob/ckanext-tapisfilestore.git
cd ckanext-tapisfilestore
pip install -e .
pip install -r requirements.txt
```

### 3. Configure CKAN

Add `tapisfilestore` to the `ckan.plugins` setting in your CKAN config file (typically `/etc/ckan/default/ckan.ini`):

```ini
ckan.plugins = ... tapisfilestore
```

### 4. Restart CKAN

```bash
sudo service apache2 reload
```

## Configuration

### Required Configuration

The extension requires integration with the Tapis OAuth2 system for authentication. Ensure you have:

1. **Tapis OAuth2 Extension**: Install and configure `ckanext-oauth2` for Tapis authentication
2. **Tapis API Access**: Valid Tapis tenant and API credentials

### Optional Configuration

Currently, the extension uses default Tapis API endpoints. If you need to customize these, you can modify the plugin code:

- **Files API Base URL**: `https://portals.tapis.io/v3/files/`
- **File Info Endpoint**: `/ops/{file_path}`
- **File Content Endpoint**: `/content/{file_path}`

## Usage

### Adding Tapis Resources

1. **Create a Dataset**: Create a new dataset in CKAN
2. **Add Resource**: Add a resource with a `tapis://` URL
3. **Automatic Processing**: The extension automatically converts the URL to a CKAN-served URL

### URL Format

Tapis URLs should follow this format:

```
tapis://path/to/file
```

Examples:

- `tapis://user/data/sample.csv`
- `tapis://shared/datasets/analysis.pdf`
- `tapis://project/results/output.txt`

### Template Helpers

The extension provides several template helper functions:

```python
# Check if a URL is a Tapis URL
h.is_tapis_url(url)

# Get the CKAN download URL for a Tapis file
h.get_tapis_download_url(url)

# Get the view URL for a Tapis file
h.get_tapis_view_url(url)
```

## How It Works

### 1. URL Processing

When a resource with a `tapis://` URL is displayed:

1. The `before_show` method intercepts the resource
2. Converts `tapis://path/to/file` to `/tapis-file/path/to/file`
3. The converted URL points to the extension's file serving endpoint

### 2. Authentication

The extension retrieves Tapis authentication tokens through multiple methods:

1. **OAuth2 Helper**: Uses `h.oauth2_get_stored_token()`
2. **Global Token**: Checks `toolkit.g.usertoken`
3. **Request Headers**: Looks for `Authorization: Bearer` or `X-Tapis-Token` headers

### 3. File Serving

When a file is requested:

1. **Token Validation**: Ensures a valid Tapis token is available
2. **File Info**: Retrieves file metadata (MIME type, size, etc.)
3. **Content Streaming**: Streams file content with appropriate headers
4. **Error Handling**: Provides user-friendly error messages

### 4. Error Handling

The extension handles common Tapis API errors:

- **404 Not Found**: File doesn't exist in Tapis
- **401 Unauthorized**: No valid authentication token
- **403 Forbidden**: User lacks permission to access the file

## API Endpoints

### File Serving Endpoint

```
GET /tapis-file/<path:file_path>
```

Serves files from the Tapis file system. The `file_path` parameter should be the path within the Tapis file system.

**Headers:**

- `Authorization: Bearer <token>` (optional)
- `X-Tapis-Token: <token>` (optional)

**Response:**

- **200 OK**: File content with appropriate MIME type
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: File not found

## Development

### Developer Installation

```bash
git clone https://github.com/mosoriob/ckanext-tapisfilestore.git
cd ckanext-tapisfilestore
python setup.py develop
pip install -r dev-requirements.txt
```

### Running Tests

```bash
pytest --ckan-ini=test.ini
```

### Project Structure

```
ckanext-tapisfilestore/
├── ckanext/
│   └── tapisfilestore/
│       ├── __init__.py
│       ├── plugin.py          # Main plugin implementation
│       ├── templates/         # Template overrides
│       ├── public/           # Static assets
│       └── tests/            # Test files
├── setup.py                  # Package configuration
├── requirements.txt          # Runtime dependencies
├── dev-requirements.txt      # Development dependencies
└── README.md                # This file
```

## Troubleshooting

### Common Issues

1. **"No Tapis token found"**

   - Ensure the Tapis OAuth2 extension is properly configured
   - Check that users are authenticated with Tapis

2. **"File not found"**

   - Verify the file path in the `tapis://` URL
   - Ensure the file exists in the Tapis file system

3. **"Access denied"**
   - Check user permissions in Tapis
   - Verify the file is accessible to the authenticated user

### Debugging

Enable debug logging in your CKAN configuration:

```ini
[logger_ckanext.tapisfilestore]
level = DEBUG
handlers = console
qualname = ckanext.tapisfilestore
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review the CKAN documentation
3. Open an issue on the GitHub repository
4. Contact the development team

## Changelog

### Version 0.0.1

- Initial release
- Basic Tapis file serving functionality
- OAuth2 integration
- Streaming support
- Error handling
