# Module Outline: Module 06 — Release to Production

---

### Brief Overview

This final module completes the end-to-end supply chain by releasing the policy-verified, signed artifact to a production Quay registry through Konflux's controlled release pipeline. Participants trigger a release using the pre-provisioned ReleasePlan, watch the release pipeline enforce a final round of policy checks, and then confirm the signed image is present in the production registry. The module closes by stepping back across all six modules to articulate the full supply chain guarantee: from source commit to signed, provenance-attested, policy-gated production artifact — every step is automated, cryptographically verifiable, and auditable.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers, security-minded practitioners.
- **Prerequisites for this module:** Module 05 completed; the Snapshot from Module 03 is in a passing state; participant is logged in to Konflux, Quay, and the OpenShift cluster.
- **Estimated duration:** 15 minutes

### Learning Objectives

- Configure and trigger a Konflux ReleasePlan to initiate the controlled release pipeline for a policy-passing Snapshot.
- Verify that the release pipeline re-evaluates the Conforma policy before promoting the artifact to the production Quay registry.
- Verify the signed image and its attestations are present in the production Quay organization after a successful release.
- Demonstrate end-to-end supply chain integrity by tracing the artifact from the source commit through signing, policy validation, and production release.

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | Review the ReleasePlan and ReleasePlanAdmission | 4 min |
| 2 | Trigger the Release | 4 min |
| 3 | Monitor the Release Pipeline | 4 min |
| 4 | Verify the Production Artifact and Supply Chain Summary | 3 min |

### Detailed Steps

**Section 1 — Review the ReleasePlan and ReleasePlanAdmission**

1. In the terminal, retrieve the ReleasePlan pre-provisioned in your tenant namespace:
   ```
   oc get releaseplan -n <your-tenant-namespace> -o yaml
   ```
2. In the output, identify the following fields:
   - `spec.application` — the Konflux Application name (should match the Application you created in Module 02).
   - `spec.target` — the managed namespace where the ReleasePlanAdmission lives.
   - `spec.releaseGracePeriodDays` — if present, the number of days before auto-release; in the lab this may be set to 0 for immediate triggering.
3. Retrieve the ReleasePlanAdmission from the managed namespace:
   ```
   oc get releaseplanadmission -n <managed-namespace> -o yaml
   ```
   The managed namespace name is provided in the lab guide.
4. In the ReleasePlanAdmission output, identify:
   - `spec.applications` — the list of Applications allowed to release through this admission (confirm your Application is listed or matches the selector).
   - `spec.policy` — the Conforma policy bundle reference that will be enforced during release.
   - `spec.pipeline` — the release pipeline that will run (includes the final EC check and the Quay push steps).
   - `spec.environment` — if present, the target environment configuration (production Quay organization and repository).
5. Confirm that the `spec.policy` in the ReleasePlanAdmission references the same (or stricter) policy bundle as the one evaluated in Module 05. The release pipeline cannot be weaker than the integration check.

**Section 2 — Trigger the Release**

6. In the Konflux UI, navigate to your Application, then to the **Releases** tab (or equivalent navigation — the lab guide provides a screenshot).
7. Locate the Snapshot from your Module 03 build (identified by its name and the associated image digest). Confirm its status is **Passing** or **Eligible for release**.
8. Click **Create release** (or equivalent action) for that Snapshot. If the UI prompts you to select a ReleasePlan, choose the one pre-provisioned in your tenant namespace.
9. Confirm the release creation in the UI. A Release object will be created in your tenant namespace.
10. In the terminal, verify the Release object was created:
    ```
    oc get release -n <your-tenant-namespace>
    ```
    Note the Release name and observe its `STATUS` field — it will begin as `Running` or `Progressing`.

**Section 3 — Monitor the Release Pipeline**

11. In the Konflux UI, click the Release to open its detail view. Observe the release pipeline stages. The release pipeline typically includes:
    - An Conforma evaluation task (re-validates the signed artifact against the production policy).
    - A task that pushes the image (and its SBOM and provenance attestation) to the production Quay organization.
    - A task that records the release event (may write to a release log or update the Snapshot status).
12. Wait for the Conforma task to complete. In the task logs, confirm the result is **Pass**. If it fails, the pipeline will stop and the image will not be pushed to production — observe the failure message and note which policy rule blocked the release.
13. Wait for the image push task to complete. In its logs, find the line showing the production image reference (the Quay URL and digest of the promoted image). Copy this reference.
14. Monitor the full release pipeline until it reaches **Succeeded**.
15. In the terminal, run:
    ```
    oc get release <release-name> -n <your-tenant-namespace> -o yaml | grep -A10 'status:'
    ```
    Confirm the `status.conditions` include a condition with `type: Released` and `status: True`.

**Section 4 — Verify the Production Artifact and Supply Chain Summary**

16. In the Quay browser tab, navigate to the production Quay organization (the organization configured in the ReleasePlanAdmission — the lab guide specifies the URL).
17. Find the image repository and locate the newly released image tag. Confirm the push timestamp matches the release pipeline execution time.
18. Click the image tag and navigate to the **Security Scan** or **Tags** view. Confirm the image is the same digest as the one built in Module 03 (the digest should be identical — no re-build occurred, only promotion).
19. Use `cosign verify` in the terminal to verify the signature on the production image, using the same command as Module 04 but pointing to the production Quay reference:
    ```
    cosign verify \
      --certificate-identity-regexp "https://konflux.*" \
      --certificate-oidc-issuer "<cluster-oidc-issuer>" \
      "quay.<cluster-domain>/<prod-quay-org>/sample-app@sha256:<digest>"
    ```
    Confirm that `Verified OK` is returned. The signature travels with the image digest.
20. Use `cosign download attestation` to confirm the SLSA provenance attestation is also present on the production image reference. The attestation should be identical to the one inspected in Module 04 — it was signed once during the build and promoted alongside the image.
21. Review the end-to-end chain:
    - **Source commit** (Module 02 — GitLab push) → uniquely referenced in the SLSA attestation.
    - **Build** (Module 03 — Konflux PipelineRun) → produced the image digest and SBOM.
    - **Sign and attest** (Module 04 — Trusted Artifact Signer + Rekor) → cryptographic signature and transparency log entry.
    - **Policy check** (Module 05 — Conforma) → Snapshot marked as passing.
    - **Release** (Module 06 — ReleasePlan + release pipeline) → image promoted to production with all attestations intact.
22. Confirm that every step is traceable: given only the production image digest, you can retrieve the SLSA provenance to find the source commit, the build PipelineRun, the signing event in Rekor, and the policy evaluation that approved the release.

### Key Takeaways

- The ReleasePlan/ReleasePlanAdmission model separates the teams that request a release (Application team, tenant namespace) from the teams that govern release policy (platform/security team, managed namespace) — no single team controls both sides of the gate.
- The release pipeline re-evaluates Conforma policy at release time — it does not trust the integration-time result. This prevents a scenario where policy changes between build and release.
- Image promotion does not re-build the image — the same immutable digest built and signed in Module 03 is what reaches production. There is no "release build" that could introduce differences.
- Attestations (SBOM, SLSA provenance) travel with the image because they are stored in the same Quay repository keyed to the same digest. Promoting the image also promotes its entire evidence package.
- End-to-end traceability is the core value proposition: starting from a production image digest, any authorized party can reconstruct the full supply chain history without relying on a central database.
- The combination of SLSA, Sigstore, Conforma, and Konflux implements a complete software supply chain security framework aligned with SLSA Level 3 requirements and applicable to any team building on OpenShift.

### Infrastructure Notes

- The managed namespace (containing the ReleasePlanAdmission) is pre-provisioned and participants do not have write access to it — by design. The managed namespace is controlled by a platform team persona. Writers should make this access boundary explicit in the lab guide to set the right expectations.
- The production Quay organization is separate from the participant's development Quay organization (used in Modules 03–05). Writers must confirm the exact production Quay org name and URL and substitute them into steps 16–20.
- The release pipeline reference in the ReleasePlanAdmission is cluster-specific. Writers must obtain the exact pipeline name and namespace from the lab environment and include it in the lab guide.
- If the release pipeline fails at the EC check step, the most likely cause is a clock skew issue (the attestation timestamp is outside the policy's acceptance window) or a policy bundle version mismatch. The lab administrator should document the expected policy bundle version and ensure it matches across IntegrationTestScenario and ReleasePlanAdmission.
- `cosign verify` in step 19 uses the same certificate identity and OIDC issuer as Module 04. Writers should confirm these values are documented in a single place in the lab guide (e.g., a reference appendix) so participants do not need to re-discover them.
