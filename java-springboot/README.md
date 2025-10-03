# Java Spring Boot samples

This project contains the following Spring Boot samples:

- **dataConverter**: custom encryption on Temporal payloads

## Prerequisites

- Java 17+
- Temporal CLI

## Running the Samples

### Data Converter

1. **Start Temporal Server**

   ```bash
   temporal server start-dev --ui-codec-endpoint http://localhost:8090
   ```

1. **Run the Workers** (from `${PROJECT_ROOT}/java-springboot`)

   ```bash
   ./gradlew :dataConverter:workers:bootRun
   ```

1. **Run the API Server** (from `${PROJECT_ROOT}/java-springboot`)

   ```bash
   ./gradlew :dataConverter:api:bootRun
   ```

The API server will be available at `http://localhost:3030`

1. **Run the Codec Server** (from `${PROJECT_ROOT}/java-springboot`)

   ```bash
   ./gradlew :dataConverter:codecServer:bootRun
   ```

The codec server will be available at `http://localhost:8090`

1. **Trigger a Temporal Workflow**

   ```bash
   curl -X POST http://localhost:3030/api/v1/users/workflow-id \
     -H "Content-Type: application/json" \
     -d '{
       "id": "custom-id",
       "value": "custom-value"
     }'
   ```

1. **View Temporal UI**

Check Temporal UI for the triggered Workflow.
