#!/bin/sh
# Init container script to fetch initial Wikipedia page

set -e

WWW_DIR="/usr/src/app/www"
WIKIPEDIA_URL="https://en.wikipedia.org/wiki/Kubernetes"

echo "Init container: Fetching Wikipedia page from ${WIKIPEDIA_URL}..."

# Create www directory if it doesn't exist
mkdir -p "${WWW_DIR}"

# Fetch the Wikipedia page and save as index.html
curl -L -s "${WIKIPEDIA_URL}" -o "${WWW_DIR}/index.html"

if [ $? -eq 0 ]; then
    echo "Init container: Successfully fetched and saved Wikipedia page to ${WWW_DIR}/index.html"
    ls -lh "${WWW_DIR}/index.html"
else
    echo "Init container: Error fetching Wikipedia page"
    exit 1
fi

