# Module Outline: Module 07 — Real-World Incident Response

---

### Brief Overview

With the full happy-path supply chain complete, this module intentionally breaks three trust mechanisms established in earlier modules to simulate real-world incidents that consultants and sales specialists will encounter in the field. Participants diagnose each failure using the same Konflux UI, CLI tools, and Conforma policy output they used throughout the lab — no new tooling, just adverse conditions. Each scenario is self-contained: participants break it, read the failure signals, and understand exactly which control caught the problem and why. By the end, participants can articulate what the supply chain enforces and what a customer would see when something goes wrong.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers, consultants, and sales specialists who need to demonstrate or explain supply chain security failures to customers.
- **Prerequisites for this module:** Module 06 completed; a successful release is present in the production Quay registry; participant is familiar with the Conforma output format and `cosign` CLI from Modules 04–05.
- **Estimated duration:** 25 minutes

### Learning Objectives

- Identify how Conforma detects and blocks an unsigned image pushed outside the Konflux pipeline, and explain the failure signals a customer would see.
- Diagnose a policy violation caused by a dependency CVE and trace which policy rule triggered the block.
- Observe how signature verification fails when a signing key or certificate identity does not match the expected trusted builder, and explain the config drift scenario this represents.
- Articulate, for each scenario, which layer of the supply chain caught the problem: build pipeline, integration policy, or release gate.

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | Scenario A — The Unsigned Hotfix | 8 min |
| 2 | Scenario B — The CVE Policy Breach | 10 min |
| 3 | Scenario C — Config Drift and Key Mismatch | 7 min |

### Detailed Steps

**Section 1 — Scenario A: The Unsigned Hotfix**

*Scenario:* A developer bypasses the Konflux pipeline during an incident and pushes an image directly to Quay. It is unsigned and has no SLSA attestation. They try to release it through the ReleasePlan.

1. Read the scenario description in the lab guide. Note that this simulates a hotfix pushed out-of-band — a common customer incident pattern.
2. The lab pre-provisions a "hotfix" image that was pushed directly to Quay without going through a Konflux PipelineRun. Set the image reference in your terminal:
   ```
   HOTFIX_IMAGE="quay.<cluster-domain>/lab-examples/unsigned-hotfix@sha256:<hotfix-digest>"
   ```
   The lab guide provides the exact image reference.
3. Attempt to verify the signature on the hotfix image:
   ```
   cosign verify \
     --certificate-identity-regexp "https://konflux.*" \
     --certificate-oidc-issuer "<cluster-oidc-issuer>" \
     "$HOTFIX_IMAGE"
   ```
4. Observe the error output. `cosign verify` will fail with a message indicating no valid signature was found. Note the exact error message — this is what a customer's security team would see.
5. Run the Conforma CLI validation against the hotfix image:
   ```
   ec validate image \
     --image "$HOTFIX_IMAGE" \
     --policy "<policy-bundle-ref>" \
     --output json | jq '.components[].violations[] | {rule: .metadata.code, msg: .msg}'
   ```
6. In the output, identify the specific policy rules that failed. Expect to see at least:
   - A rule requiring a valid image signature (`attestation_type.known_attestation_type` or equivalent)
   - A rule requiring a SLSA provenance attestation from a trusted builder
7. Confirm that the Conforma output `success` field is `false`. This is the signal that blocks the release pipeline.
8. Discuss: what would a customer need to do differently? (Answer: all images must be built through the Konflux pipeline — there is no approved path for out-of-band pushes to reach production.)

**Section 2 — Scenario B: The CVE Policy Breach**

*Scenario:* A new critical CVE is discovered in a base image dependency. The integration policy has been updated to block images with this CVE. An artifact that previously passed policy now fails on re-evaluation.

9. Read the scenario description in the lab guide. Note that this simulates a policy tightening event — the image did not change, but the policy did.
10. The lab provides a pre-built "vulnerable" image that contains a dependency with a known CVE. Set the image reference:
    ```
    CVE_IMAGE="quay.<cluster-domain>/lab-examples/cve-sample@sha256:<cve-digest>"
    ```
    The lab guide specifies the CVE identifier and the affected package.
11. Run the Conforma CLI against the CVE image:
    ```
    ec validate image \
      --image "$CVE_IMAGE" \
      --policy "<policy-bundle-ref>" \
      --output json | jq .
    ```
12. In the JSON output, locate the violations array. Identify the rule that flags the CVE — it will reference the CVE identifier in its `msg` field and will show the affected component name and version.
13. Note the `severity` field if present. A critical CVE should produce a blocking violation (not a warning).
14. In the Konflux UI, if a pre-created failing Snapshot using the CVE image is available, navigate to it. Observe how the Integration pipeline marks the Snapshot as blocked — it should show a failed integration test status and be ineligible for release.
15. In the terminal, check the Snapshot status:
    ```
    oc get snapshots -n <your-tenant-namespace> --sort-by=.metadata.creationTimestamp
    ```
    Identify the Snapshot associated with the CVE image. Confirm its conditions show a failed integration test.
16. Discuss: what would the customer remediation path be? (Answer: update the base image to a patched version, rebuild through Konflux, and the new Snapshot will be re-evaluated against the policy — if the CVE is resolved, the new artifact passes and becomes releasable.)

**Section 3 — Scenario C: Config Drift and Key Mismatch**

*Scenario:* A signing key rotation was performed on the cluster but the Conforma policy was not updated to trust the new key. Or: the policy bundle reference was changed to a version with a stricter certificate identity pattern that no longer matches the builder used in this cluster.

17. Read the scenario description in the lab guide. Note that this simulates a common operational mistake: infrastructure changes that are not reflected in policy configuration.
18. The lab provides a pre-built image that was signed with a key or certificate identity that does not match the policy's trusted signer configuration. Set the image reference:
    ```
    DRIFTED_IMAGE="quay.<cluster-domain>/lab-examples/key-drift@sha256:<drift-digest>"
    ```
19. Attempt to verify the signature using a mismatched certificate identity:
    ```
    cosign verify \
      --certificate-identity-regexp "https://different-builder.*" \
      --certificate-oidc-issuer "<cluster-oidc-issuer>" \
      "$DRIFTED_IMAGE"
    ```
    Observe that verification fails because the certificate identity in the signature does not match the expected pattern.
20. Now run the correct `cosign verify` command (using the cluster's actual trusted builder identity from Module 04). Observe that this also fails — the image was signed by an untrusted identity, so no valid match exists regardless of what identity you check against.
21. Run Conforma validation against the drifted image:
    ```
    ec validate image \
      --image "$DRIFTED_IMAGE" \
      --policy "<policy-bundle-ref>" \
      --output json | jq '.components[].violations[] | {rule: .metadata.code, msg: .msg}'
    ```
22. Identify the violation that flags the untrusted builder identity. The rule will indicate that the certificate identity in the SLSA attestation does not match the policy's allowed builder list.
23. In the Rekor transparency log, look up the signing event for the drifted image:
    ```
    cosign download attestation "$DRIFTED_IMAGE" \
      | jq -r '.payload' | base64 -d \
      | jq '.predicate.builder.id'
    ```
    Confirm the builder ID in the attestation does not match the trusted builder configured in the policy. This is the root cause — the image was built or signed outside the trusted pipeline.
24. Discuss: what would the remediation be? (Answer: rebuild the image through the correct Konflux pipeline so the builder identity in the attestation matches the policy's trusted signer list. If a key rotation caused the mismatch, the policy must also be updated to reflect the new certificate identity before new builds will pass.)

### Key Takeaways

- **The policy gate is the last line of defense.** All three scenarios show different failure modes, but in each case Conforma's evaluation was the mechanism that prevented a compromised or non-compliant artifact from reaching production.
- **Out-of-band pushes are permanently blocked.** An image built outside the Konflux pipeline has no valid SLSA attestation from a trusted builder and will always fail the signature and provenance policy rules — there is no way to retroactively add these.
- **Policy changes affect existing artifacts.** When a policy is tightened (new CVE rule, stricter certificate identity), previously passing Snapshots may need to be rebuilt and re-evaluated. This is intentional: policy enforcement is forward-looking, not a one-time gate.
- **Config drift is detectable and auditable.** The Rekor transparency log records every signing event with the builder identity and timestamp. A mismatch between the log and the policy is always detectable, even after the fact.
- **Failure messages are actionable.** Each scenario produces specific, structured error output from Conforma and `cosign` that tells an operator exactly which rule failed and why — making remediation straightforward for teams who understand the supply chain.
- **The happy path was the prerequisite.** These scenarios only make sense because participants have already seen the full working supply chain. The contrast between what passed and what failed is what makes each incident legible.

### Infrastructure Notes

- Three pre-built "bad" images must be provisioned in the lab Quay registry before the lab runs:
  - `unsigned-hotfix` — an image with no signature and no SLSA attestation, pushed directly to Quay outside Konflux.
  - `cve-sample` — an image built through Konflux but containing a dependency with a specific known CVE that the policy flags as a blocking violation. The lab administrator must confirm the CVE identifier and the policy rule name that catches it.
  - `key-drift` — an image signed with a certificate identity that does not appear in the policy's trusted builder list. This can be an image signed with a personal key or built through a pipeline not registered as a trusted builder.
- The policy bundle reference (`--policy` flag) used in this module must be the same bundle configured in the IntegrationTestScenario and ReleasePlanAdmission. Writers must obtain the exact OCI reference from the lab environment.
- The Rekor lookup in step 23 requires network access to the Trusted Artifact Signer Rekor instance. If the cluster uses a self-signed TLS certificate, participants may need to set `SIGSTORE_REKOR_PUBLIC_KEY` or the equivalent environment variable — the lab guide should specify the correct configuration.
- Writers should verify that the three bad image digests are stable (pinned by digest, not by tag) and documented in a lab reference appendix so participants do not need to discover them during the exercise.
