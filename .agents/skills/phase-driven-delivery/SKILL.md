---
name: phase-driven-delivery
description: 'Use when asked to implement thesis-writer-v1 by following 实施方案.md and 分阶段实施计划.md, updating task_plan.md/progress.md/findings.md after each phase, performing code review at phase boundaries, and consulting LandPPT, ppt-master, or approved external references when needed.'
user-invocable: true
---

# Phase Driven Delivery

Use this skill when the task is not a single isolated code change, but ongoing project delivery against the implementation references in [实施方案.md](d:/code/thesis-writer-v1/实施方案.md) and [分阶段实施计划.md](d:/code/thesis-writer-v1/分阶段实施计划.md).

This skill packages a strict workflow for:

- Implementing the project phase by phase.
- Keeping planning and progress markdown files synchronized.
- Running code review at the end of each completed phase.
- Reusing patterns from sibling projects and approved external references when they materially help delivery.

## Scope

This is a workspace-scoped delivery workflow for `thesis-writer-v1`.

It applies when the user asks for any of the following:

- Continue project development according to the staged implementation plan.
- Complete the next phase or task in the plan.
- Keep markdown progress files in sync with development.
- Perform code review as part of staged delivery.
- Reference `d:/code/LandPPT`, `d:/code/ppt-master`, or approved web material while implementing.

## Required Inputs

Before changing code, read these files if they exist:

1. `实施方案.md`
2. `分阶段实施计划.md`
3. `task_plan.md`
4. `progress.md`
5. `findings.md`

If the task touches PPT generation workflows inside `ppt-master`, also read `d:/code/ppt-master/skills/ppt-master/SKILL.md` before acting on those tasks.

## Environment Rule

The current project uses a `uv`-managed Python environment.

When running Python commands, installing dependencies, executing tests, or starting local services for `thesis-writer-v1`:

- Prefer `uv run ...` for project commands.
- Prefer `uv add ...` or the repository's existing dependency workflow for Python package changes.
- Do not assume the system Python is the correct runtime.
- If a command fails because it bypassed `uv`, rerun it through the `uv` environment before diagnosing deeper issues.

## Workflow

Follow these steps in order.

### 1. Re-anchor on the active phase

Determine:

- Which architecture, layering, and project structure constraints in `实施方案.md` still govern the active work.
- Which phase in `分阶段实施计划.md` is currently active.
- Which checklist items are already complete, in progress, or blocked.
- Whether `task_plan.md` reflects the same status.

If the plan markdowns are stale, update them before or alongside implementation so the written state matches the actual delivery state.

### 2. Define the smallest meaningful delivery slice

Choose a slice that:

- Advances exactly one phase or one coherent subtask.
- Has a visible output.
- Can be verified.
- Does not mix unrelated fixes.

Examples:

- Finish one API contract and its persistence path.
- Add one parser path and its tests.
- Complete one rendering or export capability.

Do not bundle multiple planned stages into one implementation burst unless the plan explicitly couples them.

### 3. Gather implementation context

Inspect the local codebase first.

If needed, consult:

- `d:/code/LandPPT` for product workflow, platform, API, web, template, auth, and service patterns.
- `d:/code/ppt-master` for SVG-first rendering, template assets, export flow, and PPT compatibility constraints.
- `https://linux.do/t/topic/1796104` for methodology ideas, prompt structure, or workflow inspiration.

Rules for reuse:

- Reuse ideas, architecture, patterns, and non-trivial implementation strategies.
- Do not blindly copy large blocks of code.
- Adapt external patterns to this repository's structure and conventions.
- Record any important borrowed pattern or design decision in `findings.md`.

### 4. Implement the slice

During implementation:

- Fix root causes, not only symptoms.
- Keep changes minimal and phase-focused.
- Preserve existing public contracts unless the phase requires a contract change.
- Add or update tests when the changed surface is testable.
- Avoid unrelated refactors.

### 5. Verify before claiming progress

Run the narrowest useful verification for the slice, for example:

- Targeted tests.
- API smoke tests.
- Static checks or linting.
- A short end-to-end path for the affected feature.

If environment limits prevent full verification, note exactly what was and was not validated.

### 6. Perform phase-boundary code review

When a phase or a marked sub-phase is completed, perform a review pass with a bug-and-risk mindset.

Review for:

- Behavioral regressions.
- Missing tests.
- Mismatch between code and planned acceptance criteria.
- Hidden coupling or state flow issues.
- Data contract drift.
- Incomplete documentation updates.

Primary review output should be findings first, ordered by severity. If no findings exist, say so explicitly and note residual risks.

### 7. Sync markdown files immediately

After each meaningful slice, update the markdown artifacts.

Required sync behavior:

- `分阶段实施计划.md`: mark checklist progress for the specific task or phase.
- `task_plan.md`: update current phase status and next step.
- `progress.md`: append what was implemented, verified, and any environment blockers.
- `findings.md`: append important technical discoveries, reusable patterns, and review findings.

Do not defer markdown sync until much later. The docs are part of the deliverable.

### 8. Report completion in delivery terms

When reporting back, state:

- What phase/subtask was advanced.
- What code changed.
- What was verified.
- What markdown files were synchronized.
- Whether a code review found issues.
- What the next logical delivery slice is.

## Decision Rules

### When to consult sibling projects

Consult `LandPPT` when the task is about:

- API layout
- Web product flows
- project/task management
- template metadata management
- service orchestration

Consult `ppt-master` when the task is about:

- SVG generation
- template assets
- SVG validation/finalization
- PPT export compatibility
- slide rendering rules

Consult the approved web reference when the task is about:

- methodology sequence
- prompt/workflow framing
- research to brief to outline to slide-plan process

### When to stop and ask the user

Stop and ask if:

- The current codebase state conflicts with the plan in a way that requires reprioritization.
- A referenced external implementation suggests a materially different architecture choice.
- The next phase depends on unavailable credentials, services, or product decisions.
- Three distinct attempts fail on the same blocker.

## Completion Checks

A slice is only complete if all applicable checks pass:

1. The planned checklist item is implemented in code.
2. Verification was run or the verification gap is explicitly recorded.
3. The relevant markdown files were updated.
4. A code review pass was completed for finished phase boundaries.
5. Any reused external pattern was captured in `findings.md`.

## Output Standard

Responses after using this skill should be delivery-oriented, not speculative.

Preferred structure:

1. Phase/subtask advanced.
2. Code and file changes.
3. Verification result.
4. Review findings or explicit no-findings statement.
5. Markdown sync result.
6. Next recommended slice.
