# Architecture

This diagram summarizes the workflow described in the repository README. Verify each component against the current implementation before extending the system.

```mermaid
flowchart LR
    A[Customer data] --> B[Schema validation]
    B --> C[Training and evaluation]
    C --> D[Quality and regression gates]
    D --> E[Versioned model artifact]
    E --> F[FastAPI prediction service]
    G[GitHub Actions] --> B
    G --> C
    G --> D
    H[MLflow tracking and registry] <--> C
    I[Docker image] --> F
```

## Main boundaries

- **Data and validation:** schema checks reject malformed deliveries before model training.
- **Training and evaluation:** the model workflow produces metrics and traceability metadata.
- **Release gate:** absolute quality and baseline-regression checks decide whether an artifact can be published.
- **Serving:** FastAPI exposes health and prediction endpoints.
- **Packaging and automation:** Docker and GitHub Actions support repeatable build and delivery.

## Operational questions to document as the implementation evolves

- Which exact workflow publishes the serving image?
- How are model and API compatibility checked together?
- Where are secrets configured, and how are they kept out of Git?
- What rollback procedure is used for a bad model or image?
