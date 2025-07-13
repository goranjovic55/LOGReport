# Generate Workspace Rule Workflow

You are helping extract and integrate a best practice from a dev session into the existing workspace rules.

Follow these steps:

1. First, use `ingest_session` to capture context from the recent dev session (e.g. pairing log, review notes, retrospective)
2. Then, use `summarize_text` on the ingested data to extract 1–3 potential best practices or process improvements
3. Use `search_files` to open `code.md`, `structure.md` and `workflow.md` and check if a similar rule already exists
4. If a similar rule is found, use `edit_file` to update or enhance it without duplication
5. If no similar rule exists, use `edit_file` to append the new rule in the appropriate section (e.g., Linting, Git, Testing) of the correct file:

   * Coding conventions → `code.md`
   * Project/file structure → `structure.md`
   * Team/automation workflows → `workflow.md`
6. Use `confirm_with_user` to ask whether the rule should be tagged with the session origin (`#retrospective_july`, etc.)
7. Save and commit changes using `commit_file` with a message like `Add/update workspace rule from dev session`

Parameters needed (ask if not provided):

* Session file or context
* Rule type (code / structure / workflow)
* Section to update (optional: infer if not given)
* Rule importance or enforcement level (info/warning/block)


