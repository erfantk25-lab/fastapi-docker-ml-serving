# Customer Churn MLOps Pipeline — FastAPI, Docker & CI/CD

An end-to-end MLOps project for customer-churn prediction. The repository documents a collaborative pipeline for data validation, model training and evaluation, model lineage, container packaging, and deployment.

**My individual contribution is documented separately:** the Kubernetes deployment and continuous-delivery mini-project described below. The core churn pipeline was developed collaboratively with the contributors listed at the end of this README.

## Project at a glance

- **Problem:** predict customer churn for the fictional Saldes Mobil AB case study.
- **API:** FastAPI prediction service with health and prediction endpoints.
- **ML workflow:** scikit-learn model training, evaluation, and threshold analysis.
- **Data quality:** Pandera schema validation and statistical drift checks.
- **Tracking and lineage:** MLflow experiment tracking and model registry, plus commit and dataset-hash metadata.
- **Delivery:** GitHub Actions, Docker, automated smoke tests, and GitHub Container Registry (GHCR).
- **Deployment:** Kubernetes manifests and a gated deployment workflow in the individual mini-project section.

> The company and customer data used in this educational project are fictional.

## Architecture

```text
Data delivery
    |
    v
Pandera schema validation + statistical drift checks
    |
    v
Tests and model training
    |
    v
Evaluation + regression gate
    |
    +---- rejected candidate --> CI fails; no approved artifact is published
    |
    v
Model artifact + metadata + checksum
    |
    v
MLflow tracking / model registry
    |
    v
Docker image build
    |
    v
Container smoke test
    |
    v
GHCR image (commit-SHA tag)
    |
    v
FastAPI service
    |
    v
POST /predict   GET /health
```

The pipeline is designed so that data validation and tests run before training, and only a model that passes the configured evaluation gates proceeds to packaging.

## Technology

| Area | Tools |
|---|---|
| Language and environment | Python, `uv` |
| API and validation | FastAPI, Pydantic |
| Machine learning | scikit-learn |
| Data quality | Pandera, statistical drift checks |
| Experiment tracking | MLflow |
| Testing | pytest, API tests, container smoke tests |
| Packaging | Docker, multi-stage builds, Docker Buildx |
| CI/CD | GitHub Actions, GHCR |
| Deployment mini-project | Kubernetes, `kind` |

## Run locally

### Prerequisites

- Python version compatible with the project's `pyproject.toml`
- `uv`
- Docker (for container build and run)

### 1. Clone this repository

```bash
git clone https://github.com/erfantk25-lab/fastapi-docker-ml-serving.git
cd fastapi-docker-ml-serving
```

### 2. Install dependencies

```bash
uv sync --all-extras
```

### 3. Run tests

```bash
uv run pytest
```

### 4. Train and evaluate the model

```bash
uv run python -m churn.model
uv run python -m churn.evaluate
```

The training workflow writes model and metric artifacts under `outputs/`. The project also includes a seed-variance analysis script:

```bash
uv run python analysis/seed_variance.py
```

### 5. Start the FastAPI service

After a model artifact has been generated:

```bash
uv run uvicorn churn.api:app --reload
```

Open the interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API/model availability |
| POST | `/predict` | Return a churn prediction and probability |

Run the API tests with:

```bash
uv run pytest tests/test_api.py
```

## Data validation and drift checks

The pipeline uses a Pandera schema to validate incoming customer data before training. The validation workflow includes known-good and known-bad deliveries to demonstrate that invalid data is rejected.

A separate statistical drift check compares an incoming delivery with the reference dataset. The documented checks include:

- Minimum row-count sanity check.
- Numeric feature mean-shift limits expressed in standard deviations.
- Detection of previously unseen categorical values.
- Churn target-rate shift checks.

Example:

```bash
uv run python validation/schema.py data/kundbas.csv
uv run python -m churn.drift data/kundbas_drift_leverans.csv data/kundbas.csv
```

## Model evaluation, versioning and lineage

The project evaluates classification performance using ROC AUC and accuracy, and also reports precision, recall and F1-score across classification thresholds.

A documented seed-variance analysis ran the same model across 30 train/test splits. Based on that analysis, the project uses a project-specific absolute ROC AUC gate of **0.74**. A separate regression gate compares a candidate with an approved baseline and allows a maximum ROC AUC decrease of **0.020**.

These are project configuration choices, not universal ML quality standards. They should be reassessed when the data, features or model change.

For traceability, the training workflow records metadata including:

- Git commit identifier.
- Dataset filename and SHA-256 hash.
- Evaluation metrics.
- MLflow run identifier when tracking is enabled.

The model artifact is accompanied by a SHA-256 checksum. Integrity is checked before evaluation, packaging, scoring, and API loading. A checksum detects accidental or unauthorized artifact changes when the checksum itself remains trusted; it is not a digital signature.

## MLflow experiment tracking

MLflow is an optional tracking integration. When `MLFLOW_TRACKING_URI` is configured, training runs log parameters, metrics, lineage tags and the trained model.

Example local setup using SQLite:

```bash
MLFLOW_TRACKING_URI=sqlite:///mlflow.db uv run python -m churn.model
MLFLOW_TRACKING_URI=sqlite:///mlflow.db uv run python -m churn.register
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

The repository documents an important limitation: a fresh SQLite tracking database in each CI run does not provide a persistent registry history across runs. A shared tracking server would be needed for that.

## Docker packaging and CI delivery

The GitHub Actions workflow packages the approved model and FastAPI service into a Docker image. The documented delivery steps include:

1. Download the approved model artifact.
2. Build the Docker image.
3. Start the container and run a smoke test against `/health` and `/predict`.
4. Publish the verified image to GHCR on pushes to the main branch, tagged with the commit SHA and `latest`.

The Docker configuration uses a multi-stage build, a non-root runtime user, a container health check, and Buildx GitHub Actions layer caching.

The project README records an observed comparison of approximately **39% smaller uncompressed image size** and **30% faster measured build duration** after the optimization. These are results reported for the collaborative project, not an individual performance claim.

## My individual work: Kubernetes deployment mini-project

In addition to the collaborative pipeline, I completed an **individual Kubernetes deployment and continuous-delivery mini-project** that extends the service towards a production-style deployment.

The documented work includes:

- Kubernetes Deployment and Service manifests in `k8s/`.
- Immutable container image reference pinned to a full commit SHA.
- CPU and memory requests and limits designed to fit the course namespace quota.
- Readiness and liveness probes using the API health endpoint.
- Restricted security context, non-root execution, and dropped Linux capabilities.
- Multi-architecture Docker images for `linux/amd64` and `linux/arm64`.
- RollingUpdate strategy with two replicas, zero unavailable replicas, and one surge pod.
- GitHub Actions deployment job restricted to pushes to `main` and protected by manual approval through a GitHub Environment.
- Rollout verification and documented rollback using `kubectl rollout undo`.

The deployment was tested in both local `kind` and the course cluster, as documented in the project work. The monitoring and drift-response section describes an operational plan; it should not be interpreted as a claim that a complete production monitoring service is already running.

## Repository structure

```text
.
├── .github/
│   ├── actions/
│   └── workflows/
├── analysis/
├── config/
├── data/
├── docs/
├── k8s/
├── src/
│   └── churn/
├── tests/
├── validation/
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

Some generated artifacts and local tracking files are created at runtime and may not be committed.

## What I learned

- Designing quality gates that stop invalid data and underperforming models before release.
- Tracking model artifacts back to the code commit and exact dataset version.
- Separating model evaluation from packaging and deployment.
- Building and smoke-testing containerized inference services.
- Using immutable image tags, health probes, resource limits and rolling updates in Kubernetes.
- Distinguishing team-level delivery outcomes from my own individual implementation work.

## Collaborators

The collaborative churn-pipeline work was completed with:

- [Erfan Tahmasbi](https://github.com/erfantk25-lab)
- [Lilit Ajoyan](https://github.com/LAjoyan)
- [Leo Lindqvist Kröhnert](https://github.com/LeoLindqvist123)
- [Josefin Lesley](https://github.com/Josefin3647)

## Related links

- [My GitHub profile](https://github.com/erfantk25-lab)
- [My portfolio](https://erfantk25-lab.github.io/)
- [Collaborative CI/CD repository](https://github.com/LeoLindqvist123/ci-cd-pipeline)

---

*Educational portfolio project. The repository documents both collaborative pipeline development and a separately identified individual Kubernetes mini-project.*
