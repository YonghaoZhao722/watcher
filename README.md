# watcher

Polls a public Binance Smart Money trader's open positions about every 10 minutes and sends a phone push when the position set changes (opened, increased, decreased, or closed).

Each Actions run polls six times in one job (about 10 minutes apart), stores state on disk between polls, writes it to the Actions cache at the end, and then dispatches the next run so monitoring continues without depending on GitHub cron. A scheduled trigger is kept as a backup; if a loop is already in progress or queued, the scheduled run exits early.

Previous state is stored in the Actions cache, not in this repository. API credentials and the push topic are repository secrets.

Required secrets:

- `KOPYON_KEY`
- `NTFY_TOPIC`

A monthly `keepalive` workflow commits a timestamp so GitHub does not disable the backup schedule after 60 days of repository inactivity.

Manual run: Actions → watch → Run workflow. Enable "Send a one-time ntfy test push" only when you want a test notification. Cancelling a run stops that job from dispatching the next one, which breaks the chain until you start it again or a backup schedule fires.
