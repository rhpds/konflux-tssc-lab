# Module Outline: Module 05 — Integration Testing and Policy

---

### Brief Overview

Before an artifact can be released to production, Konflux runs it through an Integration pipeline and evaluates it against an Enterprise Contract (Conforma) policy set. This module walks participants through the Integration pipeline results for their Component, examines the policy rules that govern artifact promotion, and — critically — demonstrates what happens when a policy check fails by observing how a failed check blocks the artifact from moving forward. Participants leave with a concrete understanding of how policy-as-code enforces supply chain standards automatically, without relying on human approval gates.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers, security-minded practitioners.
- **Prerequisites for this module:** Module 04 completed; the PipelineRun from Module 03 has succeeded; participant is familiar with the SLSA provenance attestation from Module 04.
- **Estimated duration:** 15 minutes

### Learning Objectives

- Analyze the Enterprise Contract policy rules applied to your Konflux Application and understand what each rule enforces.
- Observe how the Integration pipeline evaluates policy checks against the signed artifact produced in earlier modules.
- Troubleshoot a policy check failure by reading the policy evaluation output and identifying which rule was violated and why.
- Verify that a policy-passing artifact is marked as eligible for promotion while a failing artifact is blocked.

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | Examine the Enterprise Contract Policy | 4 min |
| 2 | Review Integration Pipeline Results | 5 min |
| 3 | Observe a Policy Failure | 4 min |
| 4 | Confirm the Passing Artifact Status | 2 min |

### Detailed Steps

**Section 1 — Examine the Enterprise Contract Policy**

1. In the Konflux UI, navigate to your Application and then to the **Enterprise Contract** or **Policy** section (exact navigation label depends on the Konflux version; the lab guide provides a screenshot).
2. Open the Enterprise Contract (EC) policy assigned to your Application. Note the policy source — it references a policy bundle (an OCI image or a git repository containing Rego rules).
3. Read the list of policy rules shown in the UI. Identify the following categories of rules (the lab guide lists the specific rules active in this environment):
   - **Attestation rules:** require that a SLSA provenance attestation is present and signed.
   - **Image rules:** require that the image is signed and the signature is verifiable.
   - **SBOM rules:** require that an SBOM attestation is attached to the image.
   - **Pipeline rules:** require that the build was run by a trusted Konflux pipeline task set.
4. In the terminal, use `ec` CLI or `conforma` CLI to list the active policy rules (the lab guide specifies the exact command for this cluster):
   ```
   ec validate image \
     --image "$IMAGE" \
     --policy "<policy-bundle-ref>" \
     --output json | jq '.components[].violations'
   ```
5. Review the output. With the artifact from Module 03/04, most or all rules should pass. Make note of any warnings (non-blocking) versus violations (blocking).

**Section 2 — Review Integration Pipeline Results**

6. In the Konflux UI, navigate to **Integrations** or **Snapshots** for your Application. A Snapshot was created automatically when your PipelineRun succeeded in Module 03.
7. Click the Snapshot to open its detail view. Confirm it references the image digest from Module 03.
8. Observe the Integration pipeline runs listed for the Snapshot. The default integration pipeline includes an Enterprise Contract check task.
9. Click the Enterprise Contract integration test run. In its logs or results tab, find the EC evaluation output. Confirm that the result is **Pass** (or **Success**) for the artifact built following the lab steps.
10. In the terminal, run:
    ```
    oc get integrationtestscenario -n <your-tenant-namespace>
    ```
    Observe the IntegrationTestScenario object(s) configured for your Application. Note which integration pipeline is referenced.
11. Run:
    ```
    oc get snapshots -n <your-tenant-namespace>
    ```
    Identify the Snapshot created for your latest build. Note its `STATUS` field — after Integration passes, it should show a passing or approved state.

**Section 3 — Observe a Policy Failure**

12. To simulate a policy failure, the lab provides a pre-built "bad" image reference — an image that is either unsigned or missing a required attestation. The lab guide specifies the exact image reference. Set it as a variable:
    ```
    BAD_IMAGE="quay.<cluster-domain>/lab-examples/unsigned-sample@sha256:<bad-digest>"
    ```
13. Run the EC validation CLI against the bad image:
    ```
    ec validate image \
      --image "$BAD_IMAGE" \
      --policy "<policy-bundle-ref>" \
      --output json | jq .
    ```
14. In the JSON output, locate the `components[].violations` array. Identify the specific rules that failed and read their `msg` fields to understand what the violation means.
15. Confirm that at least one of the following violation types appears: missing signature, missing SLSA attestation, or untrusted builder identity.
16. Observe the overall `success` field in the JSON — it is `false` when any violation is present. This is the signal that Enterprise Contract would use to block promotion in a real release pipeline.
17. In the Konflux UI, if the lab environment has a pre-created failing Snapshot, navigate to it and observe how the UI marks it — it should be visually distinguished from passing Snapshots (e.g., a red status, "Failed" label, or blocked promotion indicator).

**Section 4 — Confirm the Passing Artifact Status**

18. Return to your own Snapshot (the one from your Module 03 build). Confirm in the Konflux UI that it shows a passing status and is marked as eligible for release.
19. In the terminal, describe the Snapshot and check its conditions:
    ```
    oc get snapshot <snapshot-name> -n <your-tenant-namespace> -o yaml | grep -A5 'conditions:'
    ```
    Confirm there is a condition with `type: Released` or `type: IntegrationTestsPassed` in a `True` state (exact condition names depend on the Konflux version; the lab guide specifies the expected output).
20. Note that a Snapshot in "passing" state is a prerequisite for the ReleasePlan to trigger in Module 6.

### Key Takeaways

- Enterprise Contract (Conforma) evaluates Rego policy rules against the evidence attached to an image: signature, SBOM, and SLSA provenance attestation.
- Policy checks are automated — they run inside the Integration pipeline without any human intervention, making enforcement consistent and auditable.
- A single failing policy rule blocks the entire Snapshot from being promoted, regardless of how many other rules pass. This is "fail-closed" policy enforcement.
- The difference between a passing and failing artifact is visible in the Konflux UI and queryable via `oc get snapshot` — platform engineers can observe policy compliance across all Applications from a central view.
- Policy rules are versioned (the policy bundle is itself an OCI image or Git ref) — changing the policy is an auditable, reviewable change, not an ad-hoc decision.
- The Snapshot model decouples "what was built" from "what is allowed to release" — teams can iterate on builds without triggering releases until the policy is satisfied.

### Infrastructure Notes

- The `ec` (Enterprise Contract) CLI or `conforma` CLI must be available in the participant's terminal. Writers must confirm the correct binary name, version, and installation method for this lab environment.
- The policy bundle reference (`--policy` flag) is environment-specific. Writers must replace `<policy-bundle-ref>` with the exact OCI reference or git URL used in this cluster — obtain it from the EnterpriseContractPolicy object in the tenant or managed namespace:
  ```
  oc get enterprisecontractpolicy -A
  ```
- The "bad" image used in Section 3 must be pre-loaded into the lab Quay registry and its digest must be known. The lab administrator must provision this as part of lab setup.
- IntegrationTestScenario and Snapshot CRD names may differ between Konflux versions. Writers must verify the exact API group and version using `oc api-resources | grep -i integration`.
