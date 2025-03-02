# Helm Values Manager Example

This example demonstrates how to use the helm-values-manager plugin to manage different configurations for staging and production environments using the Bitnami Nginx chart.

## Reference Values

Here are the reference values that we'll be managing across environments:

### Base Values (common.yaml)

```yaml
nginx:
  image:
    registry: docker.io
    repository: bitnami/nginx
    tag: latest
    pullPolicy: IfNotPresent
```

### Staging Values (staging.yaml)

```yaml
nginx:
  replicaCount: 1

  service:
    type: ClusterIP
    port: 80

  ingress:
    enabled: true
    hostname: staging.example.com

  metrics:
    enabled: false
```

### Production Values (production.yaml)

```yaml
nginx:
  replicaCount: 3

  service:
    type: LoadBalancer
    port: 80

  ingress:
    enabled: true
    hostname: example.com
    tls: true

  metrics:
    enabled: true
```

## Setup and Usage

1. Add the Bitnami repository:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

2. Initialize helm-values-manager for the nginx release:

```bash
helm values-manager init --release nginx-app
```

3. Add value configurations with descriptions and validation:

```bash
# Core configurations
helm values-manager add-value-config --path nginx.replicaCount --description "Number of nginx replicas" --required
helm values-manager add-value-config --path nginx.service.type --description "Kubernetes service type (ClusterIP/LoadBalancer)" --required
helm values-manager add-value-config --path nginx.service.port --description "Service port number" --required

# Ingress configuration
helm values-manager add-value-config --path nginx.ingress.enabled --description "Enable ingress" --required
helm values-manager add-value-config --path nginx.ingress.hostname --description "Ingress hostname"
helm values-manager add-value-config --path nginx.ingress.tls --description "Enable TLS for ingress"

# Metrics configuration
helm values-manager add-value-config --path nginx.metrics.enabled --description "Enable prometheus metrics"
```

4. Add deployments for different environments:

```bash
helm values-manager add-deployment staging
helm values-manager add-deployment production
```

5. Set values for staging environment:

```bash
# Basic configuration
helm values-manager set-value --path nginx.replicaCount --value 1 --deployment staging
helm values-manager set-value --path nginx.service.type --value ClusterIP --deployment staging
helm values-manager set-value --path nginx.service.port --value 80 --deployment staging

# Ingress configuration
helm values-manager set-value --path nginx.ingress.enabled --value true --deployment staging
helm values-manager set-value --path nginx.ingress.hostname --value staging.example.com --deployment staging

# Metrics configuration
helm values-manager set-value --path nginx.metrics.enabled --value false --deployment staging
```

6. Generate staging values:

```bash
# Generate staging values - this should succeed as all required values are set
helm values-manager generate --deployment staging
```

7. Set up production environment (demonstrating validation):

```bash
# Set some of the production values, intentionally omitting service configuration
helm values-manager set-value --path nginx.replicaCount --value 3 --deployment production
helm values-manager set-value --path nginx.ingress.enabled --value true --deployment production
helm values-manager set-value --path nginx.ingress.hostname --value example.com --deployment production
helm values-manager set-value --path nginx.ingress.tls --value true --deployment production
helm values-manager set-value --path nginx.metrics.enabled --value true --deployment production

# Try to generate values - this should fail with validation errors
helm values-manager generate --deployment production
```

The above command will fail with validation errors because we haven't set two required values:

1. `nginx.service.type`
2. `nginx.service.port`

This demonstrates how helm-values-manager helps catch missing configurations early in the deployment process.

8. Fix validation errors and complete production setup:

```bash
# Set the missing required values
helm values-manager set-value --path nginx.service.type --value LoadBalancer --deployment production
helm values-manager set-value --path nginx.service.port --value 80 --deployment production

# Now the generate command should succeed
helm values-manager generate --deployment production
```

9. Verify configurations using helm template:

```bash
# Template the chart for staging environment
helm template nginx-staging bitnami/nginx -f common.yaml -f staging.nginx-app.values.yaml

# Template the chart for production environment
helm template nginx-prod bitnami/nginx -f common.yaml -f prod.nginx-app.values.yaml

# You can also save the templated output to files for inspection
helm template nginx-staging bitnami/nginx -f common.yaml -f staging.nginx-app.values.yaml > staging-manifests.yaml
helm template nginx-prod bitnami/nginx -f common.yaml -f prod.nginx-app.values.yaml > prod-manifests.yaml
```

The helm template command will show you the actual Kubernetes manifests that would be created, allowing you to:

- Verify that all values are correctly applied
- Inspect the differences between environments
- Catch any issues before actual deployment

## Key Benefits Demonstrated

1. **Configuration Validation**: Early detection of missing or invalid configurations through required value definitions
2. **Value Documentation**: Each configuration value is documented with clear descriptions
3. **Environment Separation**: Clean separation between staging and production configurations
4. **Structured Management**: Organized way to add and modify values
5. **Value Tracking**: Easy to track what values are available and required

## Cleanup

To clean up the example:

1. Remove generated value files:

```bash
rm -f *.nginx-app.values.yaml
```

2. Remove generated manifest files:

```bash
rm -f *-manifests.yaml
```

3. Remove helm-values-manager files:

```bash
rm -f helm-values.json .helm-values.lock
```
