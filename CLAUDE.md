# Publishing House Project

## On every session start

Read `publishing-house/spec.yaml`. Check the workflow stage by running `/rhdp-publishing-house`.

Do NOT read manifest.yaml — it does not exist. All project data is in `publishing-house/spec.yaml`.

## State
Project state tracked in [publishing-house/spec.yaml](publishing-house/spec.yaml).
Read it first every session.

## Scaffolding
Run `python scaffold.py` after cloning to select a lab pattern (AgD v2 Open,
AgD v2 Guided, or ZT Guided). The script copies common project files
(`content/` with a minimal `antora.yml`/`nav.adoc`/`index.adoc`, `qa-automation/`,
and a default `site.yml` using the `rhdp_showroom_theme` bundle — all shared by
every pattern) plus pattern-specific stubs into the project root (including
`ui-config.yml` and, for guided patterns, a `site.yml` that overwrites the
default with the nookbag UI bundle), sets `showroom_type` and `infrastructure`
in the spec, and removes `.scaffolds/`. `podman-compose.yaml` is AgD v2 Open
only — guided patterns rely on Nookbag to drive navigation, so plain
Antora + httpd can't preview them locally. The orchestrator calls
`scaffold.py --pattern <name> --force` during intake.

Pass `--automation {ansible,gitops,both}` in the same invocation to also scaffold
`automation/` from `.scaffolds/automation/` — this must happen before `.scaffolds/`
is removed, so it can't be done as a separate later step once the project has already
been scaffolded once. Add `--topology shared-cluster` (only known once intake completes)
to additionally include `automation/gitops/bootstrap-tenant/`; without it, gitops automation
only creates `automation/gitops/bootstrap-infra/`. The orchestrator calls
`scaffold.py --pattern <name> --automation <automation_type> --force` during intake,
reading `automation_type` from `publishing-house/spec.yaml`.

## Content
Showroom AsciiDoc content lives in [content/](content/). The Antora component descriptor
is at `content/antora.yml` and modules are in `content/modules/ROOT/pages/`.

## Automation
Pattern-specific automation directories are created by `scaffold.py`:

- `runtime-automation/` — Per-module solve/validate playbooks (Guided patterns)
- `setup-automation/` — Environment setup playbook (ZT Guided only)
- `config/` — Project Zero instance/network/firewall definitions (ZT Guided only)

Common to all patterns:

- `qa-automation/` — Health check and e2e test playbooks

If `--automation` was passed to `scaffold.py`, it also creates `automation/`
(source: `automation_type` in the spec):

- `automation/ansible/` — Starter Ansible collection (`ansible`/`both`) — a placeholder;
  build custom automation here (RHDPCD-110)
- `automation/gitops/bootstrap-infra/` — Helm chart with a test namespace (`gitops`/`both`)
- `automation/gitops/bootstrap-tenant/` — Per-user namespace + RBAC (`gitops`/`both`, only if
  `--topology shared-cluster` was passed)

## Architecture

- **project_id**: comes from `catalog-info.yaml` `metadata.name`
- **Central API URL**: comes from `publishing-house/spec.yaml` `system.central`
- **Auth**: Bearer token from `~/.config/publishing-house/auth.json`
- **Stage**: queried from Central API via `/api/v1/projects/{project_id}/orchestrator-state`

## Stage: intake

Use the `/rhdp-publishing-house` skill. It will conduct the spec interview, write the design, and submit to the Central API.

Do NOT change stage manually. Stage transitions are managed by SonataFlow via the Central API.

## Stage: development

Help the author write content. Answer questions about AsciiDoc, module structure, learning objectives, procedures. You are an assistant — do not advance stages or modify spec without explicit instruction.

Run compliance check when asked:
```bash
python publishing-house/tools/ph-check.py
```

## Stage: review or ready

Show the author the current spec or compliance results and wait for instruction.

## Tools

All project tools live in `publishing-house/tools/`:
- `ph-intake.py` — submit intake to Central API (called by orchestrator skill)
- `ph-check.py` — run local compliance checks against spec and content

## File locations
- Project spec: `publishing-house/spec.yaml`
- Design doc: `publishing-house/spec/design.md`
- Module outlines: `publishing-house/spec/modules/`
- Content: `content/modules/ROOT/pages/`
- Navigation: `content/modules/ROOT/nav.adoc`

## Module Writing Workflow

### Branch rules

- Always create a feature branch before any changes: `git checkout -b feat-module-NN-<slug>`
- Never commit directly to main. All changes go through a PR reviewed before merge.
- After merging: `git checkout main && git pull`

### Before writing

Read these files to build full context:
- `publishing-house/spec.yaml` — module list, environment, audience, automation_type
- `publishing-house/spec/design.md` — narrative overview, prerequisites, business scenario
- `publishing-house/spec/modules/module-NN-<slug>.md` — step-by-step outline for the target module
- All existing `content/modules/ROOT/pages/module-*.adoc` — read every completed module to cross-check consistency before writing

### Writing

Spawn `rhdp-publishing-house:module-writing-helper` with:
- `TARGET_FILE`: `content/modules/ROOT/pages/<outline-name>.adoc` (replace `.md` with `.adoc`)
- `FILE_TYPE`: `module`
- `FULL_SPEC`: combined JSON from spec.yaml + design.md + module outline
- `LAB_TYPE`: `ocp`
- `CONTENT_TYPE`: `workshop`
- `SHOWROOM_TYPE`: `classic`
- `REPO_PATH`: `/projects/konflux-tssc-lab`

### Coherence review (mandatory after writing)

Cross-check the generated module against every completed module for:

1. **Antora attributes** — only use attributes defined in `content/antora.yml`:
   `{openshift_username}`, `{openshift_apps_domain}`, `{openshift_console_url}`,
   `{tas_oidc_issuer}`, `{guid}`, `{ssh_user}`, `{ssh_password}`.
   Deploy-time attributes (`{quay_url}`, `{prod_image}`) are NOT in antora.yml — substituted
   at runtime by Showroom. Use them in content with `subs="attributes+"` only.

2. **Application name** — must be `my-sample-app` (established in Module 2)

3. **Namespace convention** — tenant: `{openshift_username}-tenant`, managed: `{openshift_username}-managed`

4. **Cross-module references** — verify any reference to another module's output names the module
   where that artifact was actually produced. Read completed modules to confirm.

5. **End-to-end chain tables** — verify each row maps to what that module actually had the
   participant do, not what the module title implies.

6. **Forward references** — do not reference steps from modules not yet completed. Restructure
   to be self-contained.

7. **cosign / SLSA commands** — include both SLSA v0.2 and v1 predicate paths in jq commands.
   Check predicateType first, then extract using the matching path:
   - Check: `cosign download attestation ${IMAGE} | jq -r '.[0].payload | @base64d | fromjson | .predicateType'`
   - v1 path: `.predicate.buildDefinition.resolvedDependencies[0]` / `.predicate.runDetails.builder.id`
   - v0.2 path: `.predicate.materials[0]` / `.predicate.builder.id`

### Missing screenshots

When a module references `image::filename.png[...]` and the file does not exist:

1. Create a GitHub issue documenting each missing file and where to capture it.
2. Use the shared placeholder: `image::screenshot-placeholder.svg[alt text,800]`
   (lives at `content/modules/ROOT/assets/images/screenshot-placeholder.svg`)
3. Add a TODO comment above each image macro linking to the issue:
   `// TODO: replace placeholder with real screenshot — see https://github.com/rhpds/konflux-tssc-lab/issues/N`

### Mark complete

```bash
# Update spec.yaml: set module status: complete
git add publishing-house/spec.yaml
git commit -m "feat: mark module N complete — <Title>
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push
python publishing-house/tools/ph-task-complete.py module-NN
```

### Local preview (DevSpaces)

`podman-compose` requires `/dev/net/tun` which is absent in DevSpaces — use `npx antora` directly:

```bash
# Install extensions once per session
npm install --prefix /tmp/antora-local @sntke/antora-mermaid-extension @andrew-jones/antora-tabs-extension

# Build
cd /projects/konflux-tssc-lab
NODE_PATH=/tmp/antora-local/node_modules npx antora --fetch site.yml

# Serve (if not already running)
cd www && python3 -m http.server 8080 &
```

`gh` CLI is at `~/.local/bin/gh`. `podman-compose` can be installed via `pip3 install --user podman-compose` but container networking (pasta) is broken in this DevSpaces pod.
