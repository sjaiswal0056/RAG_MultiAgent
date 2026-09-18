# Deployment

## Backend on Render

1. Push the repository to GitHub.
2. In Render, create a Blueprint from the repository. `render.yaml` uses the Dockerfile and `/health` readiness check.
3. Set secrets only in the provider dashboard. The deterministic default needs no LLM key.
4. Verify `https://<backend-host>/health` and submit one `/analyze` request.

## Frontend on Streamlit Community Cloud

1. Create an app from `frontend/streamlit_app.py`.
2. Set `API_BASE_URL` in Streamlit secrets/environment to the verified backend origin.
3. Confirm public-case selection, JSON upload/paste, citations, trace, and abstention displays.

## Container check

```bash
docker build -t policy-claim-engine .
docker run --rm -p 8000:8000 policy-claim-engine
```

No public deployment was performed from this environment because provider credentials were not available. Deployment configuration is complete; provider authentication/manual deployment remains.
