# Module Outline: Module 03 — Build and Scan

---

### Brief Overview

With the application onboarded, this module takes participants deep into what the Konflux build pipeline actually produces. Participants trigger a fresh pipeline run by pushing a small code change to GitLab, then trace the pipeline stages in the Konflux UI to understand how the image is built, vulnerability-scanned, and accompanied by an automatically generated Software Bill of Materials (SBOM) in CycloneDX format. The goal is to make the SBOM concrete — participants open the file, identify its sections, and understand what downstream consumers (policy engines, security teams) do with it. By the end of the module participants can articulate what artifact the pipeline produces and where each output artifact lands in Quay.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers, security-minded practitioners.
- **Prerequisites for this module:** Module 02 completed; a PipelineRun has succeeded at least once; participant is logged in to Konflux, GitLab, Quay, and the OpenShift cluster.
- **Estimated duration:** 20 minutes

### Learning Objectives

- Build a container image by pushing a source change to GitLab and observing the resulting Konflux PipelineRun.
- Analyze the automatically generated CycloneDX SBOM to identify its components, licenses, and vulnerability data.
- Observe how the pipeline scan tasks report findings and how results surface in the Konflux UI.
- Verify that the built image and its associated SBOM and attestation artifacts are present in the Quay registry after the pipeline completes.

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | Trigger a Build with a Code Change | 5 min |
| 2 | Trace the Pipeline Stages | 7 min |
| 3 | Inspect the SBOM | 5 min |
| 4 | Review Scan Results and Quay Artifacts | 3 min |

### Detailed Steps

**Section 1 — Trigger a Build with a Code Change**

1. In the GitLab browser tab, navigate to your sample application repository.
2. Open the file `README.md` (or another non-functional file in the repository root) using the GitLab web editor.
3. Add a comment line at the bottom: `# Lab update - module 03` and commit directly to the default branch with the commit message `chore: trigger module-03 build`.
4. Confirm the commit appears in the repository's commit history.
5. Switch to the Konflux UI and navigate to **Pipelines** (or **Activity**) for your Application.
6. Observe that a new PipelineRun appears within 30–60 seconds, triggered by the push event. Note the PipelineRun name and start time.

**Section 2 — Trace the Pipeline Stages**

7. Click the new PipelineRun to open its detail view.
8. Identify and read the purpose of each pipeline task listed. The Konflux default build pipeline includes tasks such as:
   - `init` — sets up workspace and input validation
   - `clone-repository` — fetches the source from GitLab
   - `build-container` — builds the OCI image using Buildah
   - `build-image-index` — creates a multi-arch image index (if applicable)
   - `clair-scan` or equivalent vulnerability scan task
   - `sast-snyk-check` or equivalent static analysis task
   - `generate-sbom` — generates the CycloneDX SBOM
   - `push-dockerfile` — pushes the Dockerfile to the image registry for provenance
   - `apply-tags` — applies version and latest tags to the image
9. Wait for the `build-container` task to complete. Expand its log output in the UI and find the line that shows the image digest (e.g., `sha256:...`). Copy the digest — you will use it in later modules.
10. Wait for the full PipelineRun to reach **Succeeded**. If any task fails with a non-zero exit code, expand the failing task's log and read the error. Report critical failures to the instructor.
11. In the terminal, run `oc get pipelineruns -n <your-tenant-namespace>` and confirm the latest PipelineRun shows `SUCCEEDED`.

**Section 3 — Inspect the SBOM**

12. With the image digest from step 9, use `cosign` in the terminal to download the SBOM attestation attached to the image:
    ```
    cosign download attestation \
      quay.<cluster-domain>/<your-quay-org>/sample-app@sha256:<digest> \
      | jq -r '.payload' | base64 -d | jq .
    ```
13. In the JSON output, locate the `subject` field and confirm it references the image digest from step 9.
14. Locate the `predicate.components` array (CycloneDX format). Count the number of components listed. These are the packages included in the image.
15. Pick any component from the list. Identify its `name`, `version`, and `licenses` fields.
16. Look for any components flagged with known CVEs (the predicate may include vulnerability information or reference an external vulnerability report). Note whether any high-severity issues are present.
17. Observe that the SBOM is machine-readable and structured — this is the format that Conforma and external security tooling consume in later modules.

**Section 4 — Review Scan Results and Quay Artifacts**

18. In the Konflux UI, navigate to the **Vulnerabilities** or **Security** tab for the Component (if available). Confirm scan results are displayed.
19. In the Quay browser tab, navigate to your Quay organization and find the `sample-app` repository.
20. Confirm the newly built image tag (e.g., `latest` or a SHA-based tag) is listed with a push time matching your recent build.
21. In Quay, click the image tag and inspect the **Tags** or **Security Scan** tab. Confirm the vulnerability scan results are visible.
22. Note that multiple tags or manifests may exist: the container image itself, the SBOM attestation, and the SLSA provenance attestation. Identify each by its media type or tag name (e.g., tags ending in `.att` or `.sbom`). You will examine the provenance attestation in Module 4.

### Key Takeaways

- The Konflux build pipeline runs entirely in-cluster on OpenShift Pipelines (Tekton) — no external CI system is required.
- Every successful build automatically produces three artifacts pushed to Quay: the container image, a CycloneDX SBOM, and a SLSA provenance attestation.
- CycloneDX SBOMs enumerate all packages in the image, enabling security teams to detect vulnerable dependencies without re-scanning the image from scratch.
- Vulnerability scan tasks run inside the pipeline before the image is promoted, giving developers early feedback on security posture.
- The image digest is immutable — it uniquely identifies a specific image content and is the reference used for signing and policy checks in later modules.
- Pipelines-as-Code makes build triggers automatic and auditable: every build can be traced back to the exact source commit that triggered it.

### Infrastructure Notes

- The `cosign` CLI must be available in the participant's terminal. Confirm with `cosign version`. If not present, the lab guide should provide the download URL or the tool should be pre-installed on the bastion or web terminal.
- The Quay registry must be reachable from the participant's terminal for `cosign download` to work. If TLS certificates are self-signed, participants may need to set `COSIGN_INSECURE_SKIP_TLS_VERIFY=true` or install the cluster CA — the lab guide should specify which.
- The Konflux default pipeline may vary by cluster version. Writers should confirm the exact task names visible in the lab environment and update step 8 accordingly.
- SBOM generation in Konflux uses `syft` internally; the output format is CycloneDX JSON. Writers should confirm the exact `cosign download attestation` payload structure in the lab environment and update the `jq` filter in step 12 if needed.
