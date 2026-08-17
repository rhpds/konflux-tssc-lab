# konflux-tssc-lab

# Build, Sign, and Ship: Securing the Software Supply Chain with Konflux

Modern software supply chains demand more than just building and deploying code — they require cryptographic proof of provenance, automated vulnerability scanning, and policy-enforced releases. In this 90-minute hands-on lab, you'll experience the complete secure software lifecycle using **Konflux**, Red Hat's next-generation build and release platform.

Working in your own tenant workspace on a shared OpenShift cluster, you'll onboard a real application from a GitLab repository, trigger automated builds via Pipelines-as-Code, and watch Konflux generate SBOMs, sign your artifacts with **Trusted Artifact Signer**, and produce SLSA Level 3 provenance attestations — all without writing a single pipeline. You'll then verify your supply chain integrity using **Enterprise Contract** policy checks and promote your application through a controlled release pipeline to a production namespace, with images pushed to a self-hosted **Quay** registry.

By the end of this lab, you'll understand how Konflux connects build, sign, scan, and release into a single automated workflow — and how your organization can adopt it to meet increasingly strict software supply chain security requirements.

**Products:** Konflux, Red Hat Trusted Artifact Signer, Red Hat Quay, OpenShift Pipelines, GitLab


**Owner:** treddy08

---

## What was set up

1. Repository created
2. `catalog-info.yaml` added to repository
3. Registered in Developer Hub catalog
4. Orchestrator workflow started — your AI-guided content pipeline is running!

## What happens next

Claude will walk you through the entire content lifecycle — from intake and spec creation, through Jira tracking and reviews, all the way to a published lab on RHDP. Just follow the prompts!

## Getting started

### DevSpaces (recommended)

1. Open in DevSpaces: `https://devspaces.apps.ocpv-infra02.wdc07.infra.demo.redhat.com#https://github.com/rhpds/konflux-tssc-lab`
2. Use Claude via the **extension** or the **CLI**:
   - **Extension:** Click the **Claude** icon in the sidebar, click **New Session**. If the Claude icon is not visible, open **Extensions** (`Ctrl/Cmd+Shift+X`), find **Claude Code for VS Code** under the DevSpaces section, click it, then click **Enable (Workspace)**.
   - **CLI:** Open a terminal and run `claude`
3. Run `/rhdp-publishing-house` — and you're off!

### Local machine

1. Install the skills:
   ```
   git clone -b prod https://github.com/rhpds/rhdp-publishing-house-skills.git ~/.claude/skills/publishing-house
   ```
2. Clone the repo:
   ```
   git clone https://github.com/rhpds/konflux-tssc-lab
   ```
3. `cd konflux-tssc-lab`
4. Start Claude CLI: `claude`
5. Run `/rhdp-publishing-house` — and you're off!
