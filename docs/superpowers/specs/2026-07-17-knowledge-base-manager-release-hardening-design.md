# Knowledge Base Manager Release Hardening Design

Date: 2026-07-17
Status: approved by the user's instruction to choose the best option automatically

## Outcome

Ship `knowledge-base-manager` as a public, installable `1.0.0` skill-only Codex plugin whose
privacy boundaries fail closed, whose local CLI is responsive and diagnosable, and whose release
can be reproduced on Windows and Ubuntu from one verification entrypoint.

Completion requires all of the following:

- a tampered or stale asset index cannot weaken `sensitivity`, `reuse_mode`, `status`, or role;
- the unified CLI imports only the selected command and reports missing dependencies clearly;
- path-boundary tests execute on Windows without silently skipping junction coverage;
- local release validation still passes after the normal test workflow;
- one end-to-end smoke proves `init --apply -> doctor -> index -> query -> source snapshot/verify`;
- README installation, dependency, Windows, smoke, and update instructions match current Codex;
- the complete intended repository is committed, pushed to a public GitHub repository, green in
  Windows/Ubuntu CI, tagged `v1.0.0`, and published as a GitHub Release.

## Chosen Approach

Keep the existing skill-only plugin architecture and harden it in place. The plugin already has a
coherent schema-v3 contract, 91 passing unit tests, synthetic forward-evaluation fixtures, valid
plugin metadata, and an installed local marketplace entry. Expanding to an MCP server or separate
application would add authentication, deployment, and privacy surfaces without improving the core
knowledge-management workflow.

Two alternatives were rejected:

1. Publish the current tree with only cache cleanup. This is fastest but would ship a demonstrated
   privacy/reuse bypass in `query` and an incomplete first-use verification path.
2. Rebuild the project as a service or UI. This would delay the release and move away from the
   requested reusable Codex skill without solving the verified CLI and release issues first.

## Security And Data Flow

The generated asset index remains a routing cache, never an authority. Query execution will use
this sequence:

```text
root manifest and current Markdown assets
-> deterministic canonical index rebuild in memory
-> owned stored index validation
-> exact canonical comparison
-> filters and ranking
-> shortlist output
```

Any missing ownership marker, stale row, changed metadata, hash mismatch, duplicate ID, or path
escape stops the query with exit code 2 and instructions to rebuild the index. The query command
must not return partial results from an untrusted index.

## CLI And Error Handling

`kb.py` will map command names to module entrypoints and import only the selected module. Top-level
help and unknown-command handling remain dependency-free. If a selected command lacks a runtime
dependency, the CLI will name the missing package and print the exact requirements installation
command instead of exposing an import traceback.

The release validator will judge files that can enter the release, not ignored local caches created
by a normal test run. It will continue to reject tracked Python cache artifacts and verify that the
ignore rules cover generated output.

## Verification Design

Unit coverage will add adversarial cases for index metadata tampering, unowned indexes, lazy command
loading, dependency errors, and Windows junction path boundaries. A repository-level smoke runner
will create a temporary synthetic root, exercise every CLI phase, verify a real retrieval result,
confirm source immutability, and remove its workspace.

CI will run Ruff, release validation, unit tests with a coverage floor, compile checks, and the
end-to-end smoke on Windows and Ubuntu. Python 3.11 remains the minimum; an additional current
Python job will prevent an untested open-ended compatibility claim.

## Publication Transaction

The initial public release will use the existing `a550752845-hue/knowledge-base-manager` identity,
MIT license, and public documentation. The repository will be created empty, the complete reviewed
tree committed on `main`, pushed, and checked through GitHub Actions. Only after CI passes will the
annotated `v1.0.0` tag and GitHub Release be created. The final audit will verify repository files,
badge and policy URLs, release assets, a fresh clone installation path, and the installed plugin
version.
