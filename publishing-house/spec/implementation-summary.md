# Konflux TSSC Lab - Quick Implementation Summary

**Last Updated**: 2026-09-03  
**Status**: Planning Complete, Ready for Implementation

---

## TL;DR

You need to build **~250 lines of custom Ansible** to glue together existing AgnosticD roles. Everything else (Konflux, RHTAS, GitLab, Quay) is already implemented.

---

## What TSF Does For You ✅

The `rhpds.ads.ocp4_workload_trusted_software_factory` role runs the `tsf` CLI which auto-installs:

| Component | Namespace | What It Does |
|-----------|-----------|--------------|
| **Konflux** | `konflux-ui` | UI + backend controllers for Applications, Components, Builds |
| **RHTAS Fulcio** | `tsf-tas` | Certificate authority for keyless signing |
| **RHTAS Rekor** | `tsf-tas` | Transparency log for signatures |
| **RHTAS TUF** | `tsf-tas` | Root of trust |
| **TPA** | `tsf-tpa` | Trusted Profile Analyzer UI |
| **Keycloak** | `tsf-keycloak` | SSO authentication |
| **Tekton Chains** | `openshift-pipelines` | Auto-signs PipelineRuns with SLSA provenance |
| **Pipeline-as-Code** | `openshift-pipelines` | GitLab webhook integration |

**Integration**: TSF automatically configures GitLab (group `tsf`) and Quay (org `tsf`) integration.

---

## What You Need to Build ❌

### **1. Custom Cluster Workload** (~100 lines)
**File**: `automation/ansible/roles/ocp4_workload_konflux_tssc_cluster/tasks/workload.yml`

```yaml
# 3 tasks only:
1. Create ClusterRole konflux-admin-user-actions (inline YAML)
2. Get routes from TSF namespaces (6 k8s_info calls)
3. Save URLs to agnosticd_user_info (1 task)
```

**Purpose**: RBAC for students + expose TSF URLs to lab guide

---

### **2. Custom Tenant Workload** (~150 lines)
**File**: `automation/ansible/roles/ocp4_workload_konflux_tssc_tenant/tasks/workload.yml`

```yaml
# 9 tasks:
1. include_role: ocp4_workload_tenant_namespace (creates 2 namespaces)
2. include_role: ocp4_workload_tenant_gitlab (user + import sample repo)
3. include_role: ocp4_workload_tenant_quay (user + push credentials)
4. include_role: ocp4_workload_tenant_authentication_user (HTPasswd)
5. k8s: Create RoleBinding in user-{guid}-tenant
6. k8s: Create RoleBinding in user-{guid}-managed
7. set_fact: Get cluster URLs from user_data
8. include_role: ocp4_workload_showroom (with user_data)
9. agnosticd_user_info: Save consolidated student credentials
```

**Purpose**: Orchestrate existing roles + bind students to Konflux ClusterRole

---

### **3. AgnosticV Catalog Items** (~350 lines total)

#### Cluster Item (`lb-konflux-tssc-cluster/common.yaml`)
Copy LB1353 pattern, include these workloads:
```yaml
workloads:
  - agnosticd.core_workloads.ocp4_workload_authentication
  - agnosticd.core_workloads.ocp4_workload_openshift_gitops
  - agnosticd.core_workloads.ocp4_workload_s4
  - agnosticd.core_workloads.ocp4_workload_quay_operator
  - agnosticd.core_workloads.ocp4_workload_gitlab
  - rhpds.ads.ocp4_workload_trusted_software_factory
  - konflux_tssc_lab.automation.ocp4_workload_konflux_tssc_cluster
```

#### Tenant Item (`lb-konflux-tssc-tenant/common.yaml`)
Copy LB1353 pattern, include these workloads:
```yaml
workloads:
  - agnosticd.namespaced_workloads.ocp4_workload_tenant_namespace
  - agnosticd.namespaced_workloads.ocp4_workload_tenant_gitlab
  - agnosticd.namespaced_workloads.ocp4_workload_tenant_quay
  - agnosticd.namespaced_workloads.ocp4_workload_tenant_authentication_user
  - konflux_tssc_lab.automation.ocp4_workload_konflux_tssc_tenant
  - agnosticd.showroom.ocp4_workload_showroom
```

---

## Module 01: What Students Get

When students open the lab, they have:

✅ **Cluster-Wide Services**:
- Konflux UI at `{konflux_ui_url}`
- GitLab at `{gitlab_url}`
- Quay at `{quay_url}`
- Keycloak at `{keycloak_url}`
- RHTAS Fulcio/Rekor/TUF running

✅ **Per-User Resources**:
- Two namespaces: `user-{guid}-tenant`, `user-{guid}-managed`
- GitLab user with `sample-component-golang` repo imported
- Quay user with push credentials in namespace Secrets
- OpenShift HTPasswd user
- RoleBindings granting Konflux permissions
- Showroom lab guide with all variables substituted

❌ **Students Do NOT Get** (they create these):
- Konflux Applications
- Konflux Components
- Konflux ReleasePlans
- Any PipelineRuns

**Module 01 is pure verification** - students click links, confirm access, read intro content.

---

## What Students Do Per Module

| Module | Student Actions | Pre-Configured Infrastructure |
|--------|----------------|-------------------------------|
| 01 | Verify access to GitLab, Quay, Konflux UI | Everything from above |
| 02 | Create Application + Component via UI | GitLab repo, Quay credentials, RBAC |
| 03 | Push code, watch build | Konflux auto-creates pipeline |
| 04 | Run `cosign verify` | Tekton Chains auto-signs builds |
| 05 | View policy results | IntegrationTestScenario auto-created |
| 06 | Create Release | ReleasePlan created by student in Module 02 |
| 07 | Break things, diagnose | All previous infrastructure working |

---

## File Checklist

| File | Lines | Status | Notes |
|------|-------|--------|-------|
| `automation/ansible/galaxy.yml` | 15 | ✅ Exists | Update version/dependencies |
| `automation/ansible/meta/runtime.yml` | 5 | ✅ Exists | Already correct |
| **Cluster role** `tasks/workload.yml` | 100 | ❌ Stub | Implement RBAC + URL collection |
| **Cluster role** `defaults/main.yml` | 10 | ✅ Empty | No defaults needed |
| **Tenant role** `tasks/workload.yml` | 150 | ❌ Stub | Orchestrate existing roles |
| **Tenant role** `defaults/main.yml` | 15 | ✅ Partial | Already has user/namespace vars |
| **Tenant role** `templates/rolebinding-admin.yaml.j2` | 15 | ✅ Exists | Can be used inline instead |
| `qa-automation/healthcheck.yml` | 100 | ❌ Empty | Verify all components running |
| `qa-automation/e2e.yml` | 300 | ❌ Empty | Full workflow test |
| AgnosticV cluster `common.yaml` | 200 | ❌ N/A | Copy from LB1353 |
| AgnosticV tenant `common.yaml` | 150 | ❌ N/A | Copy from LB1353 |

---

## Implementation Order

1. ✅ **Automation manifest** - Already complete
2. ✅ **Implementation plan** - Already complete
3. **Cluster workload role** (2-3 hours)
   - Create ClusterRole
   - Collect URLs
   - Test on live cluster
4. **Tenant workload role** (3-4 hours)
   - Orchestrate existing roles
   - Test with 1 user
5. **AgnosticV catalog items** (2-3 hours)
   - Copy LB1353 structure
   - Update workload lists
6. **Health check playbook** (1-2 hours)
7. **E2E test playbook** (4-6 hours)
8. **Multi-user testing** (8-12 hours)

**Total Effort**: 20-30 hours

---

## Key References

- **LB1353 Cluster**: https://github.com/rhpds/agnosticv/tree/master/rh1-2027/lb1353-konflux-tsf-tssc-cnv-cluster
- **LB1353 Tenant**: https://github.com/rhpds/agnosticv/tree/master/rh1-2027/lb1353-konflux-tsf-tssc-cnv-tenant
- **TSF Role**: https://github.com/rhpds/rhpds.ads/tree/main/roles/ocp4_workload_trusted_software_factory
- **Namespaced Workloads**: https://github.com/rhpds/namespaced_workloads
- **Implementation Plan**: `publishing-house/spec/implementation-plan.md`

---

**Ready to implement? Start with Phase 2 in the implementation plan.**
