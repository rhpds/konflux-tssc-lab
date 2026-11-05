# Module Outline: Module 07 — Real-World Incident Response

---

### Brief Overview

With the full happy-path supply chain complete, this module demonstrates what it is actually protecting against — two scenarios, the exact failure output each one produces, and a set of verification commands participants can take back to their own projects. Each scenario is self-contained: participants observe the failure signal, understand which cryptographic control caught the problem, and see why the block is permanent. By the end, participants can articulate what the supply chain enforces and what a customer would see when something goes wrong.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers, consultants, and sales specialists who need to demonstrate or explain supply chain security failures to customers.
- **Prerequisites for this module:** Module 06 completed; a successful release is present in the production Quay registry; participant is familiar with the Conforma output format and `cosign` CLI from Modules 04–05.
- **Estimated duration:** 15 minutes

### Learning Objectives

- Identify how Conforma detects and blocks an unsigned image pushed outside the Konflux pipeline, and explain the failure signals a customer would see.
- Observe how any byte-level change to a production image breaks its cosign signature, and explain why the check is digest-bound and cannot be bypassed by retaining the original tag.

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | Scenario A — Image Pushed Outside Konflux | 7 min |
| 2 | Scenario B — Modified Production Image | 5 min |
| 3 | Verification Commands Reference | 3 min |

### Detailed Steps

**Section 1 — Scenario A: Pushing an Image Outside Konflux**

*Scenario:* A developer needs to ship a critical fix immediately. They build the image locally and push it straight to the Quay registry, skipping Konflux. No pipeline ran, so no signing step ran, no SBOM was generated, and no SLSA provenance was recorded.

1. Read the scenario description in the lab guide. Note that from the outside the image looks fine — right organization, plausible tag, ready to pull. The supply chain does not look at the tag; it checks cryptographic evidence attached to the image digest.
2. Log in to the lab Quay registry and copy a public image directly into your namespace using `skopeo copy` to simulate the out-of-band push:
   ```
   QUAY_HOST=$(echo {quay_url} | sed 's|https://||')
   skopeo login "$QUAY_HOST" --username {openshift_username} --password "$(oc whoami -t)"
   skopeo copy docker://registry.access.redhat.com/ubi9/ubi-minimal:latest \
     "docker://$QUAY_HOST/{openshift_username}/my-sample-app:hotfix-unsigned"
   HOTFIX_IMAGE="$QUAY_HOST/{openshift_username}/my-sample-app:hotfix-unsigned"
   ```
3. Run `cosign verify` against the hotfix image. Observe the error — no signatures found — because no Tekton Chains signing task ever ran.
4. Run `cosign download attestation` and confirm it returns zero attestations: no SBOM, no SLSA provenance.
5. Run `ec validate image` with the IntegrationTestScenario policy. In the output, identify the two blocking violations:
   - `builtin.attestation.signature_check` — no valid signature
   - `builtin.provenance.slsa_provenance_available` — no SLSA provenance from a trusted builder
6. Note that the block is permanent: there is no way to add a valid Konflux signature or SLSA attestation to an image after it has been pushed outside the pipeline. A manual `cosign sign` produces a signature tied to a personal OIDC identity — not the Tekton Chains service account — and `cosign verify --certificate-identity-regexp 'https://konflux.*'` will still fail.

**Section 2 — Scenario B: What a Tampered Production Image Looks Like**

*Scenario:* Any byte-level change to a signed image — swapping a binary, adding a layer, changing a label — changes its SHA-256 digest. The cosign signature was recorded for the original digest; no valid signature exists for the new digest.

7. Read the explanation of how cosign stores signatures: as a separate OCI artifact whose tag encodes the SHA-256 digest of the image it signs. Any modification produces a new digest that maps to a tag that does not exist.
8. Confirm that the production image from Module 06 still passes:
   ```
   cosign verify --certificate-identity-regexp 'https://konflux.*' \
     --certificate-oidc-issuer {tas_oidc_issuer} "$PROD_IMAGE"
   ```
   Expected: `Verified OK`
9. Run the same `cosign verify` command against an image that was not built by Konflux (e.g., `registry.access.redhat.com/ubi9/ubi-minimal:latest`). Observe the same error output as Scenario A.
10. Note that `cosign verify` exits non-zero whether the image was never signed, was signed by the wrong builder, or was modified after signing — making it straightforward to gate on in a CI pipeline or Kubernetes admission controller without parsing the output.

**Section 3 — Verification Commands Reference**

11. Review the four portable commands that work against any image in any OCI-compatible registry where the Sigstore toolchain is installed:
    - `cosign verify` — checks the cryptographic signature against the expected builder certificate identity
    - `cosign download attestation | jq 'length'` — counts SBOM and SLSA provenance attestations
    - `cosign download attestation | jq '.[0].payload | @base64d | fromjson | {type: .predicateType, builder: .predicate.runDetails.builder.id}'` — extracts the SLSA predicate type and builder identity
    - `ec validate image --output json | jq '.components[].violations'` — full policy evaluation including signature, provenance, SBOM, and custom org rules
12. Note the substitution variables needed for each command: `<regexp>` for the builder identity pattern, `<issuer>` for the Trusted Artifact Signer Keycloak realm, and `POLICY` for the OCI bundle ref.

### Key Takeaways

- **An image pushed outside Konflux is permanently blocked.** The signing certificate is issued to the Tekton Chains service account identity — an identity that only exists inside a running Konflux pipeline. There is no approved path for out-of-band pushes to reach production.
- **Signatures are digest-bound.** Any byte-level change to an image produces a new SHA-256 digest, and no valid signature exists for that new digest. The check does not depend on tag names or registry location.
- **`cosign verify` exits non-zero on any failure.** A single line in a deployment script or a Kubernetes admission policy is enough to enforce the control without custom parsing logic.

### Infrastructure Notes

- Scenario A uses `skopeo copy` to pull a public image from `registry.access.redhat.com` and push it into the participant's Quay namespace — no pre-provisioned bad image is required.
- Scenario B uses the participant's own production image from Module 06 and an arbitrary public image to demonstrate the tamper-detection behavior — no pre-provisioned bad image is required.
- Both scenarios require `skopeo`, `cosign`, and the `ec` CLI to be available in the terminal; these are pre-installed in the lab environment.
- The Rekor/TAS OIDC issuer URL (`{tas_oidc_issuer}`) must be set in `antora.yml` attributes or provided in the lab guide.
