# FastAPI + Cloud Run + Firestore greenfield pattern

Use this reference when building a small FastAPI service that stores and reads simple documents in Google Cloud Firestore and is deployed to Cloud Run.

## Recommended shape

- Keep the service stateless.
- Separate settings, API routing, and Firestore repository code.
- Reuse the Firestore client/repository with a cached dependency instead of constructing a client per request.
- If the endpoint is `async` but the Firestore client is synchronous, run repository calls through FastAPI's threadpool helper (`run_in_threadpool`) so the request path remains responsive.

## Configuration

Prefer environment-driven configuration:

- `GOOGLE_CLOUD_PROJECT`
- `FIRESTORE_DATABASE`
- `FIRESTORE_COLLECTION`
- `GOOGLE_APPLICATION_CREDENTIALS` for local execution when a service account key file is being used

For Terraform-driven deployments, it is reasonable to source core deploy inputs from environment variables via:

- `TF_VAR_project_id`
- `TF_VAR_region`

Document these explicitly in the README and examples so local runtime and deploy docs stay aligned.

## Cloud Run baseline for moderate throughput

For a simple Firestore-backed service targeting around 50 RPS:

- keep handlers lightweight
- reuse the Firestore client
- set a moderate Cloud Run concurrency value (for example `40`) as a simple baseline
- allow horizontal scaling with min/max instance controls
- validate actual throughput with load testing in the target project rather than assuming local correctness proves capacity

This is a baseline, not a guaranteed SLA.

## Firestore notes

- A named database is valid when the deployment intentionally avoids `(default)`.
- Local tests should mock or override the repository boundary so they run without GCP credentials.
- Local real-GCP execution should document the chosen auth path clearly; if using a key file, point `GOOGLE_APPLICATION_CREDENTIALS` at the absolute path.

## Docs checklist

When generating a showcase project like this, ensure the README includes:

- local `uv` setup
- local run command
- test command that works without cloud credentials
- Docker/Cloud Run container run example
- Terraform apply flow
- exact env vars required locally and for deploy
- explicit note that the image may already exist in Artifact Registry rather than being built by Terraform
