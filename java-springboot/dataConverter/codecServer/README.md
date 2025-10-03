# Temporal Remote Codec Server

This is a remote codec server implementation for Temporal that provides HTTP endpoints for encoding and decoding payloads using the `CryptCodec` for encryption/decryption operations.

## Overview

The codec server implements Temporal's remote data encoder protocol, providing two main endpoints:
- `/encode` - Encrypts payloads using AES/GCM encryption
- `/decode` - Decrypts payloads that were previously encrypted
- `/health` - Health check endpoint

## Features

- **AES/GCM Encryption**: Uses secure AES encryption with Galois/Counter Mode
- **Spring Boot**: Built with Spring Boot for easy deployment and configuration
- **JSON API**: RESTful JSON API for encoding/decoding operations
- **CORS Support**: Cross-Origin Resource Sharing enabled for web applications
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Health Monitoring**: Health check endpoint for monitoring

## API Endpoints

### POST /encode
Encrypts a list of Temporal payloads.

**Request Body:**
```json
{
  "payloads": [
    {
      "metadata": {
        "encoding": "json/plain"
      },
      "data": "base64-encoded-data"
    }
  ]
}
```

**Response:**
```json
{
  "payloads": [
    {
      "metadata": {
        "encoding": "binary/encrypted",
        "encryption-cipher": "AES/GCM/NoPadding",
        "encryption-key-id": "test-key-test-key-test-key-test!"
      },
      "data": "base64-encoded-encrypted-data"
    }
  ]
}
```

### POST /decode
Decrypts a list of encrypted Temporal payloads.

**Request Body:**
```json
{
  "payloads": [
    {
      "metadata": {
        "encoding": "binary/encrypted",
        "encryption-cipher": "AES/GCM/NoPadding",
        "encryption-key-id": "test-key-test-key-test-key-test!"
      },
      "data": "base64-encoded-encrypted-data"
    }
  ]
}
```

**Response:**
```json
{
  "payloads": [
    {
      "metadata": {
        "encoding": "json/plain"
      },
      "data": "base64-encoded-decrypted-data"
    }
  ]
}
```

### GET /health
Returns the health status of the codec server.

**Response:**
```json
{
  "status": "OK",
  "message": "Codec server is running"
}
```

## Building and Running

### Prerequisites
- Java 11 or higher
- Gradle

### Build
```bash
./gradlew :dataConverter:codecServer:build
```

### Run
```bash
./gradlew :dataConverter:codecServer:bootRun
```

The server will start on port 8090 by default.

### Run as JAR
```bash
./gradlew :dataConverter:codecServer:bootJar
java -jar dataConverter/codecServer/build/libs/codecServer.jar
```

## Configuration

The server can be configured via `application.yaml`:

```yaml
server:
  port: 8090  # Change the port

logging:
  level:
    io.temporal.app.codecServer: DEBUG  # Adjust logging level
```

### CORS Configuration

The server is configured with CORS support to allow cross-origin requests:

- **Allowed Origins**: `*` (all origins)
- **Allowed Methods**: `POST`, `OPTIONS`
- **Allowed Headers**: `*` (all headers)

This enables web applications to make requests to the codec server from different domains. The CORS configuration is implemented both at the Spring Boot configuration level and with `@CrossOrigin` annotations on the controller.

## Security Considerations

⚠️ **Important**: This implementation uses a hardcoded encryption key for demonstration purposes. In production:

1. **Use a proper Key Management System (KMS)** like AWS KMS, HashiCorp Vault, or Azure Key Vault
2. **Implement key rotation** mechanisms
3. **Use environment variables** or secure configuration for keys
4. **Enable HTTPS/TLS** for the codec server endpoints
5. **Implement authentication and authorization** for the endpoints

## Integration with Temporal

To use this codec server with your Temporal workflows:

1. Start the codec server
2. Configure your Temporal client to use the remote codec server
3. Configure the Temporal Web UI to use the codec server for payload decoding

### Client Configuration Example

```java
// Configure the remote codec
RemoteDataEncoderCodec remoteCodec = new RemoteDataEncoderCodec(
    "http://localhost:8090"
);

// Create Temporal client with the codec
WorkflowServiceStubs service = WorkflowServiceStubs.newLocalServiceStubs();
WorkflowClient client = WorkflowClient.newInstance(service,
    WorkflowClientOptions.newBuilder()
        .setDataConverter(DefaultDataConverter.newDefaultInstance()
            .withPayloadCodecs(remoteCodec))
        .build());
```

### Web UI Configuration

Configure the Temporal Web UI to use the codec server:

```bash
temporal server start-dev --ui-codec-endpoint http://localhost:8090
```

## Testing

Run the tests:
```bash
./gradlew :dataConverter:codecServer:test
```

## Monitoring

The server includes Spring Boot Actuator endpoints for monitoring:
- `/actuator/health` - Health check
- `/actuator/info` - Application information
- `/actuator/metrics` - Application metrics

## Troubleshooting

1. **Port already in use**: Change the port in `application.yaml`
2. **Encryption/Decryption errors**: Check that the key ID matches between encode and decode operations
3. **JSON parsing errors**: Ensure the request format matches the expected Payload structure
