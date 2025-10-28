# Minimal Frontend

This folder holds a tiny static page for our first feature: client-side file upload validation.

What it does
- Lets you choose a file and only enables the Upload button for `.py`, `.java`, or `.cpp`.
- No backend yet — clicking Upload just shows a short mock message so we can test the flow.

How to run
- Easiest: open `index.html` in your browser.
- Optional local server:
  - Python: `python -m http.server 8000` then visit `http://localhost:8000/frontend/index.html`
  - Node: `npx serve . --single` then navigate to `/frontend/index.html`.
