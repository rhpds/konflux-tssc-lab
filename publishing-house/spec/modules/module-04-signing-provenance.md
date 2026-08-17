# Module Outline: Module 04 — Signing and Provenance

---

### Brief Overview

This module focuses on the cryptographic guarantees that make a built image trustworthy after it leaves the build pipeline. Participants use `cosign` to verify the image signature created by Red Hat Trusted Artifact Signer, inspect the SLSA Level 3 provenance attestation to trace the image back to its source commit and build environment, and confirm the transparency log entry in Rekor. The module answers the question "how do I know this image is what it claims to be?" and establishes the evidence chain that Conforma policy checks will evaluate in Module 5.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers, security-minded practitioners.
- **Prerequisites for this module:** Module 03 completed; image digest from the successful PipelineRun noted; `cosign` CLI available in the terminal; logged in to the OpenShift cluster and Quay.
- **Estimated duration:** 15 minutes

### Learning Objectives

- Verify the cryptographic signature on the built container image using `cosign` and the Red Hat Trusted Artifact Signer public key.
- Analyze the SLSA Level 3 provenance attestation to confirm it references the correct source commit, build pipeline, and builder identity.
- Explore the Rekor transparency log entry to demonstrate that the signature event is tamper-evident and publicly auditable.
- Demonstrate the difference between an image that is signed with verifiable provenance and one that is not, and explain why this matters for supply chain security.

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | Verify the Image Signature | 5 min |
| 2 | Inspect the SLSA Provenance Attestation | 6 min |
| 3 | Explore the Rekor Transparency Log | 4 min |

### Detailed Steps

**Section 1 — Verify the Image Signature**

1. In the terminal, set an environment variable for the image reference using the digest noted in Module 03:
   ```
   IMAGE="quay.<cluster-domain>/<your-quay-org>/sample-app@sha256:<digest>"
   ```
2. Retrieve the Red Hat Trusted Artifact Signer public key or certificate chain. The lab guide provides the path or URL — set it as a variable:
   ```
   SIGSTORE_ROOT_CERT="<path-or-url-to-cluster-root-cert>"
   ```
3. Run `cosign verify` against the image, providing the certificate identity and OIDC issuer that match the Konflux builder service account:
   ```
   cosign verify \
     --certificate-identity-regexp "https://konflux.*" \
     --certificate-oidc-issuer "<cluster-oidc-issuer>" \
     "$IMAGE"
   ```
   The exact flags and values are provided in the lab guide for the specific cluster configuration.
4. Observe the output. A successful verification prints the certificate subject, issuer, and the image digest. Confirm the subject matches the Konflux pipeline service account identity.
5. Note the statement `Verified OK` (or equivalent) in the output. This confirms: (a) the signature exists, (b) it was made by the expected identity, and (c) it has not been tampered with.
6. Optionally, run `cosign verify` against a random public image from Docker Hub (e.g., `docker.io/library/nginx`) to observe the failure — that image is not signed by Trusted Artifact Signer and will not verify.

**Section 2 — Inspect the SLSA Provenance Attestation**

7. Download the SLSA provenance attestation using `cosign`:
   ```
   cosign download attestation "$IMAGE" \
     | jq -r 'select(.payload) | .payload' | base64 -d | jq .
   ```
8. In the JSON output, locate the `predicateType` field. Confirm it is set to `https://slsa.dev/provenance/v1` (SLSA v1) or `https://slsa.dev/provenance/v0.2` depending on the cluster version.
9. Locate the `subject` array. Confirm the `digest.sha256` value matches your image digest.
10. Locate the `predicate.buildDefinition.resolvedDependencies` or `predicate.materials` section (depending on SLSA version). Find the entry that references your GitLab repository and note the `sha1` or `digest` value — this is the exact source commit the image was built from.
11. Open your GitLab repository in the browser. Navigate to the commit history and confirm that the commit SHA from step 10 matches the commit you pushed in Module 03.
12. Locate the `predicate.runDetails.builder.id` or `predicate.builder.id` field. Confirm it identifies the Konflux builder running on your OpenShift cluster (the lab guide specifies the expected value).
13. Locate the `predicate.runDetails.metadata.invocationId` or `predicate.metadata.buildInvocationId`. This is the unique identifier for the specific PipelineRun that produced the image. Cross-reference it with the PipelineRun name you observed in Module 03.
14. Summarize what the provenance attestation proves: a specific builder running on a trusted platform took specific source code at a known commit and produced this exact image digest.

**Section 3 — Explore the Rekor Transparency Log**

15. Retrieve the Rekor log entry for the image signature. Use the `rekor-cli` tool or `cosign triangulate` to find the log entry:
    ```
    rekor-cli search --sha "sha256:<digest>" \
      --rekor_server "https://rekor.<cluster-domain>"
    ```
    The lab guide provides the exact Rekor server URL.
16. From the search results, copy the log entry UUID.
17. Retrieve the full log entry:
    ```
    rekor-cli get --uuid "<uuid>" --rekor_server "https://rekor.<cluster-domain>"
    ```
18. In the output, locate the `logIndex` (a monotonically increasing integer), the `integratedTime` (the timestamp when the entry was added), and the `body` (the signed payload encoded in base64). Confirm the `integratedTime` is close to when your PipelineRun completed.
19. Open the Rekor UI in the browser (URL provided in the lab guide). Search for the same log entry by UUID or image digest and confirm the entry is visible in the web interface.
20. Observe that the log entry is append-only — entries cannot be deleted or modified. This is what "tamper-evident" means in the context of supply chain security.

### Key Takeaways

- Image signing with cosign and Trusted Artifact Signer produces a cryptographic signature tied to the build identity (OIDC-based Sigstore signing — no long-lived keys to manage).
- SLSA Level 3 provenance attestations provide a machine-verifiable record of what was built, by whom, from what source, and in what build environment.
- The Rekor transparency log creates an immutable, auditable record of every signing event — even if an attacker compromises the registry, the log entry proves the original state.
- The combination of image signature + provenance attestation + transparency log entry gives downstream consumers (policy engines, platform engineers, auditors) the evidence they need to decide whether to trust an image.
- `cosign verify` is the primary tool for consuming this evidence; Conforma (Module 5) automates this verification at scale with policy-encoded rules.

### Infrastructure Notes

- Red Hat Trusted Artifact Signer is self-hosted in the lab cluster. The Rekor server URL, OIDC issuer, and certificate chain are cluster-specific — writers must substitute real values from the lab environment into step 2 and step 3 command examples.
- `rekor-cli` must be available in the participant's terminal. If not pre-installed, the lab guide must provide a download URL or alias. Alternatively, the `cosign` CLI can retrieve transparency log entries via `cosign verify --output json` — writers should confirm which tool is available and simplify accordingly.
- Keyless signing via Sigstore short-lived certificates (Fulcio) is the expected signing method. Writers must confirm whether the lab uses keyless signing or a static key pair — the `cosign verify` flags differ significantly between the two modes.
- SLSA predicate schema differs between v0.2 and v1. Writers must run the `cosign download attestation | jq` command against the actual cluster output to confirm field names and adjust steps 8–13 to match the exact schema in use.
