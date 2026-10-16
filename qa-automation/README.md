# Konflux TSSC Lab — QA Automation

This directory contains automated testing playbooks for the Konflux TSSC Lab.

## Structure

```
qa-automation/
├── healthcheck.yml       # Tenant environment readiness validation (runs at provision time)
├── e2e.yml               # Orchestrator that runs all module e2e tests in sequence
├── e2e-module-02.yml     # Module 2: Onboard Your Application
├── e2e-module-03.yml     # Module 3: Build and Scan
├── e2e-module-04.yml     # Module 4: Signing and Provenance
├── e2e-module-05.yml     # Module 5: Integration Testing and Policy
├── e2e-module-06.yml     # Module 6: Release to Production
└── README.md             # This file
```

## Healthcheck vs E2E Tests

| Aspect | Healthcheck | E2E Tests |
|--------|-------------|-----------|
| **When** | At tenant provision time | After deployment / on-demand |
| **Purpose** | Validate environment is ready for students | Validate complete student workflows work |
| **Scope** | Infrastructure: namespaces, routes, GitLab repos, Quay orgs, RBAC | Application: create app, build, sign, verify, release |
| **Duration** | ~2 minutes | ~60-90 minutes (full suite) |
| **Failure** | Blocks student access | Indicates lab content or platform issue |

## E2E Test Coverage

### Module 2: Onboard Your Application
**What it tests:**
- Create Konflux Application via k8s API
- Create GitLab Personal Access Token via GitLab API
- Create `pipelines-as-code-secret`
- Create Konflux Component
- Verify MR opened by Konflux
- Verify first `on-pull-request` PipelineRun succeeds
- Verify image pushed to Quay

**Student actions automated:**
- UI form → k8s API (`Application`, `Component` CRs)
- GitLab PAT creation → GitLab API with root token
- All verification steps

**Duration:** ~15-20 minutes (first build takes longest)

---

### Module 3: Build and Scan
**What it tests:**
- Push commit to MR branch via GitLab API
- Verify `on-pull-request` PipelineRun triggered
- Merge MR via GitLab API
- Verify `on-push` PipelineRun triggered (merged MR build)
- Extract `IMAGE_DIGEST` from PipelineRun results
- Download and verify SBOM via `cosign download sbom`
- Verify image in Quay with `on-push-*` tag

**Student actions automated:**
- GitLab UI editing → GitLab commits API
- GitLab MR merge → GitLab API
- All `cosign` and `skopeo` commands

**Duration:** ~20-25 minutes (two full builds)

---

### Module 4: Signing and Provenance
**What it tests:**
- Initialize `cosign` with TAS TUF root
- Verify image signature with `cosign verify`
- Download SLSA provenance attestation
- Verify attestation contains correct repo/commit/builder
- Verify Rekor transparency log entry exists

**Student actions automated:**
- All CLI operations (100% scriptable already)

**Duration:** ~2-3 minutes (no builds, just verification)

---

### Module 5: Integration Testing and Policy
**What it tests:**
- Retrieve `EnterpriseContractPolicy` from cluster
- Run `ec validate image` against merged MR build
- Verify Snapshot created with passing status
- Verify `IntegrationTestScenario` exists and ran
- Verify Snapshot `AppStudioIntegrationStatus` condition = `True`
- Test policy failure with unsigned image (expect `success: false`)

**Student actions automated:**
- All CLI operations (100% scriptable)

**Duration:** ~2-3 minutes (validation only)

---

### Module 6: Release to Production
**What it tests:**
- Create `ReleasePlanAdmission` in managed namespace
- Create `ReleasePlan` in tenant namespace
- Create `Release` CR to trigger release
- Wait for tenant pipeline to complete
- Wait for managed pipeline to complete
- Verify production image in Quay with `production` tag
- Verify production digest matches merged MR digest (no rebuild)
- Verify signature on production image
- Verify attestations on production image

**Student actions automated:**
- UI forms → k8s API (`ReleasePlan`, `Release` CRs)
- All verification via `oc`, `skopeo`, `cosign`

**Duration:** ~5-7 minutes (release pipeline execution)

---

### Module 7: Real-World Incident Response
**Not automated** — intentionally manual. Students break the supply chain and diagnose failures hands-on.

---

## Usage

### Run Full E2E Suite
```bash
ansible-playbook qa-automation/e2e.yml \
  -e "ocp_api_url=https://api.cluster-xyz.example.com:6443" \
  -e "ocp_admin_password=admin-password" \
  -e "tenant_user=user-abc12"
```

**Total runtime:** ~60-90 minutes

---

### Run Single Module
```bash
ansible-playbook qa-automation/e2e-module-03.yml \
  -e "ocp_api_url=https://api.cluster-xyz.example.com:6443" \
  -e "ocp_admin_password=admin-password" \
  -e "tenant_user=user-abc12"
```

**Note:** Module 3-6 depend on earlier modules. Running Module 6 alone will fail if Module 2-5 artifacts don't exist.

---

### Run from Showroom Runner Pod
When running inside the Showroom runner pod (e.g., via Showroom API healthcheck/e2e triggers):

```bash
ansible-playbook qa-automation/e2e.yml
```

Variables are auto-populated from `user_data.yml`:
- `openshift_api_url` → cluster API
- `user` → tenant username
- Auth via `runtime-automation` ServiceAccount token

---

## Authentication

Each playbook supports **dual authentication**:

### 1. CLI Mode (oc login)
```yaml
ocp_api_url: https://api.cluster-xyz.example.com:6443
ocp_admin_password: admin-password
tenant_user: user-abc12
```

Uses `oc login` with admin credentials.

### 2. Showroom Runner Mode (ServiceAccount)
```yaml
openshift_api_url: https://api.cluster-xyz.example.com:6443  # from user_data.yml
user: user-abc12                                              # from user_data.yml
```

Reads `runtime-automation` SA token from `{user}-showroom` namespace.

---

## Error Handling Pattern

All e2e playbooks follow the **dev-day-roadshow pattern**:

```yaml
e2e_failures: []  # Track all failures

# Each task uses ignore_errors: true
- name: Some operation
  ...
  register: r_result
  ignore_errors: true

# Then conditionally records failures
- name: Record failure
  ansible.builtin.set_fact:
    e2e_failures: "{{ e2e_failures + ['Failure description'] }}"
  when: r_result is failed

# Summary at end
- name: Summary
  ansible.builtin.debug:
    msg: |
      Results:
      - Check 1: {{ 'Yes' if condition else 'No' }}
      - Failures: {{ e2e_failures | length }}

# Fail only at the end
- name: Fail if any checks failed
  ansible.builtin.fail:
    msg: "{{ e2e_failures }}"
  when: e2e_failures | length > 0
```

**Why?**
- Runs all checks even if one fails
- Comprehensive failure report at the end
- Easy to identify which step failed

---

## Dependencies

### Required Cluster Resources
E2E tests expect these to exist (created by provisioning automation):

**Cluster-wide:**
- `gitlab` namespace with GitLab instance
- `quay-enterprise` namespace with Quay instance
- `tsf-tas` namespace with Trusted Artifact Signer
- `tsf-keycloak` namespace with OIDC issuer
- `enterprise-contract-service` namespace with `lab-policy` EnterpriseContractPolicy
- `konflux-operator` namespace with integration-test-patcher deployment

**Per-tenant:**
- `{user}-tenant` namespace
- `{user}-managed` namespace
- `{user}-showroom` namespace with `runtime-automation` ServiceAccount
- GitLab repository: `{user}/sample-component-golang`
- Quay organization: `tsf` with user as member

### Required Secrets
- `gitlab/root-user-personal-token` — GitLab root PAT for API operations
- `quay-enterprise/quay-admin-token` — Quay admin token (optional, used by healthcheck)
- `{user}-showroom/runtime-automation-token` — ServiceAccount token for Showroom runner mode

### Required CLI Tools
- `oc` — OpenShift CLI
- `cosign` — Sigstore signature verification
- `skopeo` — Container image inspection
- `ec` — Enterprise Contract CLI
- `jq` — JSON processing

All tools are pre-installed in the Showroom runner pod.

---

## Limitations & Known Issues

### 1. GitLab PAT Creation
**Student:** Creates PAT via GitLab UI  
**E2E:** Uses GitLab API with root token to create PAT for tenant user

**Caveat:** Requires GitLab root token in `gitlab/root-user-personal-token` secret.

### 2. PipelineRun Wait Times
First builds can take **12-15 minutes**. E2E tests set:
- `retries: 90`
- `delay: 20` (20 seconds between checks)
- Max wait: **30 minutes**

If builds timeout, check:
- Worker node capacity
- Pipeline image pull limits
- Build task resource requests

### 3. Release Pipeline Timing
Release pipeline has **two stages**:
1. Tenant pipeline (~30 seconds)
2. Managed pipeline (~2-3 minutes)

E2E waits for `Released` condition on the `Release` CR (60 retries × 10 seconds = 10 minutes max).

### 4. Unsigned Image for Policy Failure Test
Module 5 tests policy failure using:
```
{quay_url}/lab-examples/unsigned-sample:latest
```

This image must be pre-pushed to the `lab-examples` organization in Quay.

**To create it:**
```bash
podman pull registry.access.redhat.com/ubi9/ubi-minimal:latest
podman tag ubi9/ubi-minimal:latest {quay_url}/lab-examples/unsigned-sample:latest
podman push {quay_url}/lab-examples/unsigned-sample:latest --tls-verify=false
```

---

## Troubleshooting

### E2E Test Fails: "No PipelineRun created"
**Cause:** Pipelines-as-Code webhook not firing  
**Check:**
- Is `pipelines-as-code-secret` created in tenant namespace?
- Does GitLab PAT have `api` scope?
- Is `.tekton/` directory in GitLab repo?

### E2E Test Fails: "Snapshot does not have passing AppStudioIntegrationStatus"
**Cause:** Integration pipeline failed or hasn't run yet  
**Check:**
```bash
oc get snapshot -n {user}-tenant
oc get pipelinerun -n {user}-tenant | grep enterprise-contract
```

### E2E Test Fails: "Release did not complete successfully"
**Cause:** Managed pipeline failed (usually EC policy violation)  
**Check:**
```bash
oc get release -n {user}-tenant
oc get pipelinerun -n {user}-managed
```

### Cosign Fails: "certificate identity mismatch"
**Cause:** OIDC issuer URL changed  
**Check:**
```bash
oc get cm public-info -n tsf-keycloak -o jsonpath='{.data.OIDC_ISSUER_URL}'
```

Update e2e playbook if issuer changed.

---

## Integration with Showroom API

### Healthcheck Hook
Showroom automatically runs healthcheck at provision time:
```yaml
# In showroom deployment
healthcheck:
  playbook: qa-automation/healthcheck.yml
```

### E2E Hook (Optional)
To run e2e after provisioning:
```yaml
# In showroom deployment
post_provision:
  playbook: qa-automation/e2e.yml
```

**Warning:** E2E suite takes 60-90 minutes. Only use for CI/validation environments, not student-facing deploys.

---

## Contributing

### Adding a New Module E2E Test

1. Create `qa-automation/e2e-module-XX.yml`
2. Follow the dual-auth pattern (see existing playbooks)
3. Use error collection pattern (`e2e_failures` list)
4. Add summary output at the end
5. Update `qa-automation/e2e.yml` to import the new playbook
6. Update this README with module description

### Pattern Template
```yaml
---
- name: "E2E Module X: Title"
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    _api_url: "{{ ocp_api_url | default(openshift_api_url) }}"
    _tenant_user: "{{ tenant_user | default(user) }}"
    _use_sa_token: "{{ ocp_admin_password is not defined }}"
    e2e_failures: []

  tasks:
    # Auth setup (copy from existing modules)
    # Pre-conditions
    # Test steps (with error collection)
    # Summary
    # Fail if e2e_failures | length > 0
```

---

## References

- **Konflux TSSC Lab Content:** [content/modules/ROOT/pages/](../content/modules/ROOT/pages/)
- **Dev-Day-Roadshow E2E Pattern:** https://github.com/rhpds/dev-day-roadshow/tree/main/qa-automation
- **Enterprise Contract CLI:** https://github.com/enterprise-contract/ec-cli
- **Sigstore cosign:** https://docs.sigstore.dev/cosign/overview/

---

**Last Updated:** 2025-01-16  
**Maintainer:** Tyrell Reddy (treddy@redhat.com)
