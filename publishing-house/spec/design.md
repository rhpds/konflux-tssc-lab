# Build, Sign, and Ship: Securing the Software Supply Chain with Konflux

## Overview

This lab teaches developers and platform engineers how modern software supply chains enforce provenance, signing, and policy-gated releases using Konflux and Red Hat's supply chain security tooling. It exists because teams adopting SLSA and Sigstore practices have few hands-on resources that show the full lifecycle end to end.

Participants onboard a real application from a pre-provisioned GitLab repository into Konflux, trigger automated builds via Pipelines-as-Code, inspect the generated SBOMs and SLSA Level 3 provenance attestations, verify cryptographic signatures using cosign and Trusted Artifact Signer, gate a release with Conforma policy checks, and promote a signed artifact to a production Quay registry — all in an isolated tenant namespace on a shared cluster.

## Target Audience

- **Role:** Application developers and DevOps engineers building on OpenShift; platform engineers evaluating supply chain security tooling; security-minded practitioners adopting SLSA and Sigstore practices
- **Experience level:** Intermediate
- **What they already know:** OpenShift/Kubernetes at an intermediate level (namespaces, pods, routes, oc CLI); Git basics (clone, commit, push, merge requests); container image fundamentals (registries, tags, builds); CI/CD pipeline concepts
- **What they don't know:** Supply chain security concepts (SLSA, SBOM, image signing, provenance attestations) — the lab teaches this from zero

## Prerequisites

- Comfortable with OpenShift/Kubernetes: namespaces, pods, routes, and the `oc` CLI
- Basic Git skills: clone, commit, push, and open merge requests
- Basic container image knowledge: registries, tags, and what a build produces
- Familiarity with CI/CD pipeline concepts (triggers, stages, artifacts)
- No supply chain security knowledge required — SLSA, SBOMs, and signing are introduced in the lab
- Can the lab validate these automatically? No — trust-based. Participants are expected to arrive with the stated skills; the lab does not gate entry with automated checks.

## Learning Objectives

1. Configure an application in Konflux and connect it to automated Pipelines-as-Code builds triggered from GitLab
2. Build a container image and analyze the SBOM in CycloneDX format generated automatically by the Konflux pipeline
3. Verify cryptographic image signatures and SLSA Level 3 provenance attestations using cosign and Trusted Artifact Signer
4. Analyze Conforma policy checks and observe how failed checks block artifact promotion between environments
5. Deploy a policy-verified, signed artifact through a controlled release pipeline to a production Quay registry
6. Verify end-to-end supply chain integrity from source commit to signed, provenance-attested production release

## Content Type

Lab (hands-on)

## Products & Technologies

Red Hat products:
- Red Hat OpenShift Container Platform
- Red Hat Trusted Artifact Signer (includes Rekor transparency log, self-hosted)
- Red Hat Quay (self-hosted)
- Red Hat OpenShift Pipelines

Upstream projects (not GA Red Hat products):
- Konflux (upstream build and release platform)
- Conforma (upstream policy engine)
- GitLab (self-hosted, pre-installed in lab environment)
- cosign (Sigstore CLI tool, used in student exercises)

## Module Map

| Module | Title | Duration |
|--------|-------|----------|
| 1 | Orientation | 10 min |
| 2 | Onboard Your Application | 15 min |
| 3 | Build and Scan | 20 min |
| 4 | Signing and Provenance | 15 min |
| 5 | Integration Testing and Policy | 15 min |
| 6 | Release to Production | 15 min |
| — | **Total hands-on** | **90 min** |
| — | Intro / presentation | ~0 min (self-guided) |
| — | **Total lab** | **~90 min** |

## Difficulty Level

Intermediate

## Environment

**Learner view:** Each participant lands in a pre-provisioned isolated tenant namespace on a shared OpenShift cluster. Konflux, GitLab, Red Hat Quay, and Red Hat Trusted Artifact Signer are pre-installed cluster-wide. Each user has their own GitLab repository (with a sample application), a Quay organization, and a Konflux workspace. A managed namespace with a pre-configured ReleasePlanAdmission is also provisioned. No cluster-admin access is required.

**Automation needed:** Yes — per-user provisioning includes: tenant namespace, GitLab repository with sample app, Quay organization, Konflux workspace, ReleasePlan in the tenant namespace, ReleasePlanAdmission in the managed namespace.

## Infrastructure Requirements

- **Cloud provider:** CNV (default)
- **Cluster type:** Multinode
- **OCP version:** 4.20 (minimum)
- **Topology:** Shared cluster
- **Sizing:** 3 control plane (16 vCPU, 64GB RAM); 6 workers (16 vCPU, 64GB RAM, 200GB disk)
- **Automation approach:** Ansible
- **AI/MaaS:** None
- **External services:** registry.access.redhat.com, quay.io, github.com (Konflux release artifacts)
- **AAP version:** N/A
- **Non-GA products:** None (Konflux is an upstream community project, not a non-GA Red Hat product)

## Assessment Strategy

Trust-based — no automated solve/validate buttons. Each module closes with a visible outcome in the UI or terminal (e.g., pipeline completes, image appears in Quay, release status shows success). Participants self-verify by observing the stated outcome before moving to the next module.
