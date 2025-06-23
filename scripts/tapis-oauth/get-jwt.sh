#!/bin/bash

# Check if correct number of arguments provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 username password"
    echo ""
    echo "This script retrieves a JWT token from Tapis OAuth2 service."
    echo "The token will be printed to stdout for use in other scripts or applications."
    echo ""
    echo "Example:"
    echo "  $0 myuser mypassword"
    echo "  JWT_TOKEN=\$($0 myuser mypassword)"
    exit 1
fi

USERNAME=$1
PASSWORD=$2

# Get JWT token
echo "Getting JWT token for user: $USERNAME..." >&2

JWT=$(curl -s -H "Content-type: application/json" \
    -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\", \"grant_type\": \"password\" }" \
    https://portals.tapis.io/v3/oauth2/tokens | jq -r '.result.access_token.access_token')

if [ -z "$JWT" ] || [ "$JWT" = "null" ]; then
    echo "Failed to get JWT token. Please check your credentials." >&2
    exit 1
fi

# Print the JWT token to stdout (for use in other scripts)
echo "$JWT"