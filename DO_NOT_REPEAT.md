# Avoid repeated dead ends

- `py -3` was inspected on 2026-09-20: Windows launcher reports no installed Python.
  Use the available Codex bundled Python; the launcher alone is not proof of a runtime.
- Workspace initially contained only an empty `.git`; no prior build or game data.
- No Git remote or Git author identity configured at startup. GitHub connector later
  verified owner Ahmed-alghamdi9900 (ID 82968596); local Git now uses the account
  login and GitHub's ID+login noreply address. Remote still pending creation.
- Do not infer engine, exact edition, patch, DLC completeness, or executable
  accessibility from the game's marketing name or an external folder filename.
- Synthetic parser passes do not establish game compatibility or boot milestones.
- GitHub connector can list/manipulate existing repositories but has no repository
  creation endpoint. It currently lists zero accessible repositories. Browser
  creation requires owner sign-in (handoff page opened); do not ask for credentials.
