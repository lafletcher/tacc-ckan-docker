# Docker Compose setup for CKAN

📊 **Architecture**: See the [CKAN Architecture Diagram](architecture-diagram.md) for a visual overview of the system components and their relationships.

## Configuration Management

The project uses separate files for configuration and secrets to ensure better security and version control:

### Development Environment

- `.env.dev.config`: Development configuration values (committed to git)
- `.env.dev.secrets`: Development secrets and sensitive data (not committed)

### Production Environment

- `.env.config`: Production configuration values (committed to git)
- `.env.secrets`: Production secrets and sensitive data (not committed)

### Setup Instructions

1. For Development:

```bash
# Copy the development secrets template and edit with your values
cp .env.secrets.example .env.dev.secrets
```

2. For Production:

```bash
# Copy the production secrets template and edit with your values
cp .env.secrets.example .env.prod.secrets
```

> [!IMPORTANT]
> Never commit secrets files to git. They are automatically ignored via `.gitignore`.

### Running the Application

> **Note:** The default CKAN URL is `http://localhost:5000`.
> If you change this URL, you must also update the following environment variables accordingly:
>
> - `CKAN_SITE_URL` (e.g., `CKAN_SITE_URL=http://localhost:5000`)
> - `CKAN_OAUTH2_CLIENT_ID`
> - `CKAN_OAUTH2_CLIENT_SECRET`

> **Tip:** If you cannot use `localhost:5000` (for example, due to browser or network restrictions), you can use a custom hostname such as `ckan.tacc.cloud`.
> To do this, add the following line to your `/etc/hosts` file:
>
> ```
> 127.0.0.1   ckan.tacc.cloud
> ```
>
> Then, access CKAN at `http://ckan.tacc.cloud:5000`.
> **Remember:** If you use a custom hostname, you must also update the following environment variables to match:
>
> - `CKAN_SITE_URL=http://ckan.tacc.cloud:5000`

> See [OAuth2 Client Setup](#oauth2-client-setup) at the end of this document for instructions on creating an OAuth2 client for your CKAN instance.

> For development:

```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d
```

For production:

```bash
docker compose build
docker compose up -d
```

## Development mode

To run CKAN in development mode, use the `docker-compose.dev.yml` file.

Build the images and run the containers:

```bash
docker compose -f docker-compose.dev.yml  build
```

Run the CKAN development server:

```bash
docker compose -f docker-compose.dev.yml  up -d
```

To edit the theme, you can edit the files in the `src/ckanext-tacc_theme` directory.

## Install (build and run) CKAN plus dependencies

### Base mode

Use this if you are a maintainer and will not be making code changes to CKAN or to CKAN extensions

Copy the included `.env.example` and rename it to `.env`. Modify it depending on your own needs.

> [!WARNING]
> There is a sysadmin user created by default with the values defined in `CKAN_SYSADMIN_NAME` and `CKAN_SYSADMIN_PASSWORD` in your `.env.secrets` file. These must be changed before running this setup as a public CKAN instance.

To build the images:

    docker compose build

To start the containers:

    docker compose up

This will start up the containers in the current window. By default the containers will log direct to this window with each container
using a different colour. You could also use the -d "detach mode" option ie: `docker compose up -d` if you wished to use the current
window for something else.

At the end of the container start sequence there should be 6 containers running:

```bash
$ docker compose ps
NAME                       IMAGE                              COMMAND                  SERVICE      CREATED         STATUS                   PORTS
ckan-docker-ckan-1         ckan-docker-ckan                   "/srv/app/start_ckan…"   ckan         4 minutes ago   Up 3 minutes (healthy)   5000/tcp
ckan-docker-datapusher-1   ckan/ckan-base-datapusher:0.0.20   "sh -c 'uwsgi --plug…"   datapusher   4 minutes ago   Up 4 minutes (healthy)   8800/tcp
ckan-docker-db-1           ckan-docker-db                     "docker-entrypoint.s…"   db           4 minutes ago   Up 4 minutes (healthy)
ckan-docker-nginx-1        ckan-docker-nginx                  "/bin/sh -c 'openssl…"   nginx        4 minutes ago   Up 2 minutes             80/tcp, 0.0.0.0:8443->443/tcp
ckan-docker-redis-1        redis:6                            "docker-entrypoint.s…"   redis        4 minutes ago   Up 4 minutes (healthy)
ckan-docker-solr-1         ckan/ckan-solr:2.10-solr9          "docker-entrypoint.s…"   solr         4 minutes ago   Up 4 minutes (healthy)
```

After this step, CKAN should be running at `CKAN_SITE_URL` (by default https://localhost:8443)

### Manage users

To manage users, you can use the [CKAN API](https://docs.ckan.org/en/2.9/api/index.html).

```bash
ckan sysadmin add john_doe
```

### Filesystem permissions

The CKAN data is stored in the `ckan_storage` volume. The `ckan` user needs to have write access to this volume.

The ckan user is created with the `ckan` group.

```bash
docker-compose exec  ckan bash
ckan@dbdd4ea66995:~$ id
uid=503(ckan) gid=502(ckan-sys) groups=502(ckan-sys)
```

Set the correct permissions for the ckan user:

```bash
sudo chown -R 503:502 ckan_storage
```

## API Authentication

CKAN uses Tapis OAuth2 for authentication. The Tapis OAuth2 service is configured to use the Tapis OAuth2 service at `https://portals.tapis.io/v3/oauth2/tokens`.

To get a JWT token, you can use the `scripts/tapis-oauth/get-jwt.sh` script.

```bash
JWT=$(./scripts/tapis-oauth/get-jwt.sh myuser mypassword)
```

You can then use the JWT token to authenticate your requests to the CKAN API.

```
curl --location 'https://ckan.tacc.utexas.edu/api/action/package_create' \
--header 'Content-Type: application/json' \
--header "Authorization: Bearer $JWT" \
--data '{
  "name": "my-dataset-name",
  "title": "My Dataset Title",
  "notes": "A description of the dataset",
  "owner_org": "org",
  "private": false,
  "tags": [
    {"name": "tag1"},
    {"name": "tag2"}
  ]
}'
```

## Tapis File System Integration

This CKAN instance includes integration with the Tapis file system through the `ckanext-tapisfilestore` extension. This allows CKAN to serve files stored in Tapis file systems seamlessly.

### Features

- **Tapis URL Support**: Handle `tapis://` protocol URLs in CKAN resources
- **OAuth2 Authentication**: Automatic authentication using Tapis OAuth2 tokens
- **File Streaming**: Efficient streaming of large files without loading them into memory
- **MIME Type Detection**: Automatic content-type detection for proper file handling

### Using Tapis Files

When creating or editing a resource in CKAN, you can use Tapis URLs in the following format:

```
tapis://path/to/file
```

Examples:
- `tapis://user/data/sample.csv`
- `tapis://shared/datasets/analysis.pdf`
- `tapis://project/results/output.txt`

The extension automatically converts these URLs to CKAN-served URLs that authenticate with Tapis and stream the file content.

### Requirements

- Users must be authenticated with Tapis OAuth2
- Files must exist in the Tapis file system
- Users must have appropriate permissions to access the files

For more details about the Tapis integration, see the documentation in `src/ckanext-tapisfilestore/README.md`.

## OAuth2 Client Setup

You can use the `create-client.sh` script to create an OAuth2 client for your CKAN instance. Run the following command, replacing the placeholders with your actual values:

```bash
bash -x scripts/tapis-oauth/create-client.sh tacc_username tacc_password client-name http://your_hostname:5000/oauth2/callback
```

For example, if your hostname is `ckan.tacc.cloud`, use:

```bash
bash -x scripts/tapis-oauth/create-client.sh tacc_username tacc_password ckan-tacc-cloud http://ckan.tacc.cloud:5000/oauth2/callback
```

---

### Adding a User as Sysadmin

After authenticating with OAuth2, you may need to grant sysadmin privileges to your user. You can do this using the CKAN CLI inside the running CKAN container:

Production:

```bash
docker compose exec ckan ckan sysadmin add <your-username>
```

Development:

```bash
docker compose -f docker-compose.dev.yml exec ckan-dev ckan sysadmin add <your-username>
```

Replace `<your-username>` with the username you used for OAuth2 authentication.
