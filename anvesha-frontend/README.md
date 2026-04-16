# Anvesha Frontend

Small standalone JavaScript frontend for the `anvesha-server` tracing API.

## Features

- Connect to any Anvesha backend URL
- Browse projects and trace counts
- View traces for a selected project
- Inspect spans, attributes, and events for a trace
- Filter projects, traces, and spans in the browser

## Run

From this directory:

```bash
cd /data/keshav/Anvesha/anvesha-frontend
npm start
```

The frontend will be served at:

```text
http://127.0.0.1:4173
```

## Backend URL

The UI expects the backend API base, not the site root. Example:

```text
http://127.0.0.1:8000/v1
```

If you are testing against the local Anvesha server on another port, enter that value in the UI header and click `Connect`.

## Notes

- `anvesha-server` already enables CORS for local browser access.
- The selected backend URL is saved in browser local storage.
