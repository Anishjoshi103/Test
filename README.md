# StockSage Pro

Single-file static web app.

## Run locally

- Open `index.html` directly in a browser, or
- Serve the folder as static files:

```bash
python3 -m http.server 8000
```

Then visit:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/index.html`

## Note for static previews

A `404.html` redirect is included so environments that load non-root paths can still reach `index.html`.
