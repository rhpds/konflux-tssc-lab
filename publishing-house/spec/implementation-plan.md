# Konflux TSSC Lab - Implementation Plan

**Project**: Build, Sign, and Ship: Securing the Software Supply Chain with Konflux  
**Based on**: LB1353 implementation (rh1-2027/lb1353-konflux-tsf-tssc-cnv-*)  
**Date**: 2026-09-03  
**Author**: Tyrell Reddy

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Requirements Analysis](#module-requirements-analysis)
3. [Infrastructure Components](#infrastructure-components)
4. [Implementation Phases](#implementation-phases)
5. [Cluster Workload Implementation](#cluster-workload-implementation)
6. [Tenant Workload Implementation](#tenant-workload-implementation)
7. [Sample Application Requirements](#sample-application-requirements)
8. [Testing Strategy](#testing-strategy)
9. [References](#references)

---

## Architecture Overview

### Deployment Model
- **Topology**: Shared cluster, multi-tenant
- **Per-user resources**: Two namespaces, GitLab repo, Quay account, Konflux workspace
- **Cluster-wide services**: Konflux, RHTAS, GitLab, Quay, Keycloak

### Component Stack

```
┌─────────────────────────────────────────────────────────────────┐
│ Cluster-Level (Once per cluster)                                │
├─────────────────────────────────────────────────────────────────┤
│ • S4 Object Storage (MinIO)                                     │
│ • Quay Registry (stable-3.16)                                   │
│ • GitLab (with runners)                                         │
│ • OpenShift GitOps (gitops-1.15)                               │
│ • Trusted Software Factory (TSF) via tsf CLI:                  │
│   ├─ Konflux (UI + backend)                                    │
│   ├─ Red Hat Trusted Artifact Signer (RHTAS)                   │
│   ├─ Trusted Profile Analyzer (TPA)                            │
│   ├─ Keycloak authentication                                   │
│   └─ Pipeline-as-Code controller                               │
│ • ClusterRole: konflux-admin-user-actions                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Tenant-Level (Per user)                                         │
├─────────────────────────────────────────────────────────────────┤
│ • Namespace: user-{guid}-tenant (Konflux workspace)            │
│ • Namespace: user-{guid}-managed (target deployment)           │
│ • GitLab user + sample-component-golang repository             │
│ • Quay user account                                             │
│ • HTPasswd OpenShift user                                       │
│ • RoleBindings to konflux-admin-user-actions                   │
│ • Showroom lab guide (user-{guid}-showroom namespace)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Requirements Analysis

### Module 01: Orientation (10 min)

**What Students Do:**
- Tour pre-provisioned environment
- Verify access to GitLab, Quay, Konflux UI
- Understand the supply chain problem

**Infrastructure Needs:**
- ✅ GitLab accessible with user credentials
- ✅ Quay accessible with user credentials
- ✅ Konflux UI route accessible
- ✅ Keycloak authentication configured
- ✅ OpenShift console access (HTPasswd)

**Provision Data Required:**
```yaml
- konflux_ui_url
- gitlab_url
- gitlab_username
- gitlab_password
- quay_url
- quay_user
- quay_password
- openshift_console_url
- openshift_username
- openshift_password
- tenant_namespace: user-{guid}-tenant
- managed_namespace: user-{guid}-managed
```

---

### Module 02: Onboard Your Application (15 min)

**What Students Do:**
1. Create Konflux Application
2. Create Konflux Component linked to GitLab repo
3. Configure Pipelines-as-Code webhook
4. Verify first PipelineRun created

**Infrastructure Needs:**
- ✅ GitLab repository pre-seeded: `sample-component-golang`
- ✅ GitLab webhook capability (PAC controller route)
- ✅ Konflux workspace in tenant namespace
- ✅ RBAC: Create Applications, Components, Repositories (PAC)
- ✅ ServiceAccount with git/image push permissions

**Pre-configuration:**
- Sample app repository imported to user's GitLab namespace
- GitLab personal access token (or integration via TSF)
- Quay robot account credentials in namespace Secret
- Pipeline-as-Code controller route accessible

**RBAC Required:**
```yaml
# ClusterRole: konflux-admin-user-actions
- appstudio.redhat.com/applications: [create, get, list, watch, update, delete]
- appstudio.redhat.com/components: [create, get, list, watch, update, delete]
- pipelinesascode.tekton.dev/repositories: [create, get, list, watch, update, delete]
- secrets: [create, get, list, update] # For GitLab/Quay credentials
```

---

### Module 03: Build and Scan (20 min)

**What Students Do:**
1. Trigger build via code push
2. Watch PipelineRun in Konflux UI
3. Inspect generated CycloneDX SBOM
4. Verify image in Quay

**Infrastructure Needs:**
- ✅ Konflux build pipeline (auto-created by Component)
- ✅ SBOM generation task in pipeline
- ✅ Quay push credentials configured
- ✅ Image scanning (ACS or embedded scanner)

**Pipeline Tasks (auto-configured by Konflux):**
1. git-clone
2. build-container
3. sbom-cyclonedx-generate
4. acs-image-scan (or equivalent)
5. push-to-quay

**RBAC Required:**
```yaml
- tekton.dev/pipelineruns: [get, list, watch]
- tekton.dev/taskruns: [get, list, watch]
- pods/log: [get] # To view pipeline logs
```

**Pre-configuration:**
- Quay push secret in tenant namespace
- Pipeline ServiceAccount linked to push secret

---

### Module 04: Signing and Provenance (20 min)

**What Students Do:**
1. Use cosign to verify image signature
2. Inspect SLSA Level 3 provenance attestation
3. Examine Rekor transparency log entry
4. Verify Fulcio certificate chain

**Infrastructure Needs:**
- ✅ RHTAS components (via TSF):
  - Fulcio (certificate authority)
  - Rekor (transparency log)
  - TUF (root of trust)
- ✅ Tekton Chains configured for signing
- ✅ Signing keys/keyless signing configured
- ✅ SLSA provenance generation

**Pre-configuration:**
- Tekton Chains operator installed (via TSF)
- Chains configured to sign TaskRuns/PipelineRuns
- Fulcio OIDC issuer configured
- Rekor server accessible

**Provision Data Required:**
```yaml
- tas_fulcio_url: https://fulcio-server-...
- tas_rekor_url: https://rekor-server-...
- tas_tuf_url: https://tuf-...
```

**Student Commands (examples):**
```bash
# Verify signature
cosign verify \
  --rekor-url $TAS_REKOR_URL \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  $IMAGE_URL

# Inspect provenance
cosign verify-attestation \
  --type slsaprovenance \
  --rekor-url $TAS_REKOR_URL \
  $IMAGE_URL | jq
```

---

### Module 05: Integration Testing and Policy (15 min)

**What Students Do:**
1. Examine Conforma (Enterprise Contract) policy rules
2. Observe integration test pipeline
3. See policy check results
4. Understand how failed checks block promotion

**Infrastructure Needs:**
- ✅ Enterprise Contract policy configuration
- ✅ Integration test pipeline (auto-created by IntegrationTestScenario)
- ✅ Policy results visible in Konflux UI

**RBAC Required:**
```yaml
- appstudio.redhat.com/integrationtestscenarios: [create, get, list, watch]
- appstudio.redhat.com/enterprisecontractpolicies: [get, list, watch]
- appstudio.redhat.com/snapshots: [get, list, watch]
```

**Pre-configuration:**
- Default EnterpriseContractPolicy installed
- IntegrationTestScenario auto-created for new Components
- Policy checks run on Snapshot creation

---

### Module 06: Release to Production (15 min)

**What Students Do:**
1. Trigger Konflux release
2. Watch ReleasePipeline execution
3. Verify signed image in production Quay repo
4. Trace artifact lifecycle from commit → production

**Infrastructure Needs:**
- ✅ ReleasePlan configured
- ✅ Production Quay organization/repository
- ✅ Release pipeline with policy gates
- ✅ Target Environment (managed namespace or separate Quay repo)

**RBAC Required:**
```yaml
- appstudio.redhat.com/releaseplans: [create, get, list, watch, update]
- appstudio.redhat.com/releases: [create, get, list, watch]
- appstudio.redhat.com/environments: [create, get, list, watch]
- appstudio.redhat.com/snapshotenvironmentbindings: [get, list, watch]
```

**Pre-configuration:**
- ReleasePlan linking dev → prod
- Environment resource for "production"
- Release pipeline template
- Quay robot account for production push

**Typical Flow:**
1. Student creates Release referencing ReleasePlan
2. Release pipeline runs (policy checks, image copy, signing)
3. Image pushed to production Quay organization
4. Deployment updated in managed namespace

---

### Module 07: Real-World Incident Response (25 min)

**What Students Do:**
1. **Scenario 1: Unsigned Hotfix**
   - Push image outside Konflux
   - Attempt deployment
   - Observe signature verification failure
   - Diagnose with cosign

2. **Scenario 2: CVE Policy Breach**
   - Trigger build with vulnerable dependency
   - Watch Conforma policy fail
   - Inspect policy output to identify CVE
   - Understand promotion block

3. **Scenario 3: Config Drift (Key Mismatch)**
   - Simulate signing key rotation
   - Deploy image signed with old key
   - Observe verification failure
   - Use cosign to identify key mismatch

**Infrastructure Needs:**
- ✅ All previous components functional
- ✅ Policy enforcement active
- ✅ Clear error messages from Conforma
- ✅ cosign CLI available (in terminal or bastion)

**Pre-configuration:**
- Admission controller or deployment gate that checks signatures
- Conforma policy with CVE rules
- Terminal access for cosign commands (Wetty/bastion)

**RBAC Required:**
- Same as previous modules (read access to policy results, releases)

---

## Infrastructure Components

### 1. S4 Object Storage (MinIO)

**Purpose**: Backend storage for Quay registry  
**Namespace**: `s4`  
**Configuration**:
```yaml
storage: 20Gi
buckets:
  - quay-registry
auth:
  username: s4admin
  password: {{ common_admin_password }}
api_enabled: true
route_enabled: true
```

**Workload**: `agnosticd.core_workloads.ocp4_workload_s4`

---

### 2. Quay Registry

**Purpose**: Container image registry  
**Namespace**: `quay-registry`  
**Configuration**:
```yaml
channel: stable-3.16
backend: s4
admin_user: quayadmin
admin_password: {{ common_admin_password }}
organizations:
  - tsf (cluster-wide, created by TSF)
  - user-{guid} (per-user, created by tenant workload)
```

**Workload**: `agnosticd.core_workloads.ocp4_workload_quay_operator`

**Tenant Actions**:
- Create user account via API
- Set password
- Create docker-registry Secret in tenant namespace

---

### 3. GitLab

**Purpose**: Source control and CI triggers  
**Namespace**: `gitlab`  
**Configuration**:
```yaml
auth_mode: native
root_password: {{ common_admin_password }}
runners: enabled
groups:
  - tsf (shared group)
```

**Workload**: `agnosticd.core_workloads.ocp4_workload_gitlab`

**Tenant Actions**:
- Create user account
- Import sample-component-golang from GitHub
- Add user to 'tsf' group (developer access)
- Generate personal access token (stored in Secret)

---

### 4. OpenShift GitOps

**Purpose**: GitOps workflows (optional for lab, but installed by TSF)  
**Namespace**: `openshift-gitops`  
**Configuration**:
```yaml
channel: gitops-1.15
cluster_admin: true
resources:
  controller:
    cpu: 2-4 cores
    memory: 4-8Gi
  repo_server:
    cpu: 500m-2 cores
    memory: 512Mi-2Gi
```

**Workload**: `agnosticd.core_workloads.ocp4_workload_openshift_gitops`

---

### 5. Trusted Software Factory (TSF)

**Purpose**: Installs Konflux, RHTAS, TPA, Keycloak via tsf CLI  
**Namespace**: `tsf` (control namespace)  
**Components Installed**:

#### 5a. Konflux
- **Namespace**: `konflux-ui`
- **Components**: UI, backend controllers, build service
- **Integration**: GitLab (group: tsf), Quay (org: tsf)

#### 5b. Red Hat Trusted Artifact Signer (RHTAS)
- **Namespace**: `tsf-tas`
- **Components**:
  - Fulcio (certificate authority)
  - Rekor (transparency log)
  - TUF (root of trust)
  - Timestamp authority
- **Integration**: Configured via TSF CLI

#### 5c. Trusted Profile Analyzer (TPA)
- **Namespace**: `tsf-tpa`
- **Purpose**: Policy analysis, vulnerability correlation
- **UI**: Web interface for artifact inspection

#### 5d. Keycloak
- **Namespace**: `tsf-keycloak`
- **Purpose**: SSO/authentication for TSF components
- **Users**: Managed via Keycloak admin console
- **Integration**: Konflux UI, TPA, etc.

#### 5e. Pipeline-as-Code Controller
- **Namespace**: `openshift-pipelines`
- **Purpose**: GitLab webhook integration for Tekton
- **Route**: `pipelines-as-code-controller`

**Workload**: `rhpds.ads.ocp4_workload_trusted_software_factory`

**TSF Installation Process**:
1. Create `tsf` namespace, ServiceAccount, ClusterRoleBinding
2. Deploy `tsf-cli` pod (from quay.io/rhpds/tsf-cli:latest)
3. Run: `tsf config --create --force`
4. Patch config: disable cert-manager subscription management
5. Run: `tsf integration gitlab --host ... --token ... --group tsf`
6. Run: `tsf integration quay --url ... --token ... --organization tsf`
7. Run: `tsf deploy` (installs all components via Helm charts)

**Critical Secrets**:
- `root-user-personal-token` (gitlab namespace) - GitLab root PAT
- `quay-admin-token` (quay-registry namespace) - Quay admin OAuth token

**Routes to Expose**:
- Konflux UI: `konflux-ui` route in `konflux-ui` namespace
- Fulcio: `fulcio-server` route in `tsf-tas` namespace
- Rekor: `rekor-server` route in `tsf-tas` namespace
- TPA: `trustification-ui` route in `tsf-tpa` namespace
- Keycloak: `keycloak` route in `tsf-keycloak` namespace
- PAC Controller: `pipelines-as-code-controller` route in `openshift-pipelines` namespace

---

### 6. Tenant Namespaces

**Purpose**: Isolated workspace per user  
**Namespaces**:
1. `user-{guid}-tenant` - Konflux workspace (Applications, Components)
2. `user-{guid}-managed` - Target deployment environment

**Configuration**:
```yaml
labels:
  konflux-tenant: user-{guid}
  konflux-ci.dev/type: tenant
  created-by: agnosticd
  tenant: user-{guid}

quotas:
  limits.cpu: 8
  limits.memory: 16Gi
  requests.cpu: 4
  requests.memory: 8Gi

limit_ranges:
  default:
    cpu: 500m
    memory: 512Mi
  defaultRequest:
    cpu: 100m
    memory: 128Mi
```

**Workload**: `agnosticd.namespaced_workloads.ocp4_workload_tenant_namespace`

---

### 7. ClusterRole: konflux-admin-user-actions

**Purpose**: Grant users permissions to manage Konflux resources  
**Scope**: Cluster-wide role, bound per-namespace

**Key Permissions**:
```yaml
# Konflux resources (full CRUD)
- appstudio.redhat.com/*: [applications, components, releaseplans, releases, 
                            integrationtestscenarios, environments, 
                            snapshotenvironmentbindings, snapshots]

# Tekton resources (read-only)
- tekton.dev/*: [pipelineruns, pipelines, taskruns, tasks]

# Pipelines-as-Code (full CRUD)
- pipelinesascode.tekton.dev/repositories: [*]

# Namespace resources (full CRUD)
- ""/secrets, configmaps: [*]
- ""/serviceaccounts: [get, list, watch, patch, update]

# Inspection resources (read-only)
- ""/pods, pods/log: [get, list, watch]
- route.openshift.io/routes: [get, list, watch]
- image.openshift.io/imagestreams: [get, list, watch]
```

**Created by**: Cluster workload  
**Bound by**: Tenant workload (RoleBinding in each tenant namespace)

---

### 8. HTPasswd Authentication

**Purpose**: OpenShift console login  
**Users**: `user-{guid}` per student  
**Password**: `{{ common_password }}`

**Workload**: `agnosticd.namespaced_workloads.ocp4_workload_tenant_authentication_user`

---

### 9. Showroom Lab Guide

**Purpose**: Embedded lab guide with terminal  
**Namespace**: `user-{guid}-showroom` (per user)  
**Configuration**:
```yaml
git_repo: https://github.com/rhpds/konflux-tssc-lab.git
git_ref: main
terminal_type: wetty
ssh_bastion_login: true
```

**Workload**: `agnosticd.showroom.ocp4_workload_showroom`

---

## Implementation Phases

### Phase 1: Collection Setup
**Goal**: Configure Ansible collection metadata and dependencies

**Tasks**:
1. Update `automation/ansible/galaxy.yml`:
   - Collection name: `konflux_tssc_lab.automation`
   - Version: `1.0.0`
   - Dependencies: kubernetes.core, community.general

2. Update `automation/ansible/meta/runtime.yml`:
   - Requires ansible-core >= 2.15

3. Verify collection can be built:
   ```bash
   ansible-galaxy collection build automation/ansible
   ```

**References**:
- LB1353 galaxy.yml pattern
- AgnosticD collection standards

---

### Phase 2: Cluster Workload Role
**Goal**: Create lab-specific RBAC and collect access URLs

**Role**: `automation/ansible/roles/ocp4_workload_konflux_tssc_cluster`

> **IMPORTANT**: This role does NOT install infrastructure. All infrastructure (S4, Quay, GitLab, GitOps, TSF) is installed by the **AgnosticV catalog item** via existing workloads. See LB1353 cluster `common.yaml` for the complete workload list.

**What This Role Does** (minimal implementation):

#### 2.1 Create ClusterRole for Tenant RBAC
```yaml
- name: Create konflux-admin-user-actions ClusterRole
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: rbac.authorization.k8s.io/v1
      kind: ClusterRole
      metadata:
        name: konflux-admin-user-actions
        labels:
          app: konflux-tssc-lab
          created-by: agnosticd
      rules:
        # Konflux Application resources (full CRUD)
        - apiGroups: ["appstudio.redhat.com"]
          resources: ["applications", "applications/status"]
          verbs: ["*"]
        
        # Konflux Component resources (full CRUD)
        - apiGroups: ["appstudio.redhat.com"]
          resources: ["components", "components/status"]
          verbs: ["*"]
        
        # Konflux ReleasePlan resources (full CRUD)
        - apiGroups: ["appstudio.redhat.com"]
          resources: ["releaseplans", "releaseplans/status", "releases", "releases/status"]
          verbs: ["*"]
        
        # Konflux IntegrationTestScenario resources (full CRUD)
        - apiGroups: ["appstudio.redhat.com"]
          resources: ["integrationtestscenarios", "integrationtestscenarios/status"]
          verbs: ["*"]
        
        # Konflux Environment resources (full CRUD)
        - apiGroups: ["appstudio.redhat.com"]
          resources: ["environments", "environments/status"]
          verbs: ["*"]
        
        # Konflux Snapshot resources (read-only)
        - apiGroups: ["appstudio.redhat.com"]
          resources: ["snapshots", "snapshots/status", "snapshotenvironmentbindings", "snapshotenvironmentbindings/status"]
          verbs: ["get", "list", "watch"]
        
        # Enterprise Contract policy (read-only)
        - apiGroups: ["appstudio.redhat.com"]
          resources: ["enterprisecontractpolicies", "enterprisecontractpolicies/status"]
          verbs: ["get", "list", "watch"]
        
        # Tekton resources (read-only for viewing builds)
        - apiGroups: ["tekton.dev"]
          resources: ["pipelineruns", "pipelineruns/status", "pipelines", "taskruns", "taskruns/status", "tasks"]
          verbs: ["get", "list", "watch"]
        
        # Pipelines-as-Code Repository resources (full CRUD)
        - apiGroups: ["pipelinesascode.tekton.dev"]
          resources: ["repositories", "repositories/status"]
          verbs: ["*"]
        
        # Namespace resources (full CRUD)
        - apiGroups: [""]
          resources: ["secrets", "configmaps"]
          verbs: ["*"]
        
        - apiGroups: [""]
          resources: ["serviceaccounts"]
          verbs: ["get", "list", "watch", "patch", "update"]
        
        # Pod logs for debugging
        - apiGroups: [""]
          resources: ["pods", "pods/log"]
          verbs: ["get", "list", "watch"]
        
        # Routes (read-only)
        - apiGroups: ["route.openshift.io"]
          resources: ["routes"]
          verbs: ["get", "list", "watch"]
        
        # ImageStreams (read-only)
        - apiGroups: ["image.openshift.io"]
          resources: ["imagestreams", "imagestreamtags"]
          verbs: ["get", "list", "watch"]
        
        # Deployments (read-only for release verification)
        - apiGroups: ["apps"]
          resources: ["deployments", "deployments/status"]
          verbs: ["get", "list", "watch"]
        
        # Services (read-only)
        - apiGroups: [""]
          resources: ["services"]
          verbs: ["get", "list", "watch"]
```

#### 2.2 Collect TSF Access URLs
```yaml
- name: Get Konflux UI route
  kubernetes.core.k8s_info:
    api_version: route.openshift.io/v1
    kind: Route
    namespace: konflux-ui
  register: r_konflux_routes

- name: Get Keycloak route
  kubernetes.core.k8s_info:
    api_version: route.openshift.io/v1
    kind: Route
    name: keycloak
    namespace: tsf-keycloak
  register: r_keycloak_route

- name: Get RHTAS Fulcio route
  kubernetes.core.k8s_info:
    api_version: route.openshift.io/v1
    kind: Route
    name: fulcio-server
    namespace: tsf-tas
  register: r_fulcio_route

- name: Get RHTAS Rekor route
  kubernetes.core.k8s_info:
    api_version: route.openshift.io/v1
    kind: Route
    name: rekor-server
    namespace: tsf-tas
  register: r_rekor_route

- name: Get TPA route
  kubernetes.core.k8s_info:
    api_version: route.openshift.io/v1
    kind: Route
    namespace: tsf-tpa
  register: r_tpa_routes

- name: Get Pipeline-as-Code controller route
  kubernetes.core.k8s_info:
    api_version: route.openshift.io/v1
    kind: Route
    name: pipelines-as-code-controller
    namespace: openshift-pipelines
  register: r_pac_route
```

#### 2.3 Save Access Information
```yaml
- name: Save TSF access URLs to user data
  agnosticd.core.agnosticd_user_info:
    data:
      konflux_ui_url: "{{ 'https://' + r_konflux_routes.resources[0].spec.host if r_konflux_routes.resources | length > 0 else 'Not available' }}"
      keycloak_url: "{{ 'https://' + r_keycloak_route.resources[0].spec.host if r_keycloak_route.resources | length > 0 else 'Not available' }}"
      tas_fulcio_url: "{{ 'https://' + r_fulcio_route.resources[0].spec.host if r_fulcio_route.resources | length > 0 else 'Not available' }}"
      tas_rekor_url: "{{ 'https://' + r_rekor_route.resources[0].spec.host if r_rekor_route.resources | length > 0 else 'Not available' }}"
      tpa_url: "{{ 'https://' + r_tpa_routes.resources[0].spec.host if r_tpa_routes.resources | length > 0 else 'Not available' }}"
      pac_controller_url: "{{ 'https://' + r_pac_route.resources[0].spec.host if r_pac_route.resources | length > 0 else 'Not available' }}"
```

**Defaults** (`defaults/main.yml`):
```yaml
# No defaults needed - this role only creates RBAC and collects URLs
ocp4_workload_konflux_tssc_cluster_become_override: false
ocp4_workload_konflux_tssc_cluster_silent: false
```

**Templates**:
- None needed (ClusterRole defined inline in task)

**What This Role Does NOT Do**:
- ❌ Install S4, Quay, GitLab, GitOps → Handled by AgnosticV workload list
- ❌ Install TSF (Konflux, RHTAS, TPA, Keycloak) → Handled by `rhpds.ads.ocp4_workload_trusted_software_factory`
- ❌ Create namespaces → Handled by pool/component architecture
- ❌ Configure authentication → Handled by `ocp4_workload_authentication`

**References**:
- LB1353 cluster `common.yaml`: Shows complete workload list in AgnosticV catalog item
- TSF role: https://github.com/rhpds/rhpds.ads/tree/main/roles/ocp4_workload_trusted_software_factory
- This role is called FROM the AgnosticV catalog item, not standalone

---

### Phase 3: Tenant Workload Role
**Goal**: Create per-user resources by orchestrating existing roles

**Role**: `automation/ansible/roles/ocp4_workload_konflux_tssc_tenant`

> **IMPORTANT**: This role mostly calls existing `namespaced_workloads` roles. It only implements custom RBAC bindings.

**Tasks Breakdown**:

#### 3.1 Create Tenant Namespaces
```yaml
- name: Create tenant namespaces
  ansible.builtin.include_role:
    name: agnosticd.namespaced_workloads.ocp4_workload_tenant_namespace
  vars:
    ocp4_workload_tenant_namespace_username: "user-{{ guid }}"
    ocp4_workload_tenant_namespace_suffixes:
      - suffix: tenant
        metadata:
          labels:
            konflux-tenant: "user-{{ guid }}"
            konflux-ci.dev/type: tenant
      - suffix: managed
        metadata:
          labels:
            konflux-managed: "user-{{ guid }}"
```

#### 3.2 Create GitLab User and Import Sample Repository
```yaml
- name: Create GitLab user and import sample repo
  ansible.builtin.include_role:
    name: agnosticd.namespaced_workloads.ocp4_workload_tenant_gitlab
  vars:
    ocp4_workload_tenant_gitlab_namespace: gitlab
    ocp4_workload_tenant_gitlab_username: "user-{{ guid }}"
    ocp4_workload_tenant_gitlab_password: "{{ common_password }}"
    ocp4_workload_tenant_gitlab_user_repositories:
      - name: sample-component-golang
        url: https://github.com/konflux-ci/sample-component-golang.git
        visibility: private
    ocp4_workload_tenant_gitlab_user_groups:
      - name: tsf
        access_level: developer
```

**What This Does**:
- Creates GitLab user via API
- Imports `sample-component-golang` from GitHub to user's personal namespace
- Adds user to shared `tsf` group (developer access)
- Saves GitLab URL/credentials to user_data

#### 3.3 Create Quay User and Push Credentials
```yaml
- name: Create Quay user
  ansible.builtin.include_role:
    name: agnosticd.namespaced_workloads.ocp4_workload_tenant_quay
  vars:
    ocp4_workload_tenant_quay_namespace: quay-registry
    ocp4_workload_tenant_quay_user: "user-{{ guid }}"
    ocp4_workload_tenant_quay_user_password: "{{ common_password }}"
    ocp4_workload_tenant_quay_pipeline_namespaces:
      - "user-{{ guid }}-tenant"
      - "user-{{ guid }}-managed"
```

**What This Does**:
- Creates Quay user via superuser API
- Sets password
- Creates `quay-registry-credentials` Secret in both namespaces (docker-registry type)
- Links Secret to `pipeline` ServiceAccount
- Saves Quay URL/credentials to user_data

#### 3.4 Create OpenShift User (HTPasswd)
```yaml
- name: Create HTPasswd user
  ansible.builtin.include_role:
    name: agnosticd.namespaced_workloads.ocp4_workload_tenant_authentication_user
  vars:
    ocp4_workload_tenant_authentication_user_provider: htpasswd
    ocp4_workload_tenant_authentication_user_username: "user-{{ guid }}"
    ocp4_workload_tenant_authentication_user_password: "{{ common_password }}"
    ocp4_workload_tenant_authentication_user_create_rbac: true
    ocp4_workload_tenant_namespace_name: "user-{{ guid }}-tenant"
    ocp4_workload_tenant_namespace_additional_namespaces:
      - name: "user-{{ guid }}-managed"
```

**What This Does**:
- Creates HTPasswd user
- Creates RoleBindings for `admin` role in both namespaces (standard OpenShift admin)
- Saves OpenShift credentials to user_data

#### 3.5 Bind User to Konflux ClusterRole (Custom Task)
```yaml
- name: Create RoleBinding for konflux-admin-user-actions in tenant namespace
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: rbac.authorization.k8s.io/v1
      kind: RoleBinding
      metadata:
        name: konflux-admin
        namespace: "user-{{ guid }}-tenant"
      roleRef:
        apiGroup: rbac.authorization.k8s.io
        kind: ClusterRole
        name: konflux-admin-user-actions
      subjects:
        - apiGroup: rbac.authorization.k8s.io
          kind: User
          name: "user-{{ guid }}"

- name: Create RoleBinding for konflux-admin-user-actions in managed namespace
  kubernetes.core.k8s:
    state: present
    definition:
      apiVersion: rbac.authorization.k8s.io/v1
      kind: RoleBinding
      metadata:
        name: konflux-admin
        namespace: "user-{{ guid }}-managed"
      roleRef:
        apiGroup: rbac.authorization.k8s.io
        kind: ClusterRole
        name: konflux-admin-user-actions
      subjects:
        - apiGroup: rbac.authorization.k8s.io
          kind: User
          name: "user-{{ guid }}"
```

**Why Custom**: The `namespaced_workloads` roles don't know about the Konflux-specific ClusterRole.

#### 3.6 Deploy Showroom Lab Guide (Custom Task)
```yaml
- name: Get cluster-level URLs from user_data
  ansible.builtin.set_fact:
    _konflux_ui_url: "{{ lookup('agnosticd_user_data', 'konflux_ui_url') }}"
    _keycloak_url: "{{ lookup('agnosticd_user_data', 'keycloak_url') }}"
    _tas_fulcio_url: "{{ lookup('agnosticd_user_data', 'tas_fulcio_url') }}"
    _tas_rekor_url: "{{ lookup('agnosticd_user_data', 'tas_rekor_url') }}"
    _gitlab_url: "{{ lookup('agnosticd_user_data', 'gitlab_url') }}"
    _quay_url: "{{ lookup('agnosticd_user_data', 'quay_url') }}"

- name: Deploy Showroom with user data
  ansible.builtin.include_role:
    name: agnosticd.showroom.ocp4_workload_showroom
  vars:
    ocp4_workload_showroom_namespace: "user-{{ guid }}-showroom"
    ocp4_workload_showroom_content_git_repo: https://github.com/rhpds/konflux-tssc-lab.git
    ocp4_workload_showroom_content_git_repo_ref: main
    ocp4_workload_showroom_terminal_type: wetty
    ocp4_workload_showroom_wetty_ssh_bastion_login: true
    ocp4_workload_showroom_user_data:
      # Namespaces
      tenant_namespace: "user-{{ guid }}-tenant"
      managed_namespace: "user-{{ guid }}-managed"
      
      # GitLab
      gitlab_url: "{{ _gitlab_url }}"
      gitlab_username: "user-{{ guid }}"
      gitlab_password: "{{ common_password }}"
      
      # Quay
      quay_url: "{{ _quay_url }}"
      quay_user: "user-{{ guid }}"
      quay_password: "{{ common_password }}"
      
      # OpenShift
      openshift_console_url: "{{ openshift_console_url }}"
      openshift_username: "user-{{ guid }}"
      openshift_password: "{{ common_password }}"
      
      # Konflux / TSF
      konflux_ui_url: "{{ _konflux_ui_url }}"
      keycloak_url: "{{ _keycloak_url }}"
      tas_fulcio_url: "{{ _tas_fulcio_url }}"
      tas_rekor_url: "{{ _tas_rekor_url }}"
```

**Why Custom**: Need to pass all URLs from cluster workload to Showroom for variable substitution.

#### 3.7 Save Consolidated User Data
```yaml
- name: Save consolidated tenant information
  agnosticd.core.agnosticd_user_info:
    data:
      tenant_namespace: "user-{{ guid }}-tenant"
      managed_namespace: "user-{{ guid }}-managed"
      student_username: "user-{{ guid }}"
      student_password: "{{ common_password }}"
```

**Defaults** (`defaults/main.yml`):
```yaml
---
# Tenant user identifier
ocp4_workload_konflux_tssc_tenant_user: "user-{{ guid }}"

# Namespace names
ocp4_workload_konflux_tssc_tenant_namespace: "user-{{ guid }}-tenant"
ocp4_workload_konflux_tssc_tenant_managed_namespace: "user-{{ guid }}-managed"

# Workload control
ocp4_workload_konflux_tssc_tenant_become_override: false
ocp4_workload_konflux_tssc_tenant_silent: false
```

**Templates**:
- `templates/rolebinding-admin.yaml.j2` - **Not needed** (RoleBinding defined inline)

**What This Role Does NOT Do**:
- ❌ Create namespaces directly → Uses `ocp4_workload_tenant_namespace`
- ❌ Call GitLab API directly → Uses `ocp4_workload_tenant_gitlab`
- ❌ Call Quay API directly → Uses `ocp4_workload_tenant_quay`
- ❌ Manage HTPasswd directly → Uses `ocp4_workload_tenant_authentication_user`

**References**:
- LB1353 tenant `common.yaml`: Shows exact same pattern (call existing roles + custom RBAC)
- Namespaced workloads collection: https://github.com/rhpds/namespaced_workloads

---

### Phase 4: Sample Application
**Goal**: Understand what students will deploy

**Source**: Use existing `konflux-ci/sample-component-golang`  
**Import Method**: GitLab API via tenant_gitlab role

**Application Structure**:
```
sample-component-golang/
├── main.go                  # Simple HTTP server
├── go.mod                   # Go dependencies
├── go.sum
├── Dockerfile               # Container build
└── .tekton/                 # Pipelines-as-Code config (optional)
    └── pull-request.yaml
```

**No Custom Application Needed**: 
- Use upstream Konflux sample
- GitLab import handles cloning from GitHub
- Students will trigger builds by pushing commits

**Alternative**: If customization needed, create simple app with:
- Vulnerable dependency (for Module 07, Scenario 2)
- Clear SBOM generation
- Simple HTTP endpoint for verification

---

### Phase 5: Health Check Playbook
**Goal**: Verify all components are healthy

**File**: `qa-automation/healthcheck.yml`

**Checks**:
```yaml
---
- name: Konflux TSSC Lab Health Check
  hosts: localhost
  gather_facts: false
  tasks:
    # Cluster-level checks
    - name: Check S4 deployment
      kubernetes.core.k8s_info:
        kind: Deployment
        namespace: s4
        name: s4
      register: r_s4
      failed_when: r_s4.resources[0].status.availableReplicas != 1

    - name: Check Quay registry
      kubernetes.core.k8s_info:
        kind: QuayRegistry
        namespace: quay-registry
        name: quay
      register: r_quay
      failed_when: r_quay.resources[0].status.conditions | selectattr('type', 'equalto', 'Available') | list | length == 0

    - name: Check GitLab deployment
      kubernetes.core.k8s_info:
        kind: Deployment
        namespace: gitlab
        name: gitlab-webservice-default
      register: r_gitlab

    - name: Check TSF components
      kubernetes.core.k8s_info:
        kind: Deployment
        namespace: "{{ item.namespace }}"
        name: "{{ item.name }}"
      loop:
        - {namespace: konflux-ui, name: konflux-ui}
        - {namespace: tsf-tas, name: fulcio-server}
        - {namespace: tsf-tas, name: rekor-server}
        - {namespace: tsf-tpa, name: trustification-ui}
        - {namespace: tsf-keycloak, name: keycloak}

    - name: Check ClusterRole exists
      kubernetes.core.k8s_info:
        kind: ClusterRole
        name: konflux-admin-user-actions
      register: r_clusterrole
      failed_when: r_clusterrole.resources | length == 0

    # Per-user checks (if num_users > 0)
    - name: Check tenant namespaces
      kubernetes.core.k8s_info:
        kind: Namespace
        name: "user-{{ item }}-{{ suffix }}"
      loop: "{{ range(1, num_users + 1) | list }}"
      loop_control:
        loop_var: item
      vars:
        suffix: "{{ ['tenant', 'managed'] }}"

    - name: Check RoleBindings
      kubernetes.core.k8s_info:
        kind: RoleBinding
        namespace: "user-{{ item }}-tenant"
        name: konflux-admin
      loop: "{{ range(1, num_users + 1) | list }}"

    - name: Verify routes are accessible
      ansible.builtin.uri:
        url: "{{ item }}"
        validate_certs: false
        status_code: [200, 302, 401, 403]
      loop:
        - "{{ konflux_ui_url }}"
        - "{{ gitlab_url }}"
        - "{{ quay_url }}"
        - "{{ keycloak_url }}"
```

**References**:
- Standard AgnosticD health check patterns
- k8s_info module documentation

---

### Phase 6: E2E Test Playbook
**Goal**: Validate complete student workflow

**File**: `qa-automation/e2e.yml`

**Test Scenarios**:
```yaml
---
- name: Konflux TSSC Lab E2E Test
  hosts: localhost
  gather_facts: false
  tasks:
    # Setup: Create test user resources
    - name: Create test tenant namespaces
    - name: Create test GitLab user and repo
    - name: Create test Quay user

    # Module 02: Onboard Application
    - name: Create Konflux Application
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: appstudio.redhat.com/v1alpha1
          kind: Application
          metadata:
            name: test-app
            namespace: user-test-tenant
          spec:
            displayName: Test Application

    - name: Create Konflux Component
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: appstudio.redhat.com/v1alpha1
          kind: Component
          metadata:
            name: test-component
            namespace: user-test-tenant
          spec:
            application: test-app
            componentName: test-component
            source:
              git:
                url: "{{ test_gitlab_repo_url }}"
                revision: main

    - name: Wait for initial PipelineRun
      kubernetes.core.k8s_info:
        kind: PipelineRun
        namespace: user-test-tenant
        label_selectors:
          - "appstudio.openshift.io/component=test-component"
      register: r_pipelinerun
      until: r_pipelinerun.resources | length > 0
      retries: 30
      delay: 10

    # Module 03: Build and Scan
    - name: Wait for PipelineRun to complete
      kubernetes.core.k8s_info:
        kind: PipelineRun
        namespace: user-test-tenant
        name: "{{ r_pipelinerun.resources[0].metadata.name }}"
      register: r_pipelinerun_status
      until:
        - r_pipelinerun_status.resources[0].status.conditions is defined
        - r_pipelinerun_status.resources[0].status.conditions | selectattr('type', 'equalto', 'Succeeded') | list | length > 0
      retries: 60
      delay: 10

    - name: Verify image in Quay
      ansible.builtin.uri:
        url: "{{ quay_url }}/api/v1/repository/user-test/test-component/tag/"
        headers:
          Authorization: "Bearer {{ test_quay_token }}"
        validate_certs: false
      register: r_quay_tags
      failed_when: r_quay_tags.json.tags | length == 0

    # Module 04: Verify Signing
    - name: Get image digest
    - name: Verify signature with cosign (via Job)

    # Module 05: Policy Check
    - name: Check IntegrationTestScenario created
    - name: Wait for integration test pipeline
    - name: Verify policy check results in Snapshot

    # Module 06: Release
    - name: Create ReleasePlan
    - name: Create Release
    - name: Wait for Release to complete
    - name: Verify image in production Quay repo

    # Cleanup
    - name: Delete test resources
```

**References**:
- Konflux API examples: https://konflux-ci.dev/docs/
- Tekton resource waiting patterns

---

## Sample Application Requirements

### Option 1: Use Upstream (Recommended)
**Repository**: https://github.com/konflux-ci/sample-component-golang  
**Advantages**:
- Already tested with Konflux
- Has .tekton/ directory with PaC configs
- Simple HTTP server (easy to verify deployment)
- Maintained by Konflux team

**Import Process** (handled by tenant_gitlab role):
```python
# GitLab API call
POST /api/v4/projects
{
  "name": "sample-component-golang",
  "import_url": "https://github.com/konflux-ci/sample-component-golang.git",
  "visibility": "private",
  "namespace_id": <user_namespace_id>
}
```

### Option 2: Custom Application (For Module 07)
**If** we need to inject vulnerabilities for Scenario 2:

**Repository Structure**:
```
konflux-sample-app/
├── main.go
├── go.mod              # Include old dependency with known CVE
├── go.sum
├── Dockerfile
└── .tekton/
    └── konflux-build.yaml
```

**Vulnerable Dependency Example**:
```go
// go.mod
module github.com/rhpds/konflux-sample-app

go 1.21

require (
    github.com/gin-gonic/gin v1.7.0  // Has CVE-2020-28483
)
```

**Decision**: Start with upstream, create custom fork only if needed for specific scenarios.

---

## Testing Strategy

### Manual Testing Checklist

**Cluster Workload**:
- [ ] All operators installed successfully
- [ ] S4 storage accessible
- [ ] Quay UI accessible, admin login works
- [ ] GitLab UI accessible, root login works
- [ ] Konflux UI accessible
- [ ] RHTAS routes accessible (Fulcio, Rekor)
- [ ] Keycloak admin console accessible
- [ ] ClusterRole created

**Tenant Workload (test with 1 user)**:
- [ ] Two namespaces created
- [ ] GitLab user can log in
- [ ] Sample repo imported and visible
- [ ] Quay user can log in
- [ ] OpenShift user can log in (HTPasswd)
- [ ] RoleBindings grant correct permissions
- [ ] Showroom lab guide accessible
- [ ] User can create Konflux Application
- [ ] User can create Konflux Component
- [ ] PipelineRun triggers automatically

**E2E Workflow**:
- [ ] Full onboard → build → sign → policy → release flow completes
- [ ] Image appears in Quay with signature
- [ ] Provenance attestation verifiable with cosign
- [ ] Policy check results visible in UI
- [ ] Release succeeds to production

### Multi-User Testing
- [ ] Deploy 5 users concurrently
- [ ] Verify namespace isolation
- [ ] Check resource quotas enforced
- [ ] Confirm no credential leakage between users

---

## References

### LB1353 Implementation
- **Cluster**: https://github.com/rhpds/agnosticv/tree/master/rh1-2027/lb1353-konflux-tsf-tssc-cnv-cluster
- **Tenant**: https://github.com/rhpds/agnosticv/tree/master/rh1-2027/lb1353-konflux-tsf-tssc-cnv-tenant

### Collections
- **rhpds.ads**: https://github.com/rhpds/rhpds.ads (TSF workload)
- **core_workloads**: https://github.com/rhpds/core_workloads (S4, Quay, GitLab, GitOps)
- **namespaced_workloads**: https://github.com/rhpds/namespaced_workloads (Tenant setup)
- **showroom**: https://github.com/rhpds/showroom (Lab guide)

### Product Documentation
- **Konflux**: https://konflux-ci.dev/docs/
- **RHTAS**: https://docs.redhat.com/en/documentation/red_hat_trusted_artifact_signer/
- **Tekton Chains**: https://tekton.dev/docs/chains/
- **cosign**: https://docs.sigstore.dev/cosign/overview/
- **Enterprise Contract**: (internal documentation)

### Sample Applications
- **Konflux samples**: https://github.com/konflux-ci/sample-component-golang

---

## Implementation Summary

### **What You Actually Need to Build**

| Component | Lines of Code | Complexity | Dependencies |
|-----------|---------------|------------|--------------|
| **Cluster Role** | ~100 | Low | None (just RBAC + URL collection) |
| **Tenant Role** | ~150 | Low | Calls 5 existing roles + custom RBAC |
| **AgnosticV Cluster Catalog** | ~200 | Medium | Copy LB1353 pattern |
| **AgnosticV Tenant Catalog** | ~150 | Medium | Copy LB1353 pattern |
| **Health Check Playbook** | ~100 | Low | Standard k8s_info checks |
| **E2E Test Playbook** | ~300 | Medium | Konflux API + wait loops |
| **Total Custom Code** | ~1000 lines | | |

### **What You Get For Free**

| Component | Provided By | Status |
|-----------|-------------|--------|
| S4 Storage | `ocp4_workload_s4` | ✅ Existing |
| Quay Registry | `ocp4_workload_quay_operator` | ✅ Existing |
| GitLab | `ocp4_workload_gitlab` | ✅ Existing |
| OpenShift GitOps | `ocp4_workload_openshift_gitops` | ✅ Existing |
| **Konflux** | TSF CLI | ✅ Existing |
| **RHTAS** | TSF CLI | ✅ Existing |
| **TPA** | TSF CLI | ✅ Existing |
| **Keycloak** | TSF CLI | ✅ Existing |
| **Tekton Chains** | TSF CLI | ✅ Existing |
| Tenant Namespaces | `ocp4_workload_tenant_namespace` | ✅ Existing |
| GitLab User/Repo | `ocp4_workload_tenant_gitlab` | ✅ Existing |
| Quay User | `ocp4_workload_tenant_quay` | ✅ Existing |
| HTPasswd Auth | `ocp4_workload_tenant_authentication_user` | ✅ Existing |
| Showroom | `ocp4_workload_showroom` | ✅ Existing |

### **Implementation Effort Estimate**

- **Cluster workload role**: 2-3 hours (mostly RBAC definition)
- **Tenant workload role**: 3-4 hours (orchestration + Showroom data passing)
- **AgnosticV catalog items**: 2-3 hours (copy/adapt LB1353)
- **Health check playbook**: 1-2 hours (standard checks)
- **E2E test playbook**: 4-6 hours (Konflux API learning curve)
- **Testing & debugging**: 8-12 hours (multi-user, edge cases)

**Total**: ~20-30 hours of implementation work

---

## Next Steps

1. **Review this plan** - Confirm architecture meets lab objectives
2. **Create AgnosticV catalog items** - Two items (cluster + tenant), copy LB1353 pattern
3. **Implement cluster workload** - 8 tasks, ~100 lines (Phase 2)
4. **Implement tenant workload** - 9 tasks, ~150 lines (Phase 3)
5. **Test with 1 user** - Manual validation of all modules
6. **Implement health check** - Automate validation
7. **Implement e2e tests** - Automate student workflow
8. **Write lab content** - AsciiDoc modules with tested procedures (content already stubbed)
9. **Multi-user testing** - Scale to 5-10 users
10. **Submit for review** - RHDP catalog submission

---

**End of Implementation Plan**
