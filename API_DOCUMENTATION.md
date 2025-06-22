# CROSS XML Downloader PRO - API Documentation

## Overview

The CROSS XML API provides programmatic access to all platform features including XML downloads, DANFE generation, transport labels, and user management.

**Base URL**: `https://crossxml.com.br/api/v1`
**Authentication**: API Key + Secret
**Format**: JSON

## Authentication

### Generate API Credentials

```http
POST /api/generate-credentials
Authorization: Bearer {session_token}
```

**Response:**
```json
{
  "api_key": "ck_test_1234567890abcdef",
  "api_secret": "cs_test_abcdef1234567890",
  "created_at": "2025-06-22T00:00:00Z"
}
```

### Using API Credentials

Include in all requests:
```http
X-API-Key: ck_test_1234567890abcdef
X-API-Secret: cs_test_abcdef1234567890
```

## Endpoints

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-06-22T00:00:00Z",
  "version": "1.0.0"
}
```

### XML Download Jobs

#### Create Download Job

```http
POST /api/v1/jobs
Content-Type: application/json
```

**Request Body:**
```json
{
  "invoice_keys": [
    "42250485179240000239550020004175341622314954",
    "35250513516247000107550010000113401146202508"
  ],
  "callback_url": "https://webhook.example.com/xml-complete",
  "metadata": {
    "customer_id": "12345",
    "batch_name": "Weekly Download"
  }
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created",
  "total_keys": 2,
  "created_at": "2025-06-22T00:00:00Z",
  "estimated_cost": 0.20
}
```

#### Get Job Status

```http
GET /api/v1/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": {
    "total_keys": 2,
    "processed": 2,
    "successful": 2,
    "failed": 0,
    "percentage": 100.0
  },
  "files": [
    {
      "filename": "42250485179240000239550020004175341622314954.xml",
      "size": 4750,
      "download_url": "/api/v1/jobs/550e8400/files/42250485179240000239550020004175341622314954.xml"
    }
  ],
  "created_at": "2025-06-22T00:00:00Z",
  "completed_at": "2025-06-22T00:05:00Z",
  "total_cost": 0.20
}
```

#### List Jobs

```http
GET /api/v1/jobs?status=completed&limit=10&offset=0
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "total_keys": 2,
      "successful": 2,
      "created_at": "2025-06-22T00:00:00Z"
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

#### Download File

```http
GET /api/v1/jobs/{job_id}/files/{filename}
```

**Response:** XML file content with appropriate headers

### DANFE Generation

#### Generate DANFE

```http
POST /api/v1/danfe
Content-Type: application/json
```

**Request Body:**
```json
{
  "xml_id": "123",
  "format": "pdf"
}
```

**Response:**
```json
{
  "danfe_url": "/api/v1/danfe/download/550e8400-e29b-41d4-a716-446655440000.pdf",
  "generated_at": "2025-06-22T00:00:00Z",
  "expires_at": "2025-06-22T24:00:00Z"
}
```

### Transport Labels

#### Generate Labels

```http
POST /api/v1/labels
Content-Type: application/json
```

**Request Body:**
```json
{
  "xml_id": "123",
  "layout": "transul",
  "paper_size": "10x15cm",
  "volumes": [
    {"number": 1, "weight": 8.1},
    {"number": 2, "weight": 8.1}
  ],
  "company_config": {
    "name": "TRANSPORTADORA XYZ",
    "subtitle": "OPERADOR LOGÍSTICO",
    "area_code": "15"
  }
}
```

**Response:**
```json
{
  "label_url": "/api/v1/labels/download/550e8400-e29b-41d4-a716-446655440000.pdf",
  "volumes_generated": 2,
  "total_size_bytes": 295742,
  "generated_at": "2025-06-22T00:00:00Z"
}
```

### User Management

#### Get User Info

```http
GET /api/v1/user
```

**Response:**
```json
{
  "user_id": 7,
  "email": "joao@crossxml.com.br",
  "credits_balance": 150,
  "trial_expires_at": null,
  "subscriptions": [
    {
      "feature": "labels_module",
      "status": "active",
      "expires_at": "2025-07-22T00:00:00Z"
    }
  ],
  "usage_stats": {
    "xmls_downloaded": 1250,
    "danfes_generated": 850,
    "labels_generated": 420
  }
}
```

#### Get Credit History

```http
GET /api/v1/user/credits?limit=20&offset=0
```

**Response:**
```json
{
  "transactions": [
    {
      "id": 456,
      "type": "purchase",
      "amount": 100,
      "description": "Pacote Professional - 500 créditos",
      "created_at": "2025-06-22T00:00:00Z"
    },
    {
      "id": 457,
      "type": "usage",
      "amount": -1,
      "description": "Download XML: NF 417536",
      "created_at": "2025-06-22T00:05:00Z"
    }
  ],
  "current_balance": 149,
  "total": 50
}
```

## Webhooks

### XML Download Complete

When a download job completes, we'll POST to your callback_url:

```json
{
  "event": "job.completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total_keys": 2,
  "successful": 2,
  "failed": 0,
  "files": [
    {
      "filename": "42250485179240000239550020004175341622314954.xml",
      "download_url": "/api/v1/jobs/550e8400/files/42250485179240000239550020004175341622314954.xml"
    }
  ],
  "metadata": {
    "customer_id": "12345"
  },
  "completed_at": "2025-06-22T00:05:00Z"
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "insufficient_credits",
    "message": "Insufficient credits for this operation",
    "details": {
      "required": 2,
      "available": 1
    }
  },
  "timestamp": "2025-06-22T00:00:00Z"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `invalid_api_key` | API key is invalid or missing |
| `insufficient_credits` | Not enough credits for operation |
| `invalid_invoice_key` | Invoice key format is invalid |
| `rate_limit_exceeded` | Too many requests |
| `job_not_found` | Job ID doesn't exist |
| `file_not_found` | Requested file doesn't exist |
| `subscription_required` | Feature requires active subscription |

## Rate Limits

- **API Calls**: 1000 per hour per API key
- **File Downloads**: 10,000 per day per API key
- **Job Creation**: 100 per hour per API key

## SDKs and Examples

### Python

```python
import requests

class CrossXMLAPI:
    def __init__(self, api_key, api_secret, base_url="https://crossxml.com.br"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        
    def create_job(self, invoice_keys, callback_url=None):
        headers = {
            'X-API-Key': self.api_key,
            'X-API-Secret': self.api_secret,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'invoice_keys': invoice_keys,
            'callback_url': callback_url
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/jobs",
            json=payload,
            headers=headers
        )
        
        return response.json()

# Usage
api = CrossXMLAPI('your_api_key', 'your_api_secret')
job = api.create_job(['42250485179240000239550020004175341622314954'])
print(f"Job created: {job['job_id']}")
```

### JavaScript

```javascript
class CrossXMLAPI {
    constructor(apiKey, apiSecret, baseUrl = 'https://crossxml.com.br') {
        this.apiKey = apiKey;
        this.apiSecret = apiSecret;
        this.baseUrl = baseUrl;
    }
    
    async createJob(invoiceKeys, callbackUrl = null) {
        const response = await fetch(`${this.baseUrl}/api/v1/jobs`, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey,
                'X-API-Secret': this.apiSecret,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                invoice_keys: invoiceKeys,
                callback_url: callbackUrl
            })
        });
        
        return await response.json();
    }
}

// Usage
const api = new CrossXMLAPI('your_api_key', 'your_api_secret');
const job = await api.createJob(['42250485179240000239550020004175341622314954']);
console.log(`Job created: ${job.job_id}`);
```

### cURL

```bash
# Create download job
curl -X POST https://crossxml.com.br/api/v1/jobs \
  -H "X-API-Key: your_api_key" \
  -H "X-API-Secret: your_api_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_keys": ["42250485179240000239550020004175341622314954"],
    "callback_url": "https://webhook.example.com"
  }'

# Check job status
curl https://crossxml.com.br/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: your_api_key" \
  -H "X-API-Secret: your_api_secret"

# Download file
curl https://crossxml.com.br/api/v1/jobs/550e8400/files/invoice.xml \
  -H "X-API-Key: your_api_key" \
  -H "X-API-Secret: your_api_secret" \
  -o invoice.xml
```

## Pricing

- **XML Download**: R$ 0.06 - 0.10 per file (volume-based)
- **DANFE**: Free
- **Labels Module**: R$ 49.90/month subscription
- **API Access**: Included in all plans

## Support

- **Documentation**: [docs.crossxml.com.br](https://docs.crossxml.com.br)
- **Support Email**: api@crossxml.com.br
- **Status Page**: [status.crossxml.com.br](https://status.crossxml.com.br)