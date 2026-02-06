# Docker Orchestration for TEE Multi-Service Deployment

## ADDED Requirements

### Requirement: Multi-Service Docker Compose
The oracle deployment SHALL use Docker Compose to orchestrate multiple services within the TEE enclave.

#### Scenario: Service definitions
- **WHEN** docker-compose.yml is read
- **THEN** it SHALL define three services: evm-score-oracle, ollama_server, ollama_model
- **AND** all services SHALL use network_mode: host
- **AND** all services SHALL set init: true
- **AND** all services SHALL set restart: unless-stopped

#### Scenario: Ollama server service
- **WHEN** ollama_server service is defined
- **THEN** it SHALL use image ollama/ollama:0.5.4
- **AND** it SHALL use network_mode: host for TEE compatibility
- **AND** it SHALL define health check with command "ollama --version"
- **AND** health check SHALL run every 10 seconds
- **AND** health check SHALL allow 30 second start_period

#### Scenario: Model loader service
- **WHEN** ollama_model service is defined
- **THEN** it SHALL use image ollama/ollama:0.5.4
- **AND** it SHALL depend on ollama_server with condition: service_healthy
- **AND** it SHALL run command "pull llama3.2:1b"
- **AND** it SHALL define health check with command "ollama list | grep llama3.2:1b"
- **AND** health check SHALL allow 3 minute start_period for model download

#### Scenario: Oracle service dependencies
- **WHEN** evm-score-oracle service is defined
- **THEN** it SHALL depend on ollama_model with condition: service_healthy
- **AND** it SHALL set environment variable OLLAMA_HOST=http://127.0.0.1:11434
- **AND** it SHALL mount /app/ecdsa.sec:/app/ecdsa.sec:ro volume
- **AND** it SHALL use existing image reference pattern majus/evm-score-oracle@sha256:...

### Requirement: Service Startup Orchestration
The Docker Compose configuration SHALL ensure services start in correct order with health validation.

#### Scenario: Startup sequence
- **WHEN** Docker Compose starts services
- **THEN** ollama_server SHALL start first
- **AND** ollama_model SHALL wait for ollama_server to be healthy
- **AND** evm-score-oracle SHALL wait for ollama_model to be healthy
- **AND** each service SHALL wait for its dependencies before starting

#### Scenario: Health check validation
- **WHEN** a service health check fails
- **THEN** dependent services SHALL NOT start
- **AND** Docker Compose SHALL retry health checks according to interval and retries settings
- **AND** failure SHALL be visible in deployment logs

### Requirement: Deployment Integration
The deployment script SHALL wait for Ollama readiness before proceeding with enclave registration.

#### Scenario: Extended health check in deploy.sh
- **WHEN** enclave is deployed to Oyster CVM
- **THEN** deploy.sh SHALL wait for basic service health (/health endpoint)
- **AND** it SHALL additionally check for Ollama connectivity in health response
- **AND** it SHALL poll health endpoint up to 30 times at 10 second intervals
- **AND** it SHALL look for "ollama":"connected" in JSON response
- **AND** it SHALL proceed to PCR registration only after Ollama is ready

#### Scenario: Ollama timeout handling
- **WHEN** Ollama does not become ready within retry limit
- **THEN** deploy.sh SHALL log warning message
- **AND** it SHALL suggest manual health check command
- **AND** it SHALL NOT fail deployment (allow continuation)
- **AND** warning SHALL indicate service may still be loading model

## MODIFIED Requirements

None - docker-compose.yml is being created/extended, not modifying existing requirements.

## REMOVED Requirements

None
