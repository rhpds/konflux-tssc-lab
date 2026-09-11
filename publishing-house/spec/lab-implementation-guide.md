# Konflux TSSC Lab - Complete Implementation Guide

**Purpose**: Step-by-step instructions for each module to recreate the lab content  
**Author**: Lab Development Team  
**Date**: 2026-09-07  
**Lab Duration**: 2 hours (120 minutes)

---

## Table of Contents

1. [Module 01: Orientation](#module-01-orientation-10-min)
2. [Module 02: Onboard Your Application](#module-02-onboard-your-application-15-min)
3. [Module 03: Build and Scan](#module-03-build-and-scan-20-min)
4. [Module 04: Signing and Provenance](#module-04-signing-and-provenance-20-min)
5. [Module 05: Integration Testing and Policy](#module-05-integration-testing-and-policy-15-min)
6. [Module 06: Release to Production](#module-06-release-to-production-15-min)
7. [Module 07: Real-World Incident Response](#module-07-real-world-incident-response-25-min)
8. [Appendix: Pre-Provisioned Environment](#appendix-pre-provisioned-environment)

---

## Module 01: Orientation (10 min)

**Learning Objectives**:
- Explore the pre-provisioned lab environment and locate personal resources
- Understand the software supply chain security problem
- Identify the role each tool plays in the end-to-end supply chain

**What Students Have Pre-Provisioned**:
- GitLab user account with `sample-component-golang` repository imported
- Quay user account
- OpenShift HTPasswd user account
- Two namespaces: `user-{guid}-tenant` and `user-{guid}-managed`
- Konflux RBAC permissions via ClusterRole
- Showroom lab guide with terminal

---

### Section 1: The Supply Chain Security Problem (3 min)

**Instruction**:
```
Read the following scenario to understand why supply chain security matters.

In 2020, attackers compromised the SolarWinds build system and injected 
malicious code into their software update. The signed update was distributed 
to thousands of organizations. The problem: the digital signature proved the 
artifact came from SolarWinds' infrastructure, but it didn't prove the 
infrastructure itself was trustworthy.

Modern supply chain security solves this by requiring:
1. Cryptographic proof that code came from a specific source commit
2. A tamper-evident audit log showing when and how the artifact was built
3. Policy checks that verify no vulnerabilities or unauthorized changes exist
4. Keyless signing that doesn't require managing long-lived secrets
```

**Expected Outcome**: Students understand the gap between "image is built" and "image is trusted"

---

### Section 2: Tour the Lab Environment (4 min)

**Step 1: Access the Showroom Lab Guide**

```
1. Open the Showroom URL provided in your provisioning confirmation email
2. You should see this lab guide with an embedded terminal on the right
3. Click the terminal and verify you can type commands
```

**Expected**: Showroom UI loads, terminal is responsive

---

**Step 2: Verify Konflux UI Access**

```
1. Find the Konflux UI URL in the Environment Variables section above
   (or in the lab credentials table)
2. Open the Konflux UI URL in a new browser tab:
   https://konflux-ui-konflux-ui.apps.cluster-{guid}.{domain}

3. Log in using your OpenShift credentials:
   - Username: user-{guid}
   - Password: {provided in credentials}

4. After login, verify you see the Konflux Overview page with "Get started with Konflux"

5. Click "Namespaces" in the left sidebar (or click the "View my namespaces" button)

6. Verify you see "user-{guid}-tenant" in the namespace list
```

**Expected**: Konflux UI loads, user is authenticated, namespace is accessible

---

**Step 3: Verify GitLab Access**

```
1. Find the GitLab URL in the credentials section
2. Open GitLab in a new browser tab:
   https://gitlab-gitlab.apps.cluster-{guid}.{domain}

3. Log in:
   - Username: user-{guid}
   - Password: {same as OpenShift password}

4. Click "Projects" in the left sidebar

5. Click the "Personal" tab (should show "1" indicating one personal project)

6. Locate the "sample-component-golang" repository in the list

7. Click into the repository and note the repository URL
   (you'll need this in Module 02)

8. Browse the repository files:
   - main.go (the application code)
   - Dockerfile (container build definition)
   - go.mod (Go dependencies)
```

**Expected**: GitLab loads, repository is visible with expected files

---

**Step 4: Verify Quay Access**

```
1. Find the Quay URL in the credentials section
2. Open Quay in a new browser tab:
   https://quay-{cluster}.apps.cluster-{guid}.{domain}

3. Log in:
   - Username: user-{guid}
   - Password: {same as OpenShift password}

4. Verify you land on the Organizations page
   - Your username should appear in the top-right corner (user-{guid})
   - You should see one organization: "user-{guid}" with 0 repos

5. Click "Repositories" in the left sidebar
   - Confirm the page is empty (no repositories yet - this is normal)
```

**Expected**: Quay loads, user is authenticated, organization created

---

**Step 5: Verify Red Hat Trusted Artifact Signer (RHTAS)**

```
1. Find the Rekor URL in the credentials section
2. Open the Rekor Search UI:
   https://rekor-search-ui-tsf-tas.apps.cluster-{guid}.{domain}

3. The transparency log UI should load (no login required)
4. This is where all image signatures are recorded
   (you'll use this in Module 04)
```

**Expected**: Rekor UI loads (may show empty results initially)

---

### Section 3: Verify Your Personal Resources (3 min)

**Step 6: Log in to OpenShift CLI**

```
In the Showroom terminal, run:

oc login https://api.cluster-{guid}.{domain}:6443 \
  --username=user-{guid} \
  --password='{your-password}' \
  --insecure-skip-tls-verify=true

Expected output:
Login successful.
You have access to the following projects and can switch between them with 'oc project <projectname>':
  * user-{guid}-managed
  * user-{guid}-tenant
Using project "user-{guid}-tenant".
```

**Expected**: CLI login succeeds, 2 namespaces are visible (tenant and managed)

---

**Step 7: Inspect Your Tenant Namespace**

```
# Confirm current namespace
oc project user-{guid}-tenant

# List projects you have access to
oc get projects | grep user-{guid}

Expected output:
user-{guid}-managed     Active   5m
user-{guid}-tenant      Active   5m

Note: You should see 2 namespaces. The showroom namespace (where this 
lab guide runs) is not accessible to your user account.

# Check Konflux permissions
oc auth can-i create applications.appstudio.redhat.com -n user-{guid}-tenant

Expected output: yes

oc auth can-i create components.appstudio.redhat.com -n user-{guid}-tenant

Expected output: yes

oc auth can-i create releaseplans.appstudio.redhat.com -n user-{guid}-tenant

Expected output: yes
```

**Expected**: Permissions are granted for Konflux resources

---

**Step 8: Verify RoleBindings**

```
# List RoleBindings in your tenant namespace
oc get rolebindings -n user-{guid}-tenant | grep konflux

Expected output:
konflux-admin   ClusterRole/konflux-admin-user-actions   5m

# Describe the ClusterRole to see permissions
oc describe clusterrole konflux-admin-user-actions | head -60

Expected: You should see permissions for:
- applications.appstudio.redhat.com
- components.appstudio.redhat.com
- releaseplans.appstudio.redhat.com
- integrationtestscenarios.appstudio.redhat.com
- pipelineruns.tekton.dev, pipelines.tekton.dev, taskruns.tekton.dev
- serviceaccounts, secrets, configmaps
- pods, pods/log

# Verify Tekton permissions specifically
oc describe clusterrole konflux-admin-user-actions | grep -A 2 "tekton.dev"
```

**Expected**: ClusterRole grants full Konflux resource management

---

**Key Takeaways**:
- A container image built without signing and attestation cannot be trusted at deploy time
- SLSA (Supply Chain Levels for Software Artifacts) defines a framework for proving build provenance
- SBOMs enumerate dependencies inside an image for vulnerability tracking
- Sigstore and RHTAS provide cryptographic signing and tamper-evident transparency logs
- Konflux orchestrates the full build → sign → attest → release pipeline
- Each participant's resources are isolated in a tenant namespace

---

## Module 02: Onboard Your Application (15 min)

**Learning Objectives**:
- Create a Konflux Application and Component linked to GitLab repository
- Configure Pipelines-as-Code integration for automated builds
- Verify the first PipelineRun is created

**Prerequisites**:
- Module 01 completed
- GitLab repository URL noted
- Logged in to Konflux, GitLab, and OpenShift cluster

---

### Section 1: Create a Konflux Application (4 min)

**Step 1: Navigate to Applications**

```
1. In the Konflux UI, you should be on the Namespaces page
2. Click on your namespace: "user-{guid}-tenant" (click the row in the table)
3. The namespace view will open and "Applications" in the sidebar will become enabled
4. Click "Applications" in the left sidebar
5. You should see an empty Applications list with a "Create application" button
```

**Expected**: Empty application list displayed within your namespace

---

**Step 2: Create Application**

```
1. Click "Create application" button

2. In the form that appears:
   - Application name: my-sample-app

3. Click "Create application" button at the bottom of the form

4. Wait for the Application to be created (should take 2-5 seconds)

5. You will be redirected to the Application detail page
```

**Expected**: Application created, redirected to Application detail page

---

**Step 3: Configure Integration Test Pipeline**

```
When Konflux creates an Application, it automatically creates an 
IntegrationTestScenario that runs Enterprise Contract policy checks.
Because we have limited resources in this lab environment, we need
to reduce resource requests and limits from the default Konflux
settings which require very high CPU.

In the Showroom terminal, run this command to patch the 
IntegrationTestScenario to use a low-resource version:

oc patch integrationtestscenario my-sample-app-enterprise-contract \
  -n user-{guid}-tenant \
  --type='json' \
  -p='[
  {
    "op": "replace",
    "path": "/spec/resolverRef/params/0/value",
    "value": "https://github.com/rhpds/konflux-tssc-lab"
  },
  {
    "op": "replace",
    "path": "/spec/resolverRef/params/2/value",
    "value": "tekton/pipelines/enterprise-contract-low-resources.yaml"
  }
]'

Expected output:
integrationtestscenario.appstudio.redhat.com/my-sample-app-enterprise-contract patched

Verify the patch was applied:

oc get integrationtestscenario my-sample-app-enterprise-contract \
  -n user-{guid}-tenant \
  -o jsonpath='{.spec.resolverRef.params[*]}' | jq

Expected output should show:
- url: https://github.com/rhpds/konflux-tssc-lab
- pathInRepo: tekton/pipelines/enterprise-contract-low-resources.yaml
```

**Expected**: IntegrationTestScenario configured to use low-resource Enterprise Contract pipeline from the lab's GitHub repository

**Why This Matters**: The default Konflux Enterprise Contract pipeline requires
very high CPU resources. The low-resource version reduces these requirements to
fit within our lab environment's resource constraints.

---

### Section 2: Configure GitLab Authentication for Konflux (5 min)

**Step 4: Create GitLab Personal Access Token**

```
Konflux uses Pipelines-as-Code (PaC) to integrate with GitLab. PaC needs a 
Personal Access Token (PAT) to:
- Clone the source code
- Create merge requests with pipeline definitions
- Set up webhooks
- Update commit statuses
- Read pipeline definitions from .tekton/ directory

1. In your GitLab browser tab, click your user avatar (top-right corner)

2. Click "Preferences" from the dropdown menu

3. In the left sidebar, click "Access Tokens" (or "Access" → "Personal access tokens")

4. Click the "Add new token" button (top-right corner)

5. Fill out the token creation form:
   - Token name: konflux-pac
   - Expiration date: (leave default or set far in future)
   - Select scopes: Check the following boxes:
     ✓ api (Grants complete read/write access to the API)
     ✓ read_repository (Grants read-only access to repositories)
     ✓ write_repository (Grants read-write access to repositories)

6. Click the "Create personal access token" button at the bottom of the form

7. IMPORTANT: Copy the token that appears at the top of the page
   (It looks like: glpat-xxxxxxxxxxxxxxxxxxxx)
   You will only see this token once!

8. Keep this token ready - you'll use it in the next step
```

**Expected**: Personal access token created and copied

---

**Step 5: Create GitLab Authentication Secret**

```
Now create the Kubernetes secret with your GitLab Personal Access Token.

In the Showroom terminal, run this command, replacing {your-token} with 
the Personal Access Token you just copied:

cat <<EOF | oc apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: gitlab-auth-secret
  namespace: user-{guid}-tenant
  labels:
    appstudio.redhat.com/credentials: scm
    appstudio.redhat.com/scm.host: gitlab-gitlab.apps.cluster-{guid}.{domain}
type: kubernetes.io/basic-auth
stringData:
  username: ""
  password: {your-token}
EOF

IMPORTANT: The username field MUST be an empty string when using a Personal Access Token.

Example (replace the glpat-xxx with your actual token):
password: glpat-uySoCmr_c5IajdNFIUsObm86MQp1OjcH

Verify the secret was created:

oc get secret gitlab-auth-secret -n user-{guid}-tenant

Expected output:
NAME                  TYPE                       DATA   AGE
gitlab-auth-secret    kubernetes.io/basic-auth   2      5s
```

**Expected**: Secret created successfully with GitLab PAT, Konflux can now authenticate to GitLab

---

### Section 3: Add the Component and Connect GitLab (6 min)

**Step 6: Add Component to Application**

```
1. You should now be on the Application detail page for "my-sample-app"

2. You'll see a "What's next?" section with several cards including:
   - "Grow your application" - with an "Add component" button
   - "Add integration tests"
   - "Create a release plan"
   - And other setup options

3. Click the "Add component" button in the "Grow your application" card
```

**Expected**: Add component form opens

---

**Step 7: Fill Out Add Component Form**

```
You should see the "Create a Component" form with the following fields:

1. Application name: (pre-filled with "my-sample-app" - read-only)

2. Git repository url: Paste your GitLab repository URL from Module 01
   Example: https://gitlab-gitlab.apps.cluster-{guid}.{domain}/user-{guid}/sample-component-golang.git

3. Docker file: Leave as default "./Dockerfile" (or enter if empty)

4. Component name: Enter "sample-component-golang"
   (Must be unique within your tenant namespace)

5. Pipeline: Select "docker-build-oci-ta-min"
   (This is the default Konflux pipeline with minimal resource requests,
   optimized for shared environments)

6. UNCHECK "Mark image as private in Quay"
   (This allows the image to be public for easier sharing and testing)

7. Build time secret: Leave empty (no additional secrets needed for this lab)

8. Scroll down and click "Add component" button
```

**Expected**: Component is added to the application, form submits

---

### Section 4: Review and Merge Pipeline Configuration (5 min)

**Step 8: Review GitLab Merge Request and Initial Pipeline**

```
After adding the component, Konflux automatically creates a merge request 
in your GitLab repository to add Pipelines-as-Code configuration files.

IMPORTANT: Creating the Merge Request automatically triggers the pull-request 
pipeline to run BEFORE you merge. This validates the pipeline configuration.

1. Switch to your GitLab browser tab

2. Navigate to your "sample-component-golang" repository

3. Click "Code" in the left sidebar, then click "Merge requests"

4. You should see Merge Request #1 (created by Konflux/automation)
   - Title may be: "Konflux update sample-component-golang"

5. Click on the merge request to open it

6. Review the changes - you'll see a new `.tekton/` directory being added with:
   - `.tekton/sample-component-golang-pull-request.yaml` (triggers on PRs)
   - `.tekton/sample-component-golang-push.yaml` (triggers on push to main)

7. These files define the build pipeline that will run automatically on code changes

8. IMPORTANT: Notice the pipeline status at the top of the MR:
   - You should see a pipeline run triggered by the MR creation
   - Status may show: "Running", "Pending", or "Passed"
   - This is the pull-request pipeline validating the MR
```

**Expected**: Merge request is visible with `.tekton/` pipeline definitions and an active pipeline run

---

**Step 9: Check Pull-Request Pipeline Status**

```
Before merging, verify the pull-request pipeline succeeded:

1. In the GitLab MR view, look at the pipeline status

2. If status shows "Passed" (green checkmark):
   - The pipeline configuration is valid
   - Proceed to Step 10 to merge the MR

3. If status shows "Failed" or "Cancelled":
   - DO NOT merge yet
   - Continue to Step 9a to restart the pipeline
   - Wait for the pipeline to succeed before merging

4. Click the pipeline status badge to view the pipeline details in Konflux
```

**Expected**: Pull-request pipeline status is visible

---

**Step 9a: Restart a Failed or Cancelled Pipeline (if needed)**

```
If the pull-request pipeline failed or was cancelled, restart it by adding 
a comment to the GitLab Merge Request.

IMPORTANT: You can only restart pipelines on OPEN Merge Requests. Once merged, 
this method won't work.

Option 1: Add /retest comment in GitLab UI (Easiest)
--------------------------------------------------------
1. In the GitLab MR view, scroll down to the comment section
2. Type: /retest
3. Click "Comment"
4. Wait 30-60 seconds for a new PipelineRun to start
5. Monitor the pipeline status in the MR view
6. Once it shows "Passed", proceed to Step 10

Option 2: Push a commit via GitLab API (If Option 1 doesn't work)
------------------------------------------------------------------
1. In the Showroom terminal, use the GitLab API to create a commit on the MR branch:

   # Get GitLab credentials
   GITLAB_HOST="gitlab-gitlab.apps.cluster-{guid}.{domain}"
   GITLAB_TOKEN=$(oc get secret gitlab-auth-secret -n user-{guid}-tenant -o jsonpath='{.data.password}' | base64 -d)
   
   # Create a commit via GitLab API
   curl -k --request POST \
     --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
     --header "Content-Type: application/json" \
     --data '{
       "branch": "konflux-sample-component-golang",
       "commit_message": "trigger pipeline retry",
       "actions": [
         {
           "action": "create",
           "file_path": ".trigger-'$(date +%s)'",
           "content": "pipeline trigger"
         }
       ]
     }' \
     "https://${GITLAB_HOST}/api/v4/projects/1/repository/commits"

   This creates a new commit on the MR branch without needing git configured locally.

2. Wait 30-60 seconds for the new PipelineRun to start
3. Monitor in GitLab MR view or Konflux Activity tab
4. Once pipeline shows "Passed", proceed to Step 10

Expected output:
- GitLab API returns commit details (JSON response)
- New PipelineRun created for the MR
- Pipeline executes successfully
- MR shows "Passed" status
```

**Expected**: Pipeline is restarted and completes successfully

---

**Step 10: Merge the Pipeline Configuration**

```
Once the pull-request pipeline shows "Passed":

1. Review the pipeline YAML files to understand what they do
   (they define build tasks: clone, build-container, scan, sign, etc.)

2. Click the "Merge" button to merge the MR into the main branch

3. Confirm the merge

4. Wait 30-60 seconds for the merge event to trigger the push pipeline
```

**Expected**: MR is merged, `.tekton/` directory now exists in main branch

---

### Section 5: Monitor the Push PipelineRun (5 min)

**Step 10: Watch the Push Build Start**

```
After merging the MR, a PUSH pipeline is triggered (different from the 
pull-request pipeline that ran before the merge).

1. Switch back to the Konflux UI browser tab

2. The component status should update from "Build not started" to "Building"

3. Click on the component name "sample-component-golang" to open its detail page

4. Click on the "Activity" tab

5. You should see TWO PipelineRuns now:
   - sample-component-golang-on-pull-request-xxxxx (from the MR creation)
   - sample-component-golang-on-push-xxxxx (NEW - from the merge)

6. Click on the ON-PUSH PipelineRun name to open its detail view

7. Observe the pipeline tasks listed:
   - init
   - clone-repository
   - prefetch-dependencies
   - build-container
   - build-image-index
   - deprecated-base-image-check
   - clamav-scan
   - sast-shell-check
   - sast-unicode-check
   - rpms-signature-scan
   - tpa-scan

8. Note the PipelineRun name (e.g., sample-component-golang-on-push-abc123)
```

**Expected**: Push PipelineRun is triggered and running after merge

---

**Step 11: Verify PipelineRun in CLI**

```
In the Showroom terminal:

# List PipelineRuns in your tenant namespace
oc get pipelineruns -n user-{guid}-tenant

Expected output:
NAME                                         SUCCEEDED   REASON      STARTTIME   COMPLETIONTIME
sample-component-golang-on-pull-request-xxx   True       Succeeded   5m          3m
sample-component-golang-on-push-abc123        Unknown    Running     1m          

The pull-request pipeline should show "Succeeded" (it ran before the merge)
The push pipeline should show "Running" (triggered by the merge)

# Get detailed status of the push pipeline
oc describe pipelinerun sample-component-golang-on-push-abc123 -n user-{guid}-tenant | head -30

Expected: You should see task statuses (some Running, some Pending)
```

**Expected**: Both PipelineRuns visible in CLI - pull-request (completed) and push (running)

---

**Step 12: Verify Component Status**

```
1. In Konflux UI, return to Application → Components → sample-component-golang

2. Verify the Component details show:
   - Git repository URL: {your GitLab repo}
   - Target image: {your Quay image path}
   - Latest PipelineRun: {the push run you just triggered}
   - Status: Building (or Running)

3. You may leave the pipeline running — it will complete in the background
   (Module 03 will inspect the completed build)
```

**Expected**: Component shows linked repository and running pipeline

---

**Key Takeaways**:
- Konflux uses a GitOps model: onboarding a component causes Konflux to commit Tekton PipelineRun manifests directly into the source repository
- Creating a component triggers TWO pipeline runs:
  1. Pull-request pipeline when the MR is created (validates the `.tekton/` configuration)
  2. Push pipeline when the MR is merged (builds the actual image)
- Pipelines-as-Code (PaC) reads manifests from `.tekton/` and triggers runs on push/MR events
- The `/retest` comment can restart failed pipelines on open Merge Requests
- The target image registry (Quay) is declared at the Component level
- Isolating each participant in their own tenant namespace means PipelineRuns from other participants don't appear in your view

---

## Module 03: Build and Scan (15 min)

**Learning Objectives**:
- Trace the completed pipeline execution stages
- Inspect the automatically generated SBOM
- Verify the built image and artifacts in Quay
- Understand what artifacts the build pipeline produces

**Prerequisites**:
- Module 02 completed
- Push PipelineRun from Module 02 should be complete (or nearly complete)

**What Happened in Module 02**:
After merging the Konflux-generated MR in Module 02, a push pipeline was automatically triggered. This pipeline built your container image, scanned it for vulnerabilities, generated an SBOM, and pushed everything to Quay. After the pipeline completes, Tekton Chains automatically signs the artifacts and generates provenance attestations. In this module, we'll examine what that pipeline produced.

---

### Section 1: Verify Pipeline Completion (3 min)

**Step 1: Locate the Push PipelineRun**

```
1. In the Konflux UI, navigate to your Application → Activity (or Pipelines tab)

2. Find the most recent PipelineRun:
   - Name: sample-component-golang-on-push-{random-id}
   - Triggered by: Push event from merging the MR in Module 02
   - Status: Should be "Succeeded" (green checkmark)

3. If the pipeline is still running, wait for it to complete
   (typical time: 8-15 minutes from the merge)

4. Click on the PipelineRun to open its detail view

5. In the PipelineRun detail page, observe:
   - Pipeline visualization graph showing all tasks (prefetch-dependencies, build-container, 
     build-image-index, deprecated-base-image-check, clamav-scan, sast-shell-check, 
     sast-unicode-check, rpms-signature-scan, tpa-scan)
   - Tasks with green checkmarks indicate successful completion
   - Status field shows "Succeeded"
   - Snapshot link (if integration tests ran)
   - Download SBOM section (you'll use this in Step 5)
```

**Expected**: Push pipeline from Module 02 is visible and completed successfully in Konflux UI

---

### Section 2: Trace the Pipeline Stages (7 min)

**Step 2: Understand the Pipeline Tasks**

```
In the PipelineRun detail view, identify each task and its purpose:

Task Name                    | Purpose
-----------------------------|--------------------------------------------------
init                         | Validates workspace and sets up build context
clone-repository             | Fetches source code from GitLab
prefetch-dependencies        | Pre-fetches build dependencies for hermetic builds
build-container              | Builds OCI image using Buildah
build-image-index            | Creates multi-arch image index
deprecated-base-image-check  | Checks if base image is deprecated
clamav-scan                  | Scans image for malware and viruses
sast-shell-check             | Static analysis for shell scripts
sast-unicode-check           | Detects potentially malicious unicode characters
rpms-signature-scan          | Verifies signatures of RPM packages in the image
tpa-scan                     | Trusted Profile Analyzer - scans for CVE vulnerabilities and policy compliance

Note: SBOM generation happens automatically during the build-container and 
build-image-index tasks using Syft. Image signing and provenance attestations 
are handled by Tekton Chains after the pipeline completes. These artifacts are 
attached to the image in Quay and can be retrieved with cosign.
```

**Expected**: Students understand what each task does

---

**Step 3: Examine the build-container Task**

```
1. In the pipeline task list, find the "build-container" task (should show "Succeeded")

2. Click on the task name to expand it

3. Click "Logs" to view the Buildah build output

4. Scroll through the logs and find the image digest after the push completes:
   
   The image is pushed twice (once with unique tag, once with git revision tag).
   Look for the SECOND occurrence of "Writing manifest to image destination"
   which appears AFTER the "Push image with git revision" section.
   
   Example output:
   Writing manifest to image destination
   [timestamp] Push image with git revision
   Pushing to quay-t7cws-1.apps.cluster-{guid}.{domain}/user-{guid}/sample-component-golang:b953f80...
   ...
   Writing manifest to image destination
   sha256:01ad2ac59ac87ee33aef018e101cc98833c5cf5906945906879d61329594bcb8quay-...
   
   The digest is the sha256:... part at the beginning of the line after the 
   SECOND "Writing manifest to image destination".

5. Copy the full sha256 digest (you'll need this later in this module)
   Example: sha256:01ad2ac59ac87ee33aef018e101cc98833c5cf5906945906879d61329594bcb8

6. Optional: Expand other tasks (clamav-scan, sast-shell-check, tpa-scan) to see their logs
```

**Expected**: Image digest is obtained from build logs

---

### Section 3: Inspect the SBOM (5 min)

**Step 4: View the SBOM**

```
1. In the Konflux UI, on the PipelineRun detail page, scroll down to the 
   "Download SBOM" section

2. Click the "View SBOM" link

3. A new browser tab opens and you'll be prompted to authenticate with TPA 
   (Trusted Profile Analyzer)
   - Click "Log in with OpenShift"
   - If prompted, use your OpenShift credentials:
     - Username: user-{guid}
     - Password: {your OpenShift password}
   - Click "Allow selected permissions" to authorize TPA access

4. After authentication, the SBOM displays as formatted JSON

5. The SBOM shows:
   - Subject: The image digest that was built
   - Predicate type: SPDX or CycloneDX SBOM format
   - Components: List of all packages/dependencies in the image
   - Licenses: License information for each component
   - Version information for each dependency
```

**Expected**: SBOM opens in browser showing image components and dependencies

---

**Step 5: Analyze SBOM Contents**

```
In the browser tab showing the SBOM JSON, examine the structure:

1. Find the "subject" section near the top:
   - Look for the "digest" field
   - Confirm it matches the sha256 digest from Step 3 (build-container logs)
   - This proves the SBOM is for the image you just built

2. Scroll down to find the "components" array:
   - This lists all packages and dependencies in the image
   - Count approximately how many components are listed (e.g., 40-50 dependencies)
   - Each component shows: name, version, type (library/application)

3. Pick any component and examine its details:
   - Name (e.g., "golang.org/x/net")
   - Version (e.g., "v0.15.0")
   - Licenses field (e.g., "BSD-3-Clause", "MIT", "Apache-2.0")
   - Package URL (purl) - standardized identifier

4. Note: This SBOM was automatically generated by Syft during the build-container 
   task. Konflux generates SBOMs for every image without requiring manual configuration.
```

**Expected**: Students understand SBOM structure and what information it contains

---

### Section 4: Review Scan Results and Quay Artifacts (3 min)

**Step 6: Check Vulnerability Scan Results**

```
1. In Konflux UI, on the PipelineRun detail page:
   - Look for a "Security" or "Vulnerabilities" tab
   - Or click on the "tpa-scan" task to see CVE vulnerability scan results
   - The "clamav-scan" task scans for malware/viruses (not CVE vulnerabilities)

2. Review CVE vulnerabilities found by tpa-scan:
   - Critical: (count)
   - High: (count)
   - Medium: (count)
   - Low: (count)

3. Note: Some vulnerabilities are expected (base image dependencies)
   The pipeline should still succeed unless critical CVEs block the build
   TPA (Trusted Profile Analyzer) scans for known CVE vulnerabilities in dependencies
```

**Expected**: Scan results are visible (may include some vulnerabilities)

---

**Step 7: Verify Image in Quay**

```
1. Switch to the Quay browser tab

2. Navigate to "Repositories" (or "Organizations" → user-{guid})

3. You should now see a repository: "sample-component-golang"

4. Click on the repository to open it

5. Click the "Tags" tab

6. Verify you see tags:
   - A tag with the commit SHA (e.g., sha-abc123)
   - Possibly a "latest" tag
   - The image digest should match the one from the build logs

7. Click on a tag to see its details:
   - Size: (image size in MB)
   - Pushed: (timestamp)
   - Security: Click to see vulnerability report (Clair scan results)
```

**Expected**: Image is present in Quay with correct tags and digest

---

**Step 8: Verify Image Manifests**

```
1. In Quay, while viewing the tag details, click "Fetch Tag" or "Manifest"

2. You should see options:
   - Docker Manifest V2, Schema 2
   - OCI manifest

3. Click "View" on one of the manifests

4. The manifest JSON shows:
   - Layers (filesystem layers)
   - Config digest
   - Media types

5. Note: This is the OCI image manifest that was pushed
```

**Expected**: Image manifest is viewable in Quay UI

---

**Key Takeaways**:
- Pipelines-as-Code automatically triggers builds on code pushes
- Konflux pipelines include build, scan, and SBOM generation tasks
- SBOMs are generated in CycloneDX format and attached as attestations
- Vulnerability scans run automatically and report findings
- Built images are pushed to Quay with tags and metadata

---

## Module 04: Signing and Provenance (20 min)

**Learning Objectives**:
- Verify cryptographic image signatures using cosign
- Inspect SLSA Level 3 provenance attestations
- Examine the Rekor transparency log
- Verify the Fulcio certificate chain

**Prerequisites**:
- Module 03 completed
- Image built and pushed to Quay
- Image digest noted

---

### Section 1: Verify Image Signature with cosign (7 min)

**Step 1: Set Up Environment Variables**

```
In the terminal:

# Set your image reference (use the digest from Module 03)
export IMAGE="quay-{cluster}.apps.cluster-{guid}.{domain}/user-{guid}/sample-component-golang@sha256:{digest}"

# Set RHTAS endpoints
export REKOR_URL="https://rekor-server-tsf-tas.apps.cluster-{guid}.{domain}"
export FULCIO_URL="https://fulcio-server-tsf-tas.apps.cluster-{guid}.{domain}"
export TUF_URL="https://tuf-tsf-tas.apps.cluster-{guid}.{domain}"

# Verify variables are set
echo "Image: $IMAGE"
echo "Rekor: $REKOR_URL"
```

**Expected**: Environment variables are set correctly

---

**Step 2: Verify the Image Signature**

```
# Verify signature with cosign
cosign verify \
  --rekor-url "$REKOR_URL" \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  "$IMAGE"

Expected output:
Verification for quay-...
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The signatures were verified against the specified public key

[
  {
    "critical": {
      "identity": {
        "docker-reference": "quay-..."
      },
      "image": {
        "docker-manifest-digest": "sha256:..."
      },
      "type": "cosign container image signature"
    },
    "optional": {
      "Bundle": {
        "SignedEntryTimestamp": "...",
        "Payload": {
          "body": "...",
          "integratedTime": ...,
          "logIndex": ...,
          "logID": "..."
        }
      }
    }
  }
]
```

**Expected**: Signature verification succeeds with JSON output

---

**Step 3: Understand the Signature Output**

```
The cosign verify output shows:
1. "The cosign claims were validated" - The signature is cryptographically valid
2. "Existence ... in the transparency log was verified" - Recorded in Rekor
3. "Signatures were verified" - The signature matches the image

Key fields in JSON:
- docker-manifest-digest: The image digest that was signed
- Bundle.Payload.integratedTime: When the signature was created
- Bundle.Payload.logIndex: Entry number in Rekor transparency log
```

**Expected**: Students understand what each validation means

---

**Step 4: Extract Certificate Information**

```
# Verify and save the certificate
cosign verify \
  --rekor-url "$REKOR_URL" \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  "$IMAGE" 2>&1 | grep -A 50 "Certificate subject"

Expected output (example):
Certificate subject: CN=system:serviceaccount:user-{guid}-tenant:pipeline
Certificate issuer: CN=fulcio.apps.cluster-{guid}.{domain}
```

**Expected**: Certificate subject shows the pipeline ServiceAccount

---

### Section 2: Inspect SLSA Provenance Attestation (7 min)

**Step 5: Download Provenance Attestation**

```
# Download provenance attestation
cosign download attestation "$IMAGE" \
  --predicate-type slsaprovenance \
  | jq -r '.payload' | base64 -d | jq . > provenance.json

# View the provenance
cat provenance.json
```

**Expected**: Provenance JSON is downloaded

---

**Step 6: Analyze Provenance Fields**

```
# Extract the subject (what was built)
jq -r '.subject[].name' provenance.json

Expected: Your image name

jq -r '.subject[].digest.sha256' provenance.json

Expected: Your image digest

# Extract build type (SLSA level indicator)
jq -r '.predicate.buildType' provenance.json

Expected output (example):
https://tekton.dev/chains/v2

# Extract builder identity
jq -r '.predicate.builder.id' provenance.json

Expected output (example):
https://tekton.dev/chains/v2

# This indicates SLSA Level 3 (build platform generated the provenance)
```

**Expected**: Students see the image reference and builder ID

---

**Step 7: Inspect Build Invocation**

```
# View the exact source that was built
jq -r '.predicate.invocation.configSource.uri' provenance.json

Expected: Your GitLab repository URL

jq -r '.predicate.invocation.configSource.digest.sha1' provenance.json

Expected: The git commit SHA from your README.md change

# View build parameters
jq -r '.predicate.invocation.parameters' provenance.json

Expected: Build parameters including branch, revision, etc.
```

**Expected**: Provenance traces back to specific Git commit

---

**Step 8: Examine Build Materials**

```
# List all materials used in the build
jq -r '.predicate.materials[] | "\(.uri) - \(.digest.sha256)"' provenance.json

Expected output (example):
git+https://gitlab-...git - abc123def456...
oci://registry.redhat.io/ubi8/go-toolset - 789ghi012jkl...
oci://registry.access.redhat.com/ubi8/ubi-minimal - 345mno678pqr...

These are:
1. The source repository
2. The builder image (Go toolset)
3. The base image (UBI)
```

**Expected**: All build inputs are recorded with their digests

---

**Step 9: Verify SLSA Level 3 Requirements**

```
Check if provenance meets SLSA Level 3:

1. Builder identity recorded? 
   jq -r '.predicate.builder.id' provenance.json
   ✓ Yes (should show Tekton Chains)

2. Source materials with digests?
   jq -r '.predicate.materials[].digest' provenance.json
   ✓ Yes (should show sha256 digests)

3. Build parameters non-falsifiable?
   jq -r '.predicate.buildType' provenance.json
   ✓ Yes (build platform generated this, not user-provided)

4. Provenance signed by build platform?
   (Already verified in Step 2 with cosign verify)
   ✓ Yes (signature from pipeline ServiceAccount)

Conclusion: This artifact meets SLSA Level 3 requirements!
```

**Expected**: Students confirm SLSA Level 3 compliance

---

### Section 3: Examine Rekor Transparency Log (6 min)

**Step 10: Search Rekor for Your Signature**

```
# Get the Rekor log index from the verify output
REKOR_INDEX=$(cosign verify \
  --rekor-url "$REKOR_URL" \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  "$IMAGE" 2>/dev/null | jq -r '.[0].optional.Bundle.Payload.logIndex')

echo "Rekor log index: $REKOR_INDEX"

# Retrieve the Rekor entry
rekor-cli get --rekor_server "$REKOR_URL" --log-index "$REKOR_INDEX"

Expected output:
LogID: ...
Index: ...
IntegratedTime: ...
UUID: ...
Body: ...
```

**Expected**: Rekor entry is retrieved by index

---

**Step 11: Inspect Rekor Entry Details**

```
# Get full entry as JSON
rekor-cli get --rekor_server "$REKOR_URL" --log-index "$REKOR_INDEX" --format json > rekor-entry.json

# View the entry type
jq -r '.Body.HashedRekordObj.signature.content' rekor-entry.json | base64 -d | head -c 100

# View the public key used
jq -r '.Body.HashedRekordObj.signature.publicKey.content' rekor-entry.json | base64 -d | head -20

Expected: X.509 certificate (begins with -----BEGIN CERTIFICATE-----)

# View the timestamp
jq -r '.IntegratedTime' rekor-entry.json

Expected: Unix timestamp (e.g., 1725739200)

# Convert to human-readable date
date -r $(jq -r '.IntegratedTime' rekor-entry.json)

Expected: Date and time when the signature was recorded
```

**Expected**: Students understand Rekor stores tamper-evident records

---

**Step 12: Verify Rekor Inclusion Proof**

```
# Rekor provides a cryptographic proof that an entry exists in the log
# This proof can be verified independently

rekor-cli verify --rekor_server "$REKOR_URL" \
  --artifact "$IMAGE" \
  --signature <(cosign download signature "$IMAGE")

Expected output:
Inclusion Proof:
...
Current Root Hash: ...
Verification Successful!

Note: This proves the entry was included in the transparency log
and cannot be retroactively modified.
```

**Expected**: Inclusion proof verification succeeds

---

**Step 13: Browse Rekor UI (Optional)**

```
1. Open the Rekor Search UI in a browser:
   https://rekor-search-ui-tsf-tas.apps.cluster-{guid}.{domain}

2. Search options:
   - Search by UUID (from rekor-cli output)
   - Search by log index
   - Search by artifact digest

3. Enter your image digest or log index

4. View the entry in the web UI:
   - Shows the same information as CLI
   - Displays certificate details
   - Shows signature algorithm
   - Provides download links
```

**Expected**: Entry is visible in Rekor UI

---

**Key Takeaways**:
- cosign verifies signatures using certificates from Fulcio (no long-lived keys)
- SLSA provenance attestations record what was built, from where, and how
- SLSA Level 3 requires build platforms to generate non-falsifiable provenance
- Rekor provides a tamper-evident transparency log for all signatures
- Inclusion proofs ensure signatures cannot be retroactively removed or modified

---

## Module 05: Integration Testing and Policy (15 min)

**Learning Objectives**:
- Understand IntegrationTestScenario resources
- Observe Conforma (Enterprise Contract) policy checks
- See how failed policy checks block promotion
- Understand the role of Snapshots in the release workflow

**Prerequisites**:
- Module 04 completed
- Image is signed with provenance attestation
- Integration pipeline has run (auto-triggered)

---

### Section 1: Understand Integration Test Scenarios (5 min)

**Step 1: List IntegrationTestScenarios**

```
# In the terminal, check for auto-created integration test scenarios
oc get integrationtestscenarios -n user-{guid}-tenant

Expected output:
NAME                              APPLICATION      AGE
sample-app-default-integration    my-sample-app    15m

Note: Konflux auto-creates a default IntegrationTestScenario when you 
create a Component. This scenario runs policy checks on every build.
```

**Expected**: Default IntegrationTestScenario exists

---

**Step 2: Inspect the IntegrationTestScenario**

```
# Get details
oc get integrationtestscenario sample-app-default-integration \
  -n user-{guid}-tenant -o yaml > integration-test-scenario.yaml

# View the spec
cat integration-test-scenario.yaml

Key fields to note:
- spec.application: Links to your Application
- spec.resolverRef: Points to the test pipeline definition
- spec.params: Parameters passed to the test pipeline

# View just the resolver reference
oc get integrationtestscenario sample-app-default-integration \
  -n user-{guid}-tenant -o jsonpath='{.spec.resolverRef}' | jq .

Expected output (example):
{
  "resolver": "git",
  "params": [
    {"name": "url", "value": "https://github.com/konflux-ci/integration-examples"},
    {"name": "revision", "value": "main"},
    {"name": "pathInRepo", "value": "pipelines/enterprise-contract.yaml"}
  ]
}

This means the integration test uses an Enterprise Contract (Conforma) 
pipeline from the Konflux integration examples repository.
```

**Expected**: IntegrationTestScenario references a policy pipeline

---

**Step 3: Understand Snapshots**

```
A Snapshot is created every time a Component build completes successfully.
It represents a consistent set of Component versions ready for testing/release.

# List Snapshots
oc get snapshots -n user-{guid}-tenant --sort-by=.metadata.creationTimestamp

Expected output:
NAME                          APPLICATION      AGE
my-sample-app-abc123          my-sample-app    10m
my-sample-app-xyz456          my-sample-app    2m

# Get the most recent Snapshot
LATEST_SNAPSHOT=$(oc get snapshots -n user-{guid}-tenant \
  --sort-by=.metadata.creationTimestamp -o name | tail -1)

echo "Latest Snapshot: $LATEST_SNAPSHOT"

# View Snapshot details
oc get $LATEST_SNAPSHOT -n user-{guid}-tenant -o yaml > snapshot.yaml
cat snapshot.yaml
```

**Expected**: Snapshots exist for each completed build

---

### Section 2: Observe Policy Checks (6 min)

**Step 4: Check Snapshot Status**

```
# View integration test results in the Snapshot
oc get $LATEST_SNAPSHOT -n user-{guid}-tenant \
  -o jsonpath='{.status.conditions}' | jq .

Expected output:
[
  {
    "type": "IntegrationTestSucceeded",
    "status": "True",
    "reason": "Succeeded",
    "message": "Integration test passed"
  }
]

If status is "False", the policy check failed.
```

**Expected**: Integration test status is visible

---

**Step 5: Find the Integration Test PipelineRun**

```
# Integration tests run as PipelineRuns
# List PipelineRuns and find the integration test
oc get pipelineruns -n user-{guid}-tenant \
  --sort-by=.metadata.creationTimestamp

Expected: You'll see build PipelineRuns AND integration test PipelineRuns

Look for a PipelineRun with a name like:
  integration-test-sample-app-abc123

# Describe the integration test PipelineRun
INTEGRATION_RUN=$(oc get pipelineruns -n user-{guid}-tenant \
  -l 'appstudio.openshift.io/snapshot' \
  --sort-by=.metadata.creationTimestamp -o name | tail -1)

oc describe $INTEGRATION_RUN -n user-{guid}-tenant
```

**Expected**: Integration test PipelineRun is found

---

**Step 6: View Conforma Policy Results**

```
The integration test pipeline runs the "ec" (Enterprise Contract) CLI 
to validate the artifact against policy rules.

# Get the PipelineRun result (TaskRun logs contain policy output)
oc logs $INTEGRATION_RUN -n user-{guid}-tenant --all-containers | grep -A 50 "ec validate"

Expected output (example):
Running: ec validate image --image quay-...
Policy check results:
✓ Required SLSA provenance attestation found
✓ Image signature verified
✓ No critical CVEs found
✓ Base image is from trusted source
✓ Build materials recorded with digests

Success: 5 checks passed, 0 failures
```

**Expected**: Policy check output shows passed rules

---

**Step 7: Inspect Policy Bundle**

```
The Enterprise Contract policy is defined in a policy bundle.

# Get the policy reference from the IntegrationTestScenario
oc get integrationtestscenario sample-app-default-integration \
  -n user-{guid}-tenant -o yaml | grep -A 10 "policy"

Expected output (example):
  params:
    - name: POLICY_CONFIGURATION
      value: "github.com/enterprise-contract/config//default"

This points to a policy bundle that defines:
- Required attestations (SLSA provenance, SBOM)
- Signature requirements
- Vulnerability thresholds
- Approved base images
- Other supply chain rules
```

**Expected**: Policy bundle reference is identified

---

### Section 3: Understand Promotion Blocking (4 min)

**Step 8: Simulate a Policy Failure (Read-Only)**

```
In a real scenario, if the policy check fails:

1. The Snapshot condition would show:
   type: IntegrationTestSucceeded
   status: "False"
   reason: "PolicyCheckFailed"
   message: "Critical CVE detected: CVE-2023-12345"

2. The Snapshot would NOT be eligible for release:
   - You cannot create a Release referencing this Snapshot
   - The Release API would reject it

3. The failed policy output would show:
   ✗ Critical CVE found: CVE-2023-12345 in package libfoo
   Policy rule violated: critical-cve-threshold

This is how Conforma blocks insecure artifacts from reaching production.
```

**Expected**: Students understand the blocking mechanism

---

**Step 9: View Policy Check in Konflux UI**

```
1. Switch to the Konflux UI browser tab

2. Navigate to your Application → Activity

3. Locate the Snapshot entry for your latest build

4. Click on the Snapshot to view details

5. You should see:
   - Integration test status: Passed (green checkmark)
   - Policy check results: Succeeded
   - Link to integration test PipelineRun

6. Optional: Click the PipelineRun link to view logs in the UI
```

**Expected**: Konflux UI shows integration test status

---

**Step 10: Verify Snapshot is Releasable**

```
# A Snapshot is releasable if integration tests passed
oc get $LATEST_SNAPSHOT -n user-{guid}-tenant \
  -o jsonpath='{.metadata.labels}' | jq .

Expected: You should see a label indicating release readiness
(exact label name may vary by Konflux version)

Example:
{
  "appstudio.openshift.io/snapshot-release-ready": "true"
}

This label signals that the Snapshot passed policy checks and can be released.
```

**Expected**: Snapshot is marked as releasable

---

**Key Takeaways**:
- IntegrationTestScenarios define policy checks that run on every build
- Snapshots represent consistent sets of Component versions
- Conforma (Enterprise Contract) validates artifacts against policy rules
- Failed policy checks prevent Snapshots from being released
- Policy bundles define security and compliance requirements centrally
- The integration test PipelineRun executes the policy validation

---

## Module 06: Release to Production (15 min)

**Learning Objectives**:
- Create a ReleasePlan to define the release strategy
- Trigger a Release referencing a policy-verified Snapshot
- Observe the release pipeline execution
- Verify the signed image in the production Quay repository
- Trace the full artifact lifecycle from commit to production

**Prerequisites**:
- Module 05 completed
- Snapshot exists with integration tests passed
- Snapshot is marked as releasable

---

### Section 1: Understand the Release Workflow (3 min)

**Instruction**:
```
Konflux release workflow:

1. ReleasePlan (created by user):
   - Defines release strategy (target, automation)
   - Lives in the user's tenant namespace
   - References the Application

2. ReleasePlanAdmission (pre-created by admin):
   - Defines target environment constraints
   - Lives in the managed namespace
   - May enforce additional policy checks

3. Release (created by user):
   - References a specific Snapshot to release
   - Triggers the release pipeline
   - Tracks release status

4. Release Pipeline:
   - Copies signed image to target registry
   - May run additional checks
   - Updates deployment manifests (if applicable)

In this lab:
- ReleasePlan: You will create
- ReleasePlanAdmission: Pre-created (in user-{guid}-managed namespace)
- Release: You will create
```

**Expected**: Students understand the release objects

---

### Section 2: Create a ReleasePlan (4 min)

**Step 1: Check for Pre-Created ReleasePlanAdmission**

```
# Check the managed namespace for ReleasePlanAdmission
oc get releaseplanadmissions -n user-{guid}-managed

Expected output:
NAME                  AGE
production-release    20m

If no ReleasePlanAdmission exists, create one (normally pre-created):

cat <<EOF | oc apply -f -
apiVersion: appstudio.redhat.com/v1alpha1
kind: ReleasePlanAdmission
metadata:
  name: production-release
  namespace: user-{guid}-managed
spec:
  applications:
    - my-sample-app
  origin: user-{guid}-tenant
  policy: default-policy
EOF
```

**Expected**: ReleasePlanAdmission exists in managed namespace

---

**Step 2: Create a ReleasePlan**

```
# Create ReleasePlan in your tenant namespace
cat <<EOF | oc apply -f -
apiVersion: appstudio.redhat.com/v1alpha1
kind: ReleasePlan
metadata:
  name: production-release
  namespace: user-{guid}-tenant
spec:
  application: my-sample-app
  target: user-{guid}-managed
  releaseGracePeriodDays: 0
EOF

# Verify ReleasePlan was created
oc get releaseplans -n user-{guid}-tenant

Expected output:
NAME                  APPLICATION      TARGET                  AGE
production-release    my-sample-app    user-{guid}-managed     5s
```

**Expected**: ReleasePlan is created

---

**Step 3: Verify ReleasePlan Configuration**

```
# View ReleasePlan details
oc get releaseplan production-release -n user-{guid}-tenant -o yaml

Key fields:
- spec.application: Links to your Application
- spec.target: Target namespace (user-{guid}-managed)
- spec.releaseGracePeriodDays: How long to wait before release (0 = immediate)

# Optional: View ReleasePlanAdmission
oc get releaseplanadmission production-release -n user-{guid}-managed -o yaml

Key fields:
- spec.applications: Allowed Applications
- spec.origin: Source namespace (user-{guid}-tenant)
- spec.policy: Policy to apply during release
```

**Expected**: ReleasePlan configuration is correct

---

### Section 3: Trigger a Release (3 min)

**Step 4: Get the Latest Releasable Snapshot**

```
# List Snapshots
oc get snapshots -n user-{guid}-tenant --sort-by=.metadata.creationTimestamp

# Get the latest Snapshot name
SNAPSHOT_NAME=$(oc get snapshots -n user-{guid}-tenant \
  --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

echo "Releasing Snapshot: $SNAPSHOT_NAME"

# Verify the Snapshot passed integration tests
oc get snapshot $SNAPSHOT_NAME -n user-{guid}-tenant \
  -o jsonpath='{.status.conditions[?(@.type=="IntegrationTestSucceeded")].status}'

Expected output: True
```

**Expected**: Snapshot name is obtained and verified

---

**Step 5: Create a Release**

```
# Create Release object
cat <<EOF | oc apply -f -
apiVersion: appstudio.redhat.com/v1alpha1
kind: Release
metadata:
  name: production-release-$(date +%Y%m%d-%H%M%S)
  namespace: user-{guid}-tenant
spec:
  releasePlan: production-release
  snapshot: $SNAPSHOT_NAME
EOF

# Verify Release was created
oc get releases -n user-{guid}-tenant

Expected output:
NAME                             RELEASPLAN           SNAPSHOT                 AGE
production-release-20260907...   production-release   my-sample-app-xyz456     5s
```

**Expected**: Release object is created

---

### Section 4: Monitor Release Execution (5 min)

**Step 6: Watch Release Status**

```
# Get the Release name
RELEASE_NAME=$(oc get releases -n user-{guid}-tenant \
  --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

# Watch Release status
oc get release $RELEASE_NAME -n user-{guid}-tenant -w

Expected status progression:
PHASE
Pending
Running
Succeeded

Press Ctrl+C to stop watching after status shows "Succeeded"

Typical execution time: 2-5 minutes
```

**Expected**: Release transitions to Succeeded

---

**Step 7: Find the Release PipelineRun**

```
# The Release triggers a PipelineRun in the managed namespace
oc get pipelineruns -n user-{guid}-managed

Expected output:
NAME                              SUCCEEDED   REASON      AGE
release-production-release-abc    True        Succeeded   2m

# View PipelineRun details
RELEASE_RUN=$(oc get pipelineruns -n user-{guid}-managed \
  --sort-by=.metadata.creationTimestamp -o name | tail -1)

oc describe $RELEASE_RUN -n user-{guid}-managed

# View logs
oc logs $RELEASE_RUN -n user-{guid}-managed --all-containers
```

**Expected**: Release PipelineRun completed successfully

---

**Step 8: Verify Image in Production Quay Repository**

```
1. Switch to the Quay browser tab

2. Navigate to your organization: user-{guid}

3. Look for a NEW repository or NEW tag:
   - Repository: sample-component-golang (same as dev)
   - Tag: May have a "production" or "release" tag

4. Alternatively, check if images were promoted to a different Quay organization:
   - Navigate to "Organizations" and check if a "user-{guid}-prod" org exists

5. Click on the tag/image to verify:
   - Digest matches the Snapshot's image digest
   - Security scan results are present
   - Pushed timestamp is recent (within last 5 minutes)

Note: The exact target location depends on ReleasePlanAdmission configuration
```

**Expected**: Image is present in production target

---

**Step 9: Verify Release Details in Konflux UI**

```
1. Switch to the Konflux UI browser tab

2. Navigate to your Application → Releases

3. You should see your Release listed:
   - Release name: production-release-20260907...
   - Status: Succeeded
   - Snapshot: my-sample-app-xyz456
   - Target: user-{guid}-managed

4. Click on the Release to view details:
   - Timeline of events
   - Link to release PipelineRun
   - Image digests
   - Target environment
```

**Expected**: Release is visible in Konflux UI with Succeeded status

---

**Step 10: Trace Full Artifact Lifecycle**

```
Review the complete journey of your artifact:

1. Source Commit:
   - GitLab: README.md change (Module 03)
   - Commit SHA: {from provenance.json}

2. Build:
   - PipelineRun: sample-app-on-push-xyz456 (Module 03)
   - Image pushed to Quay with digest: sha256:abc123...

3. Signing:
   - Tekton Chains signed the image (Module 04)
   - Signature recorded in Rekor log
   - Provenance attestation attached

4. Policy Check:
   - IntegrationTestScenario ran (Module 05)
   - Conforma validated SLSA provenance, signature, CVEs
   - Snapshot marked as releasable

5. Release:
   - Release created referencing Snapshot (Module 06)
   - Release PipelineRun executed
   - Image promoted to production

6. Production:
   - Signed, provenance-attested image in production Quay
   - Full audit trail from commit → production
   - Supply chain integrity verified at every step

You can trace this entire chain using:
- Git commit → Provenance.invocation.configSource.digest
- Image digest → Constant throughout (immutable)
- Rekor log → Signature timestamp and inclusion proof
- Snapshot → Links Component versions to integration test results
- Release → Links Snapshot to production deployment
```

**Expected**: Students understand the full lifecycle

---

**Key Takeaways**:
- ReleasePlans define release strategies and targets
- ReleasePlanAdmissions control what can be released to specific namespaces
- Releases trigger release pipelines that promote verified artifacts
- Only Snapshots that passed policy checks can be released
- The entire artifact lifecycle is traceable from commit to production
- Every release is backed by cryptographic proof and audit logs

---

## Module 07: Real-World Incident Response (25 min)

**Learning Objectives**:
- Diagnose supply chain failures using Conforma and cosign
- Understand how unsigned artifacts are detected and blocked
- Analyze CVE policy violations
- Identify configuration drift scenarios
- Articulate which layer of the supply chain caught each problem

**Prerequisites**:
- All previous modules completed
- Understanding of signing, policy checks, and releases

---

### Scenario A: The Unsigned Hotfix (8 min)

**Context**:
```
A developer bypassed the Konflux pipeline during an incident and pushed 
an image directly to Quay using docker push. The image is unsigned and 
has no SLSA provenance attestation. They try to release it through the 
ReleasePlan.

This simulates a common customer incident pattern: emergency hotfixes 
that skip the normal build process.
```

---

**Step 1: Set Up Scenario (Pre-Provisioned)**

```
The lab environment includes a pre-built "unsigned hotfix" image for demonstration.

# Set the unsigned image reference
HOTFIX_IMAGE="quay-{cluster}.apps.cluster-{guid}.{domain}/lab-examples/unsigned-hotfix@sha256:{hotfix-digest}"

# This image was pushed directly to Quay without going through Konflux
# It has no signature and no provenance attestation
```

**Expected**: Hotfix image reference is set

---

**Step 2: Attempt Signature Verification**

```
# Try to verify the signature on the hotfix image
cosign verify \
  --rekor-url "$REKOR_URL" \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  "$HOTFIX_IMAGE"

Expected error:
Error: no matching signatures:
 - fetching signatures: no signatures associated with the image

This error means:
1. No signature is attached to the image manifest
2. The image was NOT signed by Tekton Chains
3. It cannot be verified cryptographically
```

**Expected**: Signature verification fails with clear error message

---

**Step 3: Run Conforma Policy Validation**

```
# Validate the unsigned image against Conforma policy
ec validate image \
  --image "$HOTFIX_IMAGE" \
  --policy "github.com/enterprise-contract/config//default" \
  --output json | jq .

Expected output (abbreviated):
{
  "success": false,
  "components": [
    {
      "violations": [
        {
          "msg": "Required attestation type not found: slsaprovenance",
          "metadata": {
            "code": "attestation_type.known_attestation_type"
          }
        },
        {
          "msg": "Image signature verification failed",
          "metadata": {
            "code": "attestation_signature_check.signature_valid"
          }
        }
      ]
    }
  ]
}

# Filter to show only violation messages
ec validate image \
  --image "$HOTFIX_IMAGE" \
  --policy "github.com/enterprise-contract/config//default" \
  --output json | jq '.components[].violations[] | {rule: .metadata.code, msg: .msg}'

Expected violations:
1. "attestation_type.known_attestation_type" - Missing SLSA provenance
2. "attestation_signature_check.signature_valid" - No valid signature
```

**Expected**: Policy validation fails with specific rule violations

---

**Step 4: Understand the Blocking Mechanism**

```
What happens if someone tries to release this image?

1. If they create a Snapshot manually referencing this image:
   - IntegrationTestScenario would run
   - Conforma would fail (as shown above)
   - Snapshot status would show: IntegrationTestSucceeded=False

2. If they try to create a Release with a failed Snapshot:
   - Konflux Release API would reject it
   - Error: "Cannot release Snapshot with failed integration tests"

3. Even if they bypass Konflux and push directly to production namespace:
   - Admission controllers (if configured) would reject unsigned images
   - Or runtime policy engines (e.g., RHACS) would flag it

The supply chain security stack has multiple defense layers.
```

**Expected**: Students understand multi-layered blocking

---

**Step 5: Diagnosis Summary**

```
Question: What should the developer do?

Answer:
1. Do NOT push images directly to Quay
2. Make the code change in GitLab
3. Commit and push to trigger the Konflux pipeline
4. Wait for the signed build to complete
5. Release the signed, provenance-attested artifact

Question: What if it's a true emergency?

Answer:
- Emergency procedures should still use the pipeline
- Pipelines can be fast (5-10 minutes)
- Skipping the pipeline creates security debt
- If you MUST push directly, you must re-build through the pipeline
  before the artifact can be released

Which layer caught this?
→ Policy layer (Conforma Enterprise Contract)
```

**Expected**: Students identify the remediation path

---

### Scenario B: The CVE Policy Breach (10 min)

**Context**:
```
A new critical CVE is discovered in a base image dependency. The 
integration policy has been updated to block images with this CVE. 
An artifact that previously passed policy now fails on re-evaluation.

This simulates a policy tightening event: the image didn't change, 
but the policy did.
```

---

**Step 6: Set Up Scenario (Pre-Provisioned)**

```
The lab environment includes a pre-built "vulnerable" image that 
contains a dependency with a known CVE.

# Set the vulnerable image reference
CVE_IMAGE="quay-{cluster}.apps.cluster-{guid}.{domain}/lab-examples/cve-sample@sha256:{cve-digest}"

# This image has:
- Valid signature (it WAS built through Konflux)
- SLSA provenance attestation
- But contains: CVE-2023-45678 in package libcurl

The CVE was added to the policy blocklist AFTER this image was built.
```

**Expected**: CVE image reference is set

---

**Step 7: Verify the Image IS Signed**

```
# First, verify this image IS signed (unlike Scenario A)
cosign verify \
  --rekor-url "$REKOR_URL" \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  "$CVE_IMAGE"

Expected output:
Verification for quay-...
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The signatures were verified against the specified public key
[...]

This confirms:
✓ The image IS signed
✓ The signature is valid
✓ It was built through the proper pipeline

But signing alone is not enough — policy checks are separate!
```

**Expected**: Signature verification succeeds (different from Scenario A)

---

**Step 8: Run Policy Validation and Observe CVE Failure**

```
# Validate the vulnerable image against policy
ec validate image \
  --image "$CVE_IMAGE" \
  --policy "github.com/enterprise-contract/config//default" \
  --output json | jq .

Expected output (abbreviated):
{
  "success": false,
  "components": [
    {
      "violations": [
        {
          "msg": "Critical CVE found: CVE-2023-45678 in package libcurl version 7.68.0",
          "metadata": {
            "code": "cve.critical_vulnerabilities",
            "severity": "CRITICAL",
            "cve": "CVE-2023-45678",
            "package": "libcurl",
            "version": "7.68.0"
          }
        }
      ]
    }
  ]
}

# Extract just the CVE information
ec validate image \
  --image "$CVE_IMAGE" \
  --policy "github.com/enterprise-contract/config//default" \
  --output json | jq '.components[].violations[] | select(.metadata.cve) | {cve: .metadata.cve, package: .metadata.package, severity: .metadata.severity}'

Expected output:
{
  "cve": "CVE-2023-45678",
  "package": "libcurl",
  "severity": "CRITICAL"
}
```

**Expected**: Policy validation fails due to CVE

---

**Step 9: Inspect the SBOM to Confirm the Vulnerable Package**

```
# Download the SBOM from the vulnerable image
cosign download attestation "$CVE_IMAGE" \
  | jq -r '.payload' | base64 -d | jq . > cve-sbom.json

# Search for the vulnerable package in the SBOM
jq -r '.predicate.components[] | select(.name == "libcurl") | {name: .name, version: .version, purl: .purl}' cve-sbom.json

Expected output:
{
  "name": "libcurl",
  "version": "7.68.0",
  "purl": "pkg:deb/ubuntu/libcurl@7.68.0"
}

This confirms the SBOM recorded the vulnerable dependency.
The policy engine uses the SBOM to detect CVEs.
```

**Expected**: Vulnerable package is found in SBOM

---

**Step 10: Simulate Release Blocking**

```
If someone tried to release this image:

1. Create a Snapshot referencing this image (manually)
2. IntegrationTestScenario runs
3. Conforma policy check fails (as shown above)
4. Snapshot status:
   conditions:
     - type: IntegrationTestSucceeded
       status: "False"
       reason: "PolicyCheckFailed"
       message: "Critical CVE detected: CVE-2023-45678"

5. Attempt to create Release:
   - Konflux rejects: "Cannot release Snapshot with failed integration tests"

The release is BLOCKED even though the image is validly signed.
```

**Expected**: Students understand policy != signature

---

**Step 11: Diagnosis and Remediation**

```
Question: Why did this image pass policy before but fail now?

Answer:
- The CVE database was updated (new CVE published)
- Or the policy was tightened (CVE added to blocklist)
- The image content didn't change, but the evaluation criteria did

Question: How to remediate?

Answer:
1. Update the base image to a patched version (e.g., libcurl 7.88.1)
2. Rebuild the application through Konflux
3. New Snapshot is created with updated dependencies
4. Policy re-evaluates against new SBOM
5. If CVE is resolved, policy check passes
6. New artifact becomes releasable

Question: What if the CVE has no fix yet?

Answer:
- Option A: Accept the risk with a policy exception (requires approval)
- Option B: Switch to an alternative package
- Option C: Delay release until fix is available

Which layer caught this?
→ Policy layer (Conforma Enterprise Contract + vulnerability scanning)
```

**Expected**: Students understand remediation path

---

### Scenario C: Config Drift and Key Mismatch (7 min)

**Context**:
```
A signing key rotation was performed on the cluster, but the Conforma 
policy was not updated to trust the new key. Or: the policy bundle 
reference was changed to a version with a stricter certificate identity 
pattern that no longer matches the builder used in this cluster.

This simulates a common operational mistake: infrastructure changes 
that are not reflected in policy configuration.
```

---

**Step 12: Set Up Scenario (Pre-Provisioned)**

```
The lab environment includes a pre-built image that was signed with a 
certificate identity that does not match the current policy's trusted 
signer configuration.

# Set the drifted image reference
DRIFTED_IMAGE="quay-{cluster}.apps.cluster-{guid}.{domain}/lab-examples/key-drift@sha256:{drift-digest}"

# This image was signed by a ServiceAccount in a different namespace,
# or with a different certificate identity than policy expects.
```

**Expected**: Drifted image reference is set

---

**Step 13: Attempt Signature Verification with Mismatched Identity**

```
# Try to verify with a strict certificate identity filter
cosign verify \
  --rekor-url "$REKOR_URL" \
  --certificate-identity="system:serviceaccount:user-{guid}-tenant:pipeline" \
  --certificate-oidc-issuer-regexp ".*" \
  "$DRIFTED_IMAGE"

Expected error:
Error: no matching signatures:
 - none of the expected identities matched what was in the certificate

# Now verify with relaxed identity (to see what the actual identity is)
cosign verify \
  --rekor-url "$REKOR_URL" \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  "$DRIFTED_IMAGE" 2>&1 | grep "Certificate subject"

Expected output:
Certificate subject: CN=system:serviceaccount:different-namespace:pipeline

This shows the image WAS signed, but by a different identity than expected.
```

**Expected**: Identity mismatch is detected

---

**Step 14: Run Policy Validation**

```
# Validate the drifted image
ec validate image \
  --image "$DRIFTED_IMAGE" \
  --policy "github.com/enterprise-contract/config//default" \
  --output json | jq .

Expected output (abbreviated):
{
  "success": false,
  "components": [
    {
      "violations": [
        {
          "msg": "Signature verification failed: certificate subject does not match policy",
          "metadata": {
            "code": "attestation_signature_check.signature_key_trusted",
            "expected": "system:serviceaccount:user-{guid}-tenant:pipeline",
            "actual": "system:serviceaccount:different-namespace:pipeline"
          }
        }
      ]
    }
  ]
}

The policy requires signatures from a specific ServiceAccount.
This image was signed by a different ServiceAccount.
```

**Expected**: Policy fails due to certificate identity mismatch

---

**Step 15: Diagnosis and Remediation**

```
Question: What caused this drift?

Answer (possible scenarios):
1. The cluster was rebuilt and ServiceAccount identities changed
2. The signing key was rotated and policy wasn't updated
3. The policy bundle was updated to require a stricter identity
4. The image was built in a different cluster/namespace and imported

Question: How to remediate?

Answer:
- Option A: Update the policy to trust the new certificate identity
- Option B: Rebuild the image in the correct namespace with correct identity
- Option C: If this is a key rotation, update policy to trust both old and new keys during transition period

Question: How to prevent this?

Answer:
- Automate policy updates alongside infrastructure changes
- Test policy changes in staging before production
- Use policy version control and change tracking
- Maintain a registry of trusted signers

Which layer caught this?
→ Policy layer (Conforma Enterprise Contract signature validation)
```

**Expected**: Students understand config drift detection

---

**Summary: Which Layer Catches What**

```
Supply Chain Security Layers:

1. Build Layer (Konflux + Tekton):
   - Ensures consistent build process
   - Generates SBOM and provenance
   - NOT caught here: Unsigned hotfix (Scenario A)
     → Because it bypassed the build

2. Signing Layer (Tekton Chains + RHTAS):
   - Cryptographically signs artifacts
   - Records in Rekor transparency log
   - Caught here: Unsigned hotfix (Scenario A)
     → cosign verify failed

3. Policy Layer (Conforma / Enterprise Contract):
   - Validates signatures, provenance, SBOMs
   - Checks CVEs, base images, attestations
   - Caught here: All scenarios
     → CVE policy breach (Scenario B)
     → Key mismatch (Scenario C)
     → Unsigned image (Scenario A)

4. Release Layer (Konflux Release API):
   - Enforces integration test pass before release
   - Blocks Snapshots with failed policy checks
   - Caught here: All scenarios
     → Rejects Releases of failed Snapshots

5. Runtime Layer (admission controllers, RHACS):
   - Enforces policy at deployment time
   - Can reject unsigned or policy-failed images
   - Caught here: Would catch all scenarios if configured

Defense in depth: Multiple layers ensure failures are caught.
```

**Expected**: Students understand the security stack

---

**Key Takeaways**:
- Unsigned artifacts are detected by cosign verification failures
- Policy checks are separate from signature checks (signing ≠ compliance)
- CVE policy violations prevent releases even if signatures are valid
- Certificate identity mismatches indicate configuration drift
- The supply chain has multiple defensive layers (build, sign, policy, release, runtime)
- SBOMs enable vulnerability detection at policy evaluation time
- Remediation always involves rebuilding through the proper pipeline

---

## Appendix: Pre-Provisioned Environment

**This section documents what is auto-provisioned by the lab automation**

### Cluster-Level Resources

Created by the cluster workload (`ocp4_workload_trusted_software_factory` + others):

| Resource | Namespace | Purpose |
|----------|-----------|---------|
| S4 (MinIO) | s4 | Object storage for Quay backend |
| Quay Registry | quay-enterprise | Container image registry |
| GitLab | gitlab | Source control with runners |
| OpenShift GitOps | openshift-gitops | ArgoCD for GitOps workflows |
| Konflux UI | konflux-ui | Konflux web interface |
| Konflux Operator | openshift-operators | Manages Konflux CRDs |
| RHTAS Fulcio | tsf-tas | Certificate authority for signing |
| RHTAS Rekor | tsf-tas | Transparency log |
| RHTAS TUF | tsf-tas | Root of trust |
| Keycloak | tsf-keycloak | SSO for Konflux |
| TPA | tsf-tpa | Trusted Profile Analyzer |
| Pipeline-as-Code | openshift-pipelines | GitLab webhook integration |
| ClusterRole | cluster-wide | konflux-admin-user-actions |

---

### Per-User Resources

Created by the tenant workload (`ocp4_workload_tenant_*` + `ocp4_workload_konflux_tssc_tenant`):

| Resource | Location | Purpose |
|----------|----------|---------|
| Tenant namespace | user-{guid}-tenant | Konflux workspace |
| Managed namespace | user-{guid}-managed | Production/release target |
| Showroom namespace | user-{guid}-showroom | Lab guide + terminal |
| GitLab user account | gitlab | Source control access |
| GitLab repository | gitlab/user-{guid}/sample-component-golang | Pre-imported sample app |
| Quay user account | quay-enterprise | Registry access |
| HTPasswd user | cluster-wide | OpenShift console login |
| RoleBinding | user-{guid}-tenant | Bind user to konflux-admin-user-actions |
| RoleBinding | user-{guid}-managed | Bind user to konflux-admin-user-actions |
| Showroom deployment | user-{guid}-showroom | Lab guide with Wetty terminal |

---

### What Students Create

These are NOT pre-provisioned (students create during the lab):

| Resource | Module | Purpose |
|----------|--------|---------|
| Konflux Application | Module 02 | Container for Components |
| Konflux Component | Module 02 | Links GitLab repo to build pipeline |
| .tekton/ directory | Module 02 | PipelineRun manifests (auto-committed by Konflux) |
| PipelineRuns | Module 02-03 | Build executions |
| Snapshots | Module 05 | Auto-created after builds |
| IntegrationTestScenarios | Module 05 | Auto-created with Component |
| ReleasePlan | Module 06 | Release strategy definition |
| Release | Module 06 | Triggers release pipeline |

---

### Environment URLs

Students need these URLs (provided in lab guide):

```bash
# OpenShift
export OPENSHIFT_CONSOLE=https://console-openshift-console.apps.cluster-{guid}.{domain}
export OPENSHIFT_API=https://api.cluster-{guid}.{domain}:6443

# Konflux
export KONFLUX_UI=https://konflux-ui-konflux-ui.apps.cluster-{guid}.{domain}

# GitLab
export GITLAB_URL=https://gitlab-gitlab.apps.cluster-{guid}.{domain}

# Quay
export QUAY_URL=https://quay-{cluster}.apps.cluster-{guid}.{domain}

# RHTAS
export REKOR_URL=https://rekor-server-tsf-tas.apps.cluster-{guid}.{domain}
export FULCIO_URL=https://fulcio-server-tsf-tas.apps.cluster-{guid}.{domain}
export TUF_URL=https://tuf-tsf-tas.apps.cluster-{guid}.{domain}

# Keycloak
export KEYCLOAK_URL=https://keycloak-tsf-keycloak.apps.cluster-{guid}.{domain}
```

---

### User Credentials

```bash
# All passwords are the same across GitLab, Quay, and OpenShift
Username: user-{guid}
Password: {provided in provisioning email}

# Namespaces
Tenant namespace: user-{guid}-tenant
Managed namespace: user-{guid}-managed
Showroom namespace: user-{guid}-showroom
```

---

### Sample Application Repository

Pre-imported from: `https://github.com/konflux-ci/sample-component-golang.git`

**Repository structure**:
```
sample-component-golang/
├── main.go                # Simple HTTP server (Go)
├── go.mod                 # Go module definition
├── go.sum                 # Dependency checksums
├── Dockerfile             # Container build definition
└── README.md              # Repository documentation
```

**Application behavior**:
- HTTP server listening on port 8080
- Endpoint: `GET /` returns "Hello, World!"
- Built with Go 1.21
- Base image: registry.access.redhat.com/ubi8/go-toolset

---

### ClusterRole Permissions

The `konflux-admin-user-actions` ClusterRole grants these permissions in bound namespaces:

```yaml
# Konflux resources (full CRUD)
- applications.appstudio.redhat.com: [*]
- components.appstudio.redhat.com: [*]
- releaseplans.appstudio.redhat.com: [*]
- releases.appstudio.redhat.com: [*]
- integrationtestscenarios.appstudio.redhat.com: [*]
- snapshots.appstudio.redhat.com: [*]
- enterprisecontractpolicies.appstudio.redhat.com: [*]

# Tekton resources (read + write PipelineRuns)
- pipelineruns.tekton.dev: [create, get, list, watch, delete]
- pipelines.tekton.dev: [get, list, watch]
- taskruns.tekton.dev: [get, list, watch]

# Namespace resources (full CRUD)
- secrets: [*]
- configmaps: [*]
- serviceaccounts: [get, list, watch, patch, update]

# Inspection (read-only)
- pods: [get, list, watch]
- pods/log: [get, list, watch]
```

---

**End of Implementation Guide**
