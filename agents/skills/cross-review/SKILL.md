---
name: cross-review
description: Cross-model PR review. Claude spawns a GPT-6-Astra reviewer; an OpenAI model spawns a Claude Opus 5.5 reviewer. Each iteration starts a fresh reviewer, the two sessions debate its new findings to agreement, and the implementer fixes the simple issues. The loop stops when a fresh review finds no new major issue (max 3 iterations), then reports the rest to the user in STE. Use when the user asks for a cross-review or invokes /cross-review.
---

# Cross-review

Two senior engineers from different model vendors review one PR and agree on the issues. Each iteration uses a new reviewer session, so earlier findings do not anchor the review.

```
implementer (you)                          reviewer (other vendor, new session per iteration)
-----------------                          ---------------------------------------------------
iteration k (k = 1..3):
  00-request.md (no ledger) -- peer.sh ->  fresh review: findings F1..Fn
  01-dedup.md (ledger)      -- peer.sh ->  map each F to NEW | I<n> | REOPEN I<n>
  round 1..3: assess        -- peer.sh ->  assess NEW and REOPEN issues   (stop rule below)
  fix agreed simple issues, commit
  stop if no NEW or REOPEN issue is major or blocker
report to user
```

## Roles

| You are      | Reviewer                         | `peer.sh` argument |
|--------------|----------------------------------|--------------------|
| Claude       | GPT-6-Astra (Codex CLI)          | `codex`            |
| OpenAI model | Claude Opus 5.5 (Claude Code CLI) | `claude`           |

- **Implementer**: the session that loaded this skill. You implemented this PR.
- **Reviewer**: a senior engineer. The reviewer receives this same file.
- **Ledger**: `$dir/ledger.md`. The implementer keeps all issues from all iterations in it, with stable `I<n>` IDs.

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

### Reviewer: fresh review

Read the diff and the code around it. Produce the findings. Use `F<n>` IDs in place of `I<n>`. Report only issues that you can show with the code.

### Reviewer: dedup

Compare each finding with the ledger. Give one line for each finding:

```
F<n> -> NEW
F<n> -> I<m>                 (same issue; ledger status stays)
F<n> -> REOPEN I<m>: <why>   (the issue is still present after its fix, or the ledger decision was wrong)
```

### Debate rounds

One round is one implementer turn plus one reviewer turn. Debate only the NEW and REOPEN issues of this iteration. In each turn, address every issue that is not `agreed` or `withdrawn`. For each issue, agree, dispute with evidence, change the severity, or propose a simpler solution. You can add new issues.

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

   The reviewer diff is `git diff $mb` (includes uncommitted changes and earlier fix commits).

2. Make a state directory and an empty ledger: `dir=$(mktemp -d -t cross-review); : >"$dir/ledger.md"`.

3. Do iterations `k = 1, 2, 3`. Each iteration uses `$dir/i$k/`. A new directory makes `peer.sh` start a new reviewer session.

   1. Write `$dir/i$k/00-request.md` with:
      - This line: "You are the Reviewer in the protocol below. Do not spawn sessions. Do not edit files. Produce the fresh review."
      - The full text of this file.
      - The repository path, the diff command, and the PR title, body, and linked issue.

      Do not include the ledger or earlier findings.

   2. Send each turn with the helper. The first call in a directory starts the reviewer session. Later calls resume it.

      ```bash
      ~/.claude/skills/cross-review/peer.sh <codex|claude> "$dir/i$k" "$dir/i$k/00-request.md"
      ```

      - Run it from the repository root.
      - One turn can take many minutes. Claude: use `run_in_background` and wait for the notification. Codex: set a timeout of 30 minutes or more.
      - The peer CLI needs network access. Run it outside the sandbox or request escalated permission.
      - The reply is in `$dir/i$k/<name>.reply.md`.

   3. If the ledger is not empty, write `$dir/i$k/01-dedup.md` with the dedup instruction and the full ledger. Send it. If the ledger is empty, all findings are NEW.

   4. Add the NEW issues to the ledger with the next free `I<n>` IDs. Set REOPEN issues back to `proposed`.

   5. For round N, write `$dir/i$k/rN-implementer.md` with your assessment of every open NEW and REOPEN issue. Send it with `peer.sh`. Apply the debate stop rule after each reviewer reply. Update the ledger.

   6. Fix every `agreed` issue that has a `simple` solution. Run the project tests and linters. If there are changes, make one commit on top of the branch: "Address cross-review findings (iteration k)". Do not rewrite history. Do not push.

   7. Stop the iterations if no NEW or REOPEN issue in this iteration is `major` or `blocker`. Otherwise, start the next iteration.

4. Write the report to `$dir/report.md` and put the full report in your final message. Use STE. Sections:
   - **Summary**: the number of iterations. Say "converged" if the last fresh review found no NEW or REOPEN `major` or `blocker` issue. Otherwise, say "not converged" and list the fixes that no fresh review has examined.
   - **Fixed**: one line per issue (ID, title, severity). Give the commit SHA.
   - **Needs your decision**: `agreed` issues with a `complex` solution.
   - **Unresolved**: `disputed` issues. Give both positions and your recommendation.
   - **Dedup**: for each iteration, the reviewer's mapping lines.

   For each issue in "Needs your decision" and "Unresolved", include:
   - Context: where the issue is and what the code does there.
   - Terms: define jargon and abbreviations.
   - Failure example: a concrete input or sequence and the wrong result.
   - Diagram: an ASCII diagram when the issue involves flow, state, or structure.
   - Proposed solution: what to change, why, and the cost or risk.

## Failure handling

If `peer.sh` fails, stop. Show the error and the command to the user. Do not use a different model or skip the review.
