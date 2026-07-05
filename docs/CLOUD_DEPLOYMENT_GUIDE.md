# Phase 1 Cloud Deployment Guide

Last updated: 2026-07-05

## Selected Platform

Phase 1 uses Render because it supports:

- GitHub-connected deployments
- Docker builds
- Public HTTPS URLs
- Environment variables and secrets
- HTTP health checks
- Optional persistent disks for ChromaDB, models, and generated data

Configuration is stored in `render.yaml`.

## Expected Cost

The supplied Blueprint uses Render's Free web-service plan for the Phase 1
review demo. It does not require payment.

The Free service has an ephemeral filesystem and spins down after inactivity.
This is acceptable for the review because the Docker image contains seed copies
of the company universe, feature data, trained models, and ChromaDB index.
`deploy/start.sh` restores them whenever a new instance starts.

For production, change `plan` to `starter` and attach a persistent disk at
`/var/data`.

## Files Used

```text
Dockerfile
requirements-cloud.txt
deploy/start.sh
render.yaml
.dockerignore
```

During the Docker build, the application:

1. Installs the minimal cloud dependencies.
2. Builds the 10K company universe from cached source files.
3. Generates the 10K-row Phase 1 feature table.
4. Trains and saves the risk and forecast classifiers.
5. Indexes the RAG documents into ChromaDB.
6. Stores the resulting seed assets inside the image.

At first startup, `deploy/start.sh` copies missing seed assets to `/var/data`.
On the Free plan these files are restored after each restart or cold start.

## Repository Deployment

After the GitHub repository has been pushed:

1. Open `https://dashboard.render.com/`.
2. Select **New > Blueprint**.
3. Connect the GitHub account and repository.
4. Render detects `render.yaml`.
5. Confirm that the service plan is Free and that no disk is listed.
6. Apply the Blueprint.
7. Monitor the build logs.
8. Open the generated `onrender.com` URL.

Verify:

```text
https://<service-name>.onrender.com/health
https://<service-name>.onrender.com/api/summary
https://<service-name>.onrender.com/
```

The health response should report:

```json
{
  "status": "ok",
  "service": "financial-intelligence-engine"
}
```

## OpenAI Configuration

The first deployment uses:

```text
FIE_GENAI_PROVIDER=local
```

To enable OpenAI, add these variables under the Render service's Environment
settings:

```text
FIE_GENAI_PROVIDER=openai
FIE_GENAI_MODEL=gpt-5.4-mini
OPENAI_API_KEY=<secret value>
```

Do not put the key in `render.yaml`, `.env.example`, Git, screenshots, or
deployment logs.

## Storage Behavior

The application maps its writable runtime data to:

```text
/var/data
```

The application maps:

```text
FIE_DATA_ROOT=/var/data
FIE_MODEL_DIR=/var/data/models
FIE_REPORTS_DIR=/var/data/reports
```

The Docker image contains bootstrap copies of:

- Processed company universe
- Feature table
- ChromaDB files
- Trained model artifacts
- Generated reports

On Render Free, runtime changes are ephemeral and are reset after a restart,
redeploy, or idle spin-down. The packaged bootstrap assets are restored on
startup, so the Phase 1 read-only demonstration remains functional. Upgrade to
a paid service with a persistent disk before relying on uploaded documents,
new vector indexes, or generated reports across restarts.

## Troubleshooting

If the health endpoint reports `degraded`, inspect the service logs and confirm
that `/var/data` contains processed, features, vectors, and models.

If the service cannot bind to a port, confirm:

```text
FIE_HOST=0.0.0.0
PORT=10000
```

If OpenAI generation fails, switch `FIE_GENAI_PROVIDER` back to `local` and
verify the API key and account configuration separately.

If a Docker build fails because of memory or dependency installation, confirm
that Render is using `requirements-cloud.txt`, not the full development
`requirements.txt`.
