---
name: cross-review
description: Cross-model PR review. Claude spawns a GPT-6-Astra reviewer; an OpenAI model spawns a Claude Opus 5.5 reviewer. The two sessions debate the findings to agreement, the implementer fixes the simple issues, then reports the rest to the user in STE. Use when the user asks for a cross-review or invokes /cross-review.
---

# Cross-review

Two senior engineers from different model vendors review one PR and agree on the issues.

```
implementer (you)                         reviewer (other vendor)
-----------------                         -----------------------
write 00-request.md  ---- peer.sh ---->   turn 0: issue list
                     <---- reply -----
round 1: assess      ---- peer.sh ---->   assess
round 2: assess      ---- peer.sh ---->   assess        (stop rule below)
round 3: assess      ---- peer.sh ---->   assess
fix simple issues, commit
report to user
```

## Roles

| You are      | Reviewer                         | `peer.sh` argument |
|--------------|----------------------------------|--------------------|
| Claude       | GPT-6-Astra (Codex CLI)          | `codex`            |
| OpenAI model | Claude Opus 5.5 (Claude Code CLI) | `claude`           |

- **Implementer**: the session that loaded this skill. You implemented this PR.
- **Reviewer**: a senior engineer. The reviewer receives this same file.

## Shared rules (both roles)

- Write in Simplified Technical English (STE, ASD-STE100). Use short sentences, active voice, and one idea per sentence.
- KISS. Propose the smallest fix that solves the problem.
- Make no code changes during the debate. The reviewer never edits files.
- Verify claims against the code. Hold a position when you have evidence. Concede when the other side has better evidence. Do not agree only to finish.
- Severity:
  - `blocker`: wrong behavior, data loss, security hole, or broken build or tests. Fix before merge.
  - `major`: real defect or design problem with limited impact. Fix before merge if possible.
  - `minor`: small defect, unclear code, or a missing edge-case test.
- Solution size:
  - `simple`: local change, no design choice, no new concept, low risk.
  - `complex`: all other solutions.
- Use this format for each issue in every turn. Keep IDs stable. A new issue gets the next free ID.

  ```
  ### I<n>: <title>
  - Where: <path:line>
  - Severity: blocker | major | minor
  - Problem: <what fails, with an example input or sequence>
  - KISS solution: <smallest fix> (simple | complex)
  - Status: proposed | agreed | disputed | withdrawn
  - Note: <your response to the other side's last position>
  ```

### Reviewer turn 0

Read the diff and the code around it. Produce the issue list. Report only issues that you can show with the code.

### Debate rounds

One round is one implementer turn plus one reviewer turn. In each turn, address every issue that is not `agreed` or `withdrawn`. For each issue, agree, dispute with evidence, change the severity, or propose a simpler solution. You can add new issues.

Stop the debate when one of these conditions is true:

- 3 rounds are complete.
- One full round finds no new `blocker` issue.
- All issues are `agreed` or `withdrawn`.

## Implementer procedure

1. Get the review range and PR context:

   ```bash
   base=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null || echo main)
   mb=$(git merge-base "origin/$base" HEAD)
   gh pr view --json title,body,url 2>/dev/null   # PR context, if a PR exists
   ```

   The reviewer diff is `git diff $mb` (includes uncommitted changes).

2. Make a state directory: `dir=$(mktemp -d -t cross-review)`.

3. Write `$dir/00-request.md` with:
   - This line: "You are the Reviewer in the protocol below. Do not spawn sessions. Do not edit files. Produce turn 0."
   - The full text of this file.
   - The repository path, the diff command, and the PR title, body, and linked issue.

4. Send each turn with the helper. The first call starts the reviewer session. Later calls resume it.

   ```bash
   ~/.claude/skills/cross-review/peer.sh <codex|claude> "$dir" "$dir/00-request.md"
   ```

   - Run it from the repository root.
   - One turn can take many minutes. Claude: use `run_in_background` and wait for the notification. Codex: set a timeout of 30 minutes or more.
   - The peer CLI needs network access. Run it outside the sandbox or request escalated permission.
   - The reply is in `$dir/<name>.reply.md`.

5. For round N, write `$dir/rN-implementer.md` with your assessment of every open issue. Send it with `peer.sh`. Apply the stop rule after each reviewer reply.

6. Fix every `agreed` issue that has a `simple` solution. Run the project tests and linters. Make one commit on top of the branch: "Address cross-review findings". Do not rewrite history. Do not push.

7. Write the report to `$dir/report.md` and put the full report in your final message. Use STE. Sections:
   - **Fixed**: one line per issue (ID, title, severity). Give the commit SHA.
   - **Needs your decision**: `agreed` issues with a `complex` solution.
   - **Unresolved**: `disputed` issues. Give both positions and your recommendation.

   For each issue in the last two sections, include:
   - Context: where the issue is and what the code does there.
   - Terms: define jargon and abbreviations.
   - Failure example: a concrete input or sequence and the wrong result.
   - Diagram: an ASCII diagram when the issue involves flow, state, or structure.
   - Proposed solution: what to change, why, and the cost or risk.

## Failure handling

If `peer.sh` fails, stop. Show the error and the command to the user. Do not use a different model or skip the review.
