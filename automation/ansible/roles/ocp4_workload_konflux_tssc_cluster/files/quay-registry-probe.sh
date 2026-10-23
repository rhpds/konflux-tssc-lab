#!/usr/bin/env bash
# Run inside tsf-cli: validate the alias without sending registry credentials.
set -eu
url=${1:?registry API URL required}
attempts=${2:-12}
delay=${3:-5}
headers=$(mktemp)
trap 'rm -f "$headers"' EXIT

for ((attempt=1; attempt<=attempts; attempt++)); do
    rc=0
    # Do not follow redirects or print response bodies, cookies or auth challenges.
    status=$(curl --silent --insecure --connect-timeout 5 --max-time 10 \
        --dump-header "$headers" --output /dev/null --write-out '%{http_code}' \
        "$url") || rc=$?
    registry_api=false
    redirect=false
    if grep -Eiq '^Docker-Distribution-Api-Version:[[:space:]]*registry/2\.0[[:space:]]*$' "$headers"; then
        registry_api=true
    fi
    if grep -Eiq '^Location:' "$headers"; then
        redirect=true
    fi
    printf 'attempt=%s curl_exit=%s http_status=%s registry_api=%s redirect=%s\n' \
        "$attempt" "$rc" "$status" "$registry_api" "$redirect"
    if [[ "$rc" == 0 && "$registry_api" == true && ( "$status" == 200 || "$status" == 401 ) ]]; then
        exit 0
    fi
    # Retry only connection-level failures and temporary gateway/unavailable responses.
    case "$rc:$status" in
        6:*|7:*|28:*|52:*|56:*|0:502|0:503|0:504) ;;
        *) exit 1 ;;
    esac
    if ((attempt < attempts)); then
        sleep "$delay"
    fi
done
exit 1
