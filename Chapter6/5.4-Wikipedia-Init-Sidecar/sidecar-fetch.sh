#!/bin/sh
# Sidecar container script to periodically fetch random Wikipedia pages

WWW_DIR="/usr/src/app/www"
RANDOM_URL="https://en.wikipedia.org/wiki/Special:Random"

# Function to get random number between min and max (in seconds)
get_random_seconds() {
    min=$1
    max=$2
    # Convert minutes to seconds
    min_sec=$((min * 60))
    max_sec=$((max * 60))
    range=$((max_sec - min_sec + 1))
    
    # Generate random number using /dev/urandom
    # Read random bytes and use modulo to get value in range
    if [ -c /dev/urandom ]; then
        # Use /dev/urandom if available
        random_val=$(od -An -N2 -tu2 /dev/urandom 2>/dev/null | tr -d ' ')
    else
        # Fallback: use current time
        random_val=$(date +%s)
    fi
    
    # Ensure we have a value
    if [ -z "$random_val" ]; then
        random_val=300  # Default to 5 minutes
    fi
    
    random_num=$((random_val % range + min_sec))
    echo $random_num
}

# Function to fetch random Wikipedia page
fetch_random_page() {
    echo "Sidecar: Fetching random Wikipedia page from ${RANDOM_URL}..."
    
    # Use curl with -L to follow redirects automatically
    # -s for silent, -o to save output
    curl -L -s "${RANDOM_URL}" -o "${WWW_DIR}/index.html"
    
    if [ $? -eq 0 ] && [ -s "${WWW_DIR}/index.html" ]; then
        echo "Sidecar: Successfully fetched and saved random Wikipedia page to ${WWW_DIR}/index.html"
        file_size=$(ls -lh "${WWW_DIR}/index.html" | awk '{print $5}')
        echo "Sidecar: File size: ${file_size}"
    else
        echo "Sidecar: Error fetching Wikipedia page or file is empty"
    fi
}

# Main loop
echo "Sidecar: Starting sidecar container..."
echo "Sidecar: Will wait 5-15 minutes between fetches"

while true; do
    # Wait for random time between 5 and 15 minutes
    wait_time=$(get_random_seconds 5 15)
    wait_minutes=$((wait_time / 60))
    
    echo "Sidecar: Waiting ${wait_minutes} minutes (${wait_time} seconds) before next fetch..."
    sleep "${wait_time}" || sleep 300  # Fallback to 5 minutes if sleep fails
    
    # Fetch random page (don't exit on error, keep running)
    fetch_random_page || echo "Sidecar: Fetch failed, will retry on next cycle"
done

