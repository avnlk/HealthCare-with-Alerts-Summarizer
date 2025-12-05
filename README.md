# AIOps Healthcare Monitoring System

A complete multi-service healthcare monitoring platform with AI-powered summarization, real-time vitals monitoring, and comprehensive DevOps infrastructure.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            React Frontend (Port 3000)                       │
│                    Dashboard │ Patient Details │ Real-time Vitals           │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ REST / WebSocket
┌────────────────────────────────────┴────────────────────────────────────────┐
│                         Kubernetes Ingress Controller                        │
└───────┬─────────────────────────┬─────────────────────────┬─────────────────┘
        │                         │                         │
┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
│ Vitals Gen    │         │ Alert Engine  │         │  Summarizer   │
│ Service       │────────▶│ Service       │────────▶│  Service      │
│ (Port 8001)   │         │ (Port 8002)   │         │  (Port 8003)  │
└───────┬───────┘         └───────┬───────┘         └───────┬───────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                           Elasticsearch Cluster                              │
│  ┌───────────────────────────┐    ┌───────────────────────────────────────┐ │
│  │   Medical Indices         │    │   System Indices                      │ │
│  │   • medical-vitals-*      │    │   • system-api-*                      │ │
│  │   • medical-alerts-*      │    │   • system-k8s-*                      │ │
│  │   • medical-events-*      │    │   • system-deployment-*               │ │
│  │   • medical-summaries-*   │    │                                       │ │
│  └───────────────────────────┘    └───────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
healthcare-aiops/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── pages/              # Dashboard & Patient Details
│   │   ├── services/           # API clients
│   │   └── App.jsx
│   ├── Dockerfile
│   └── package.json
│
├── backend/                     # FastAPI microservices
│   ├── vitals-generator/       # Vitals simulation service
│   ├── alert-engine/           # Clinical alert detection
│   ├── summarizer-service/     # AI summarization (DistilBART)
│   └── shared/                 # Common utilities
│
├── infrastructure/
│   ├── docker/                 # Dockerfiles
│   ├── kubernetes/             # K8s manifests
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── ingress/
│   │   └── hpa/
│   ├── ansible/                # Provisioning roles
│   │   ├── roles/
│   │   └── playbooks/
│   └── elk/                    # ELK configuration
│
├── ci-cd/
│   └── jenkins/                # Pipeline definitions
│
├── docker-compose.yml          # Local development stack
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.10+
- Kubernetes cluster (for production)

### Local Development

```bash
# Clone and start all services
git clone <repository>
cd healthcare-aiops

# Start ELK + all microservices
docker-compose up -d

# Access services:
# - Frontend:      http://localhost:3000
# - Vitals API:    http://localhost:8001
# - Alerts API:    http://localhost:8002
# - Summarizer:    http://localhost:8003
# - Kibana:        http://localhost:5601
# - Elasticsearch: http://localhost:9200
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Backend Development

```bash
# Each service
cd backend/<service-name>
pip install -r requirements.txt
uvicorn app.main:app --reload --port <port>
```

## 🏥 Features

### Patient Monitoring Dashboard
- Real-time patient grid with vital snapshots
- Color-coded alert severity indicators
- Click-through to detailed patient views

### Real-time Vitals Streaming
- Heart Rate, SpO₂, Blood Pressure, Temperature, Respiratory Rate
- WebSocket-based live updates
- Historical trend charts (Recharts)

### Clinical Alert Engine
- **Tachycardia**: HR > 100 bpm
- **Bradycardia**: HR < 60 bpm
- **Hypoxia**: SpO₂ < 90%
- **Fever**: Temp > 38.0°C
- **Hypertensive Crisis**: Systolic BP > 180 mmHg
- **Sensor Disconnection**: Missing vitals detection

### AI-Powered Summaries
- DistilBART/T5-small transformer model
- Periodic summarization of patient conditions
- Reads ONLY from `medical-*` Elasticsearch indices
- Version-tracked model updates

### Auto-Retraining Pipeline
- Collects new medical logs automatically
- Fine-tunes transformer model
- Builds new Docker image
- Kubernetes rolling update deployment

## 📊 Dual ELK Architecture

### Medical Indices (for AI summarization)
| Index Pattern | Description |
|--------------|-------------|
| `medical-vitals-*` | Patient vital signs |
| `medical-alerts-*` | Clinical alerts |
| `medical-events-*` | Medical events |
| `medical-summaries-*` | AI-generated summaries |

### System Indices (for DevOps observability)
| Index Pattern | Description |
|--------------|-------------|
| `system-api-*` | API request logs |
| `system-k8s-*` | Kubernetes events |
| `system-deployment-*` | Deployment logs |

## ☸️ Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f infrastructure/kubernetes/

# Verify deployments
kubectl get deployments -n healthcare

# Check HPA status
kubectl get hpa -n healthcare
```

## 🔧 CI/CD Pipeline

### Jenkins Pipelines

1. **Main Pipeline** (`Jenkinsfile`)
   - Build all services
   - Run unit tests
   - Build & push Docker images
   - Deploy to Kubernetes

2. **Retrain Pipeline** (`Jenkinsfile.retrain`)
   - Collect medical logs
   - Fine-tune summarizer model
   - Build new model image
   - Rolling update deployment

### Triggering Pipelines

```bash
# Manual trigger
curl -X POST http://jenkins:8080/job/healthcare-aiops/build

# Scheduled (cron): Every 6 hours for retraining
```

## 🔐 Secrets Management

Using HashiCorp Vault:

```bash
# Store secrets
vault kv put secret/healthcare-aiops \
    elasticsearch_password=<password> \
    docker_registry_token=<token>

# Read in application
export ELASTICSEARCH_PASSWORD=$(vault kv get -field=elasticsearch_password secret/healthcare-aiops)
```

## 📝 API Reference

### Vitals Generator Service (8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/patients` | GET | List all patients |
| `/api/patients/{id}/vitals` | GET | Get patient vitals |
| `/ws/vitals/{patient_id}` | WS | Real-time vitals stream |

### Alert Engine Service (8002)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/alerts` | GET | Get all active alerts |
| `/api/alerts/{patient_id}` | GET | Get patient alerts |

### Summarizer Service (8003)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/summaries` | GET | Get all summaries |
| `/api/summaries/{patient_id}` | GET | Get patient summary |
| `/api/model/info` | GET | Model version info |
| `/api/model/trigger-summary` | POST | Trigger manual summary |

## 🔧 Ansible Provisioning

```bash
cd infrastructure/ansible

# Full infrastructure setup
ansible-playbook playbooks/site.yml -i inventory/hosts

# Individual components
ansible-playbook playbooks/elk.yml
ansible-playbook playbooks/kubernetes.yml
ansible-playbook playbooks/jenkins.yml
```

## 📈 Scaling

The summarizer service uses HPA for automatic scaling:

```yaml
minReplicas: 2
maxReplicas: 10
targetCPUUtilizationPercentage: 70
```

## 🧪 Testing

```bash
# Backend tests
cd backend/vitals-generator && pytest tests/ -v
cd backend/alert-engine && pytest tests/ -v
cd backend/summarizer-service && pytest tests/ -v

# Frontend tests
cd frontend && npm test
```

## 📄 License

MIT License - See LICENSE file for details.
