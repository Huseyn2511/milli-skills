# Milli Taksi — skills & config backup

Mirror of the `milli-taksi` Hermes skill used by the autonomous assistant.
Secrets (N8N_API_KEY, UpTaxi password, Telegram token) live ONLY in the local
`~/.hermes/.env` on the owner's PC — never in this repo.

## Sync
- Pull: `git pull` then copy `milli-taksi/` into Hermes skills dir.
- Push: `git add -A && git commit && git push` (after sanitizing secrets).
