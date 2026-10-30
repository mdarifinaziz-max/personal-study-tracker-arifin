# Personal study tracker

A private, single-user edition of the supplied academic tracker with SQLite persistence. Requires Python 3.10+; no packages to install.

Run `python3 server.py` from this directory and open http://127.0.0.1:8000 in your browser. Keep the server running while using the app. Data is stored in `data/tracker.sqlite3`; set TRACKER_DATA_DIR to a persistent directory to change that location. Use the same port for browser cache continuity.

Every changed save creates a durable revision. Save status appears at bottom right. Interrupted saves retry while the page is open, with pending changes cached for reload. Concurrent edits are rejected rather than silently overwriting another tab: export the conflicted tab before resolving changes. Close extra tabs when importing or restoring data.

Use the existing Export/Import buttons for portable JSON backups. To migrate from the original standalone HTML, export there and import here; browsers isolate storage between file URLs and this server. Revision history is available at `/api/history`; `/api/revision/NUMBER` returns a previous JSON snapshot that can be saved and imported. Revisions currently remain indefinitely; monitor disk space.

For a consistent database backup, run `python3 server.py --backup /path/to/backup.sqlite3`. Schedule this command using your operating system's scheduler and copy backups to another device or backup service. To restore a database, stop the server and replace the data directory with a directory containing the backup named tracker.sqlite3 (retain the old directory for recovery). Restart and verify your data. SQLite survives normal restarts, but no local disk is permanent or immune to loss.

The server intentionally binds only to localhost and checks request origins. It has no multi-user authentication and is not configured for public deployment. Hosting across devices requires authentication, HTTPS, a persistent volume, and off-device backups.

Validation: `python3 -m unittest -v` tests actual HTTP saves, stale-write rejection, invalid payload rejection, revision recovery, process restart persistence, and backup creation. Browser interaction has not yet been automated.

## Open without a server

Open index.html with memory.js in the same folder, or serve both on a static host. When the backend is absent, the tracker uses browser storage and clearly labels that mode. This does not provide cross-device sync. Export before clearing browser data. If you later use a server, use “Download browser-only work” to recover unsynced work and import it deliberately; it never silently overwrites the server copy.

## Hosted version with password sign-in

The included render.yaml provisions a Python service and persistent disk on Render. This uses a paid plan; check Render's current pricing before creating it. In Render, create a Blueprint from this GitHub repository, enter a strong TRACKER_PASSWORD, and deploy. Open the HTTPS address supplied by Render. Sign in with username `arifin` and your chosen password in the browser's sign-in prompt. Never enter your ChatGPT password here. This is HTTP Basic authentication over Render's HTTPS, not a ChatGPT or Google account. The server refuses hosted startup without a password.

The persistent disk keeps the database across restarts and deployments. Keep exported backups outside the service as well; deleting the service/disk can remove the database. The deployment configuration is prepared but has not been deployed or tested against Render in this task.
