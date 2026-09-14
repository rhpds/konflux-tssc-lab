#!/bin/bash
set -e

BUNDLE_URL="quay.io/rhpds/pipeline-docker-build-lab:1.0"
PIPELINE_FILE="bundle-content/docker-build-oci-ta-min.yaml"

echo "Fixing pipeline task references to use bundle resolver..."

# Backup original
cp "${PIPELINE_FILE}" "${PIPELINE_FILE}.bak"

# Use jq to update all taskRef entries to use bundle resolver
jq --arg bundle "${BUNDLE_URL}" '
  .spec.tasks |= map(
    .taskRef = {
      "resolver": "bundles",
      "params": [
        {"name": "bundle", "value": $bundle},
        {"name": "name", "value": .taskRef.name},
        {"name": "kind", "value": "task"}
      ]
    }
  )
' "${PIPELINE_FILE}" > "${PIPELINE_FILE}.tmp"

mv "${PIPELINE_FILE}.tmp" "${PIPELINE_FILE}"

echo "✅ Pipeline task references updated to use bundle resolver"
echo "  Bundle: ${BUNDLE_URL}"
