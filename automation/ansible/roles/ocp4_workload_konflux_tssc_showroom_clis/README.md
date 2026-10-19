# ocp4_workload_konflux_tssc_showroom_clis

Patches the Showroom deployment to install TAS CLIs (cosign, ec, rekor-cli) in the terminal container.

## Purpose

This role must run **after** the Showroom workload has deployed. It patches the Showroom deployment to add:
- An initContainer that downloads CLIs from the TAS CLI server
- An emptyDir volume to store the CLIs
- Volume mounts and PATH updates to make CLIs available in the terminal

## CLIs Installed

The following CLIs are downloaded from the TAS CLI server and installed to `/opt/bin`:

1. **cosign** - Sigstore signing and verification tool
2. **ec** - Enterprise Contract policy validation CLI
3. **rekor-cli** - Rekor transparency log client

Source: `http://cli-server.trusted-artifact-signer.svc.cluster.local:8080/clients/linux/`

## Requirements

- Showroom deployment must exist in `{user}-showroom` namespace
- TAS CLI server must be running in `trusted-artifact-signer` namespace
- Showroom must be using a deployment named `showroom` with a `terminal` container

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ocp4_workload_konflux_tssc_showroom_clis_showroom_namespace` | `user-{{ guid }}-showroom` | Namespace containing the Showroom deployment |

## Usage in AgnosticV Catalog

Add this role to your workload list **after** the showroom workload:

```yaml
workloads:
  # ... other workloads
  - konflux_tssc.ocp4_workload_showroom  # Showroom must run first
  - konflux_tssc.ocp4_workload_konflux_tssc_showroom_clis  # Then install CLIs
```

## What It Does

1. Waits for Showroom deployment to exist
2. Patches the deployment with:
   - `initContainer` using `ubi9/ubi` image (has gunzip pre-installed)
   - Downloads and extracts .gz CLIs from TAS CLI server
   - `emptyDir` volume for CLI storage
   - Volume mounts for the terminal container
   - PATH environment variable update to include `/opt/bin`
3. Waits for deployment to become ready after patching

## Persistence Behavior

- CLIs are stored in an `emptyDir` volume
- **Not persistent** across pod deletions
- **Auto-reinstalled** via initContainer on every pod start
- Download time: ~5-10 seconds per pod start

## Troubleshooting

### CLIs not available in terminal
```bash
# Check if initContainer ran successfully
oc logs -n {user}-showroom deployment/showroom -c install-tas-clis

# Check if volume is mounted
oc describe pod -n {user}-showroom -l app=showroom
```

### InitContainer fails to download
```bash
# Verify TAS CLI server is running
oc get svc -n trusted-artifact-signer cli-server

# Check network connectivity from Showroom namespace
oc run -n {user}-showroom test-curl --image=curlimages/curl --rm -it -- \
  curl -I http://cli-server.trusted-artifact-signer.svc.cluster.local:8080/clients/linux/cosign-amd64.gz
```

## Notes

- This role uses strategic merge patch to add initContainer and volumes
- Multiple runs are idempotent
- The patch triggers a new rollout of the Showroom deployment
