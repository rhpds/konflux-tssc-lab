# Module Outline: Module 02 — Onboard Your Application

---

### Brief Overview

In this module participants register their pre-provisioned GitLab sample application with Konflux by creating a Konflux Application and Component, then wire up Pipelines-as-Code so that every push to the GitLab repository automatically triggers a Konflux build pipeline. By the end of the module the Konflux UI shows the Component linked to the GitLab repository, and a PipelineRun has been created (or is running) in response to a test push or merge request. This is the foundational integration step; all later modules depend on the connection established here.

### Audience and Time

- **Target personas:** Application developers, DevOps engineers, platform engineers.
- **Prerequisites for this module:** Module 01 completed; GitLab repo URL and Quay org name noted; logged in to Konflux, GitLab, and the OpenShift cluster.
- **Estimated duration:** 15 minutes

### Learning Objectives

- Create a Konflux Application and Component linked to your pre-provisioned GitLab repository.
- Configure Pipelines-as-Code integration so that GitLab merge request and push events automatically trigger Konflux build pipelines.
- Verify the onboarding by observing the first PipelineRun created in your tenant namespace.

### Lab Structure

| Section | Title | Duration |
|---------|-------|----------|
| 1 | Create a Konflux Application | 4 min |
| 2 | Add the Component and Connect GitLab | 6 min |
| 3 | Trigger and Verify the First PipelineRun | 5 min |

### Detailed Steps

**Section 1 — Create a Konflux Application**

1. In the Konflux web UI, ensure you are in your personal workspace (top-left workspace selector shows your assigned user ID).
2. Click **Create application** (or the equivalent button on the Applications overview page).
3. In the **Application name** field, enter a name for your application (e.g., `my-sample-app`). Record this name — you will reference it in later modules.
4. Leave all other fields at their defaults and click **Create** (or **Next**).
5. Confirm the new Application appears in the Applications list with a status of "No components yet" or similar.

**Section 2 — Add the Component and Connect GitLab**

6. Inside the Application detail page, click **Add component**.
7. In the **Source** field, select **Git repository** and paste the GitLab repository URL noted in Module 1.
8. When prompted to authenticate or provide a token for the GitLab source, use the GitLab personal access token provided in your lab credentials. Enter it in the provided field.
9. Konflux will inspect the repository. Confirm the repository is detected and a Dockerfile or build strategy is identified automatically (the sample app includes a Dockerfile).
10. In the **Component name** field, accept the auto-generated name or set a clear name (e.g., `sample-app`).
11. Set the **Target image repository** to your pre-provisioned Quay organization and repository (e.g., `quay.<cluster-domain>/<your-quay-org>/sample-app`). The lab guide provides the full image path.
12. Click **Create component**. Konflux will commit a `.tekton/` directory with PipelineRun definitions into your GitLab repository via a merge request.
13. Switch to the GitLab browser tab. Locate the merge request opened by Konflux (it will be titled something like "Konflux — initial PipelineRun configuration"). Review the files added under `.tekton/`.
14. Merge the merge request into the default branch.

**Section 3 — Trigger and Verify the First PipelineRun**

15. After the merge, return to the Konflux UI. Navigate to **Pipelines** or **Activity** within your Application.
16. Observe that a PipelineRun has been created (or is queued) automatically in response to the merge event. Note the PipelineRun name.
17. In the terminal, run `oc get pipelineruns -n <your-tenant-namespace>` to confirm the same PipelineRun appears in your tenant namespace.
18. In the Konflux UI, click the PipelineRun name to open its detail view. Observe the pipeline stages listed (the pipeline should include a build task and at least one scan task).
19. Wait for the PipelineRun to reach a **Running** or **Succeeded** state before moving to Module 3. If it fails, read the task logs shown in the UI and report the error to the instructor.
20. Confirm the Component status in the Application view shows the linked GitLab repository URL and the target Quay image path.

### Key Takeaways

- Konflux uses a GitOps model: onboarding a component causes Konflux to commit Tekton PipelineRun manifests directly into the source repository.
- Pipelines-as-Code (PaC) reads those manifests from the `.tekton/` directory in the repository and triggers runs on push and merge-request events — no manual pipeline execution is needed.
- The target image registry (Quay) is declared at the Component level; the build pipeline pushes all images and attestations to that registry automatically.
- Isolating each participant in their own tenant namespace means PipelineRuns from other participants do not appear in your view and cannot interfere with your resources.

### Infrastructure Notes

- The GitLab webhook to the Konflux Pipelines-as-Code controller is configured automatically when Konflux commits the `.tekton/` directory — no manual webhook setup is required.
- If the GitLab repository is private and the cluster cannot reach it, the lab administrator must pre-configure a Git secret in the tenant namespace. Check for a secret named `pipelines-as-code-secret` or equivalent using `oc get secrets -n <your-tenant-namespace>`.
- The Quay image push credentials must be present as a Kubernetes pull secret linked to the pipeline service account. Verify with `oc get serviceaccount pipeline -n <your-tenant-namespace> -o yaml` and confirm an image pull/push secret is attached.
- The sample application repository must include a `Dockerfile` at the repository root (or a path Konflux can detect). The pre-provisioned repository satisfies this requirement.
