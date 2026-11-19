# trader-watch

Polls a public Binance Smart Money trader's open positions on a 10-minute GitHub Actions schedule and sends a phone push when the position set changes (opened, increased, decreased, or closed).

Previous state is stored in the Actions cache, not in this repository. API credentials and the push topic are repository secrets.

Required secrets:

- `KOPYON_KEY`
- `NTFY_TOPIC`

A monthly `keepalive` workflow commits a timestamp so GitHub does not disable the schedule after 60 days of repository inactivity.

Manual run: Actions → watch → Run workflow. Enable "Send a one-time ntfy test push" only when you want a test notification.
