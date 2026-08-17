# Module Outline: Module 01 — Orientation

---

### Brief Overview

This module introduces participants to the lab scenario, the software supply chain security problem being solved, and the pre-provisioned environment they will work in throughout the lab. Participants tour the cluster-wide tools — Konflux, GitLab, Red Hat Quay, and Red Hat Trusted Artifact Signer — and confirm that their personal resources (GitLab repository, Quay organization, and Konflux workspace) are accessible before any hands-on steps begin. The module sets the conceptual frame (SLSA, SBOMs, image signing, provenance attestations) at the level needed to follow subsequent exercises without prior knowledge. By the end, every participant knows where they are starting, what they will build toward, and why supply chain security controls matter.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers, and security-minded practitioners — all with intermediate OpenShift/Kubernetes and Git skills.
- **Prerequisites for this module:** Access credentials provided by the lab instructor; a working browser session on the shared cluster.
- **Estimated duration:** 10 minutes

### Learning Objectives

- Explore the pre-provisioned lab environment and locate your personal GitLab repository, Quay organization, and Konflux workspace.
- Demonstrate an understanding of the software supply chain problem this lab addresses by identifying the gap between "image is built" and "image is trusted."
- Identify the role each tool plays in the end-to-end supply chain: Konflux (build and release orchestration), GitLab (source and merge-request-based triggers), Red Hat Quay (image registry), and Red Hat Trusted Artifact Signer with Rekor (signing and transparency log).

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | The Supply Chain Security Problem | 3 min |
| 2 | Tour the Lab Environment | 4 min |
| 3 | Verify Your Personal Resources | 3 min |

### Detailed Steps

**Section 1 — The Supply Chain Security Problem**

1. Read the introductory narrative in the lab guide explaining what a software supply chain attack looks like and why building an image is not enough.
2. Review the diagram showing the full artifact lifecycle: source commit → build → sign → attest → policy check → release to production.
3. Note the three guarantees the lab will demonstrate: (a) the image was built from a known commit, (b) no unauthorized party altered it after the build, and (c) it passed policy checks before reaching production.

**Section 2 — Tour the Lab Environment**

4. Open the Konflux web UI URL provided in the lab guide. Confirm the login page loads.
5. Log in with the credentials provided on your lab card or by the instructor.
6. Navigate to your Konflux workspace (named after your assigned user ID). Confirm you land on the Applications overview page.
7. Open the GitLab URL in a new browser tab. Log in with your GitLab credentials.
8. Locate the pre-provisioned sample application repository under your GitLab user or group. Note the repository URL — you will use it in Module 2.
9. Open the Red Hat Quay URL in a new browser tab. Log in with your Quay credentials.
10. Confirm your pre-provisioned Quay organization is listed on the dashboard. Note the organization name.
11. Open the Red Hat Trusted Artifact Signer (Rekor) URL if provided in the lab guide and confirm the transparency log UI loads.

**Section 3 — Verify Your Personal Resources**

12. In a terminal, log in to the OpenShift cluster using the `oc login` command and the token from the lab guide.
13. Run `oc whoami` and confirm your user identity matches your assigned lab user.
14. Run `oc project` to confirm you are in your pre-provisioned tenant namespace.
15. Run `oc get all -n <your-tenant-namespace>` and observe that the namespace is pre-populated with the expected resources (confirm no errors).
16. Return to the Konflux UI. Confirm the workspace is associated with your tenant namespace.
17. Verify that a ReleasePlan object exists in your tenant namespace by running `oc get releaseplan -n <your-tenant-namespace>` — you should see one entry.
18. Confirm readiness: all four services (Konflux, GitLab, Quay, Trusted Artifact Signer) are reachable and your personal resources are present. Flag any issues to the instructor before proceeding.

### Key Takeaways

- A container image built without signing and attestation cannot be trusted at deploy time — anyone can claim it came from a known source.
- SLSA (Supply Chain Levels for Software Artifacts) defines a framework for proving build provenance; this lab targets SLSA Level 3.
- SBOMs (Software Bills of Materials) enumerate the dependencies inside an image, enabling vulnerability tracking and compliance reporting.
- Sigstore and Red Hat Trusted Artifact Signer provide the cryptographic infrastructure for image signing and a tamper-evident transparency log (Rekor).
- Konflux orchestrates the full build-sign-attest-release pipeline and enforces Conforma policy checks before promotion.
- Each participant's resources are fully isolated in a tenant namespace — actions in one namespace do not affect others.

### Infrastructure Notes

- Tenant namespace, GitLab repository, Quay organization, Konflux workspace, and ReleasePlan are all pre-provisioned by lab automation before participants arrive. No setup steps are required in this module beyond verification.
- The ReleasePlanAdmission lives in a separate managed namespace, also pre-provisioned. Participants do not interact with it directly until Module 6.
- If a participant cannot reach the Konflux, GitLab, Quay, or Trusted Artifact Signer UI, this must be resolved before Module 2 — the remaining modules depend on all four services.
