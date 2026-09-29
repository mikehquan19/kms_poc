# KMS
The POC for the custom key management system of Nebula Labs.

# Overview



# Loadtest

We performed the load-test experiment to determine custom KMS would become the bottleneck on the perfomance of the API server.

# Resource endpoints

The API exposes API-key-protected list endpoints for the following resources:

- `GET /api/animals`
- `GET /api/plants`
- `GET /api/vehicles`
- `GET /api/books`

The controller-facing services intentionally iterate over repository results to simulate per-record processing. Mongo-shaped fixtures containing 40 records for each resource are available at:

- `data/animals.json`
- `data/plants.json`
- `data/vehicles.json`
- `data/books.json`

