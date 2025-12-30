# Enterprise Deployment

Enterprise-grade deployment with Kubernetes.

## Overview

Enterprise deployment features:
- Kubernetes orchestration
- High availability
- Multi-region support
- Custom PKI integration
- Enterprise monitoring

## Kubernetes Deployment

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pdf2md
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pdf2md-config
  namespace: pdf2md
data:
  RATE_LIMIT_BACKEND: "redis"
  RATE_LIMIT_FAIL_MODE: "closed"
  LOG_LEVEL: "INFO"
```

### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf2md-app
  namespace: pdf2md
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdf2md
  template:
    metadata:
      labels:
        app: pdf2md
    spec:
      containers:
      - name: app
        image: your-registry/pdf2md:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: pdf2md-config
        - secretRef:
            name: pdf2md-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Redis

```yaml
# redis.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: pdf2md
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          limits:
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: pdf2md
spec:
  clusterIP: None
  selector:
    app: redis
  ports:
  - port: 6379
```

### Service & Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: pdf2md-service
  namespace: pdf2md
spec:
  selector:
    app: pdf2md
  ports:
  - port: 80
    targetPort: 8000
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pdf2md-ingress
  namespace: pdf2md
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - pdf2md.example.com
    secretName: pdf2md-tls
  rules:
  - host: pdf2md.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pdf2md-service
            port:
              number: 80
```

## High Availability

- **Multiple replicas**: 3+ app instances
- **Pod anti-affinity**: Distribute across nodes
- **Health checks**: Liveness and readiness probes
- **Auto-scaling**: Horizontal Pod Autoscaler

## Monitoring

Use Prometheus and Grafana:

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: pdf2md
  namespace: pdf2md
spec:
  selector:
    matchLabels:
      app: pdf2md
  endpoints:
  - port: metrics
    interval: 30s
```

See [Docker Deployment](docker.md) for configuration reference.