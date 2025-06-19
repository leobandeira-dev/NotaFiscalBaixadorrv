# XML Downloader API

## Visão Geral

A API REST do XML Downloader permite integração automatizada para download em lote de arquivos XML de notas fiscais. A API oferece endpoints para criar jobs de download, monitorar progresso e baixar arquivos XML individualmente.

**Base URL:** `https://sua-aplicacao.replit.app/api/v1`

## Autenticação

Atualmente a API não requer autenticação. Para uso em produção, recomenda-se implementar autenticação por API key.

## Endpoints

### 1. Health Check

Verifica se a API está funcionando.

**Endpoint:** `GET /api/v1/health`

**Resposta:**
```json
{
    "status": "healthy",
    "version": "1.0",
    "service": "MeuDANFe XML Downloader API",
    "timestamp": "2025-06-19T04:00:00.000000"
}
```

### 2. Criar Job de Download

Cria um novo job para download de XMLs de notas fiscais.

**Endpoint:** `POST /api/v1/jobs`

**Body:**
```json
{
    "invoice_keys": [
        "35250162954987000130550020001854371034511150",
        "35250162954987000130550020001854371034511151"
    ],
    "callback_url": "https://seu-webhook.com/callback" // opcional
}
```

**Resposta de Sucesso (201):**
```json
{
    "job_id": "cc9fc653-7b99-45fe-bafb-9cb0c7f2784f",
    "status": "created",
    "total_keys": 2,
    "created_at": "2025-06-19T04:00:00.000000"
}
```

**Resposta de Erro (400):**
```json
{
    "error": "Invalid invoice key format. Must be 44 digits.",
    "code": "INVALID_KEY_FORMAT",
    "invalid_keys": ["123456"]
}
```

### 3. Obter Status do Job

Consulta o status e progresso de um job específico.

**Endpoint:** `GET /api/v1/jobs/{job_id}`

**Resposta:**
```json
{
    "job_id": "cc9fc653-7b99-45fe-bafb-9cb0c7f2784f",
    "status": "completed",
    "progress": {
        "total_keys": 2,
        "processed": 2,
        "successful": 2,
        "failed": 0,
        "percentage": 100.0
    },
    "files": [
        "35250162954987000130550020001854371034511150.xml",
        "35250162954987000130550020001854371034511151.xml"
    ],
    "errors": [],
    "created_at": "2025-06-19T04:00:00.000000",
    "completed_at": "2025-06-19T04:05:00.000000"
}
```

### 4. Listar Jobs

Lista todos os jobs com filtros opcionais.

**Endpoint:** `GET /api/v1/jobs`

**Parâmetros de Query:**
- `status` (opcional): Filtrar por status (`running`, `completed`, `failed`)
- `limit` (opcional): Máximo de jobs por página (padrão: 50)
- `offset` (opcional): Número de jobs a pular (padrão: 0)

**Exemplo:** `GET /api/v1/jobs?status=completed&limit=10&offset=0`

**Resposta:**
```json
{
    "jobs": [
        {
            "job_id": "cc9fc653-7b99-45fe-bafb-9cb0c7f2784f",
            "status": "completed",
            "total_keys": 2,
            "processed": 2,
            "successful": 2,
            "failed": 0,
            "created_at": "2025-06-19T04:00:00.000000",
            "completed_at": "2025-06-19T04:05:00.000000"
        }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
}
```

### 5. Listar Arquivos do Job

Lista todos os arquivos XML baixados por um job específico.

**Endpoint:** `GET /api/v1/jobs/{job_id}/files`

**Resposta:**
```json
{
    "job_id": "cc9fc653-7b99-45fe-bafb-9cb0c7f2784f",
    "files": [
        {
            "filename": "35250162954987000130550020001854371034511150.xml",
            "size": 4590,
            "download_url": "/api/v1/jobs/cc9fc653-7b99-45fe-bafb-9cb0c7f2784f/files/35250162954987000130550020001854371034511150.xml"
        }
    ]
}
```

### 6. Baixar Arquivo XML

Baixa um arquivo XML específico de um job.

**Endpoint:** `GET /api/v1/jobs/{job_id}/files/{filename}`

**Resposta:** Arquivo XML como attachment para download.

### 7. Testar Conexão

Testa a conectividade do sistema de automação.

**Endpoint:** `POST /api/v1/test`

**Resposta:**
```json
{
    "status": "success",
    "message": "Connection test completed",
    "details": {
        "success": true,
        "response_time": "2.5s"
    },
    "timestamp": "2025-06-19T04:00:00.000000"
}
```

## Status de Jobs

Os jobs podem ter os seguintes status:

- **`starting`**: Job criado, aguardando início do processamento
- **`running`**: Job em execução, baixando XMLs
- **`completed`**: Job finalizado com sucesso
- **`failed`**: Job falhou devido a erro crítico

## Códigos de Erro

### Códigos HTTP
- **200**: Sucesso
- **201**: Recurso criado com sucesso
- **400**: Erro na requisição (dados inválidos)
- **404**: Recurso não encontrado
- **500**: Erro interno do servidor

### Códigos de Erro da API
- **`MISSING_INVOICE_KEYS`**: Campo invoice_keys ausente
- **`INVALID_INVOICE_KEYS`**: Lista de chaves inválida
- **`INVALID_KEY_FORMAT`**: Formato de chave inválido (deve ter 44 dígitos)
- **`JOB_NOT_FOUND`**: Job não encontrado
- **`FILE_NOT_FOUND`**: Arquivo não encontrado
- **`INTERNAL_ERROR`**: Erro interno do servidor

## Exemplos de Uso

### Python

```python
import requests
import time

# Criar job
response = requests.post('https://sua-app.replit.app/api/v1/jobs', json={
    'invoice_keys': ['35250162954987000130550020001854371034511150']
})

job_data = response.json()
job_id = job_data['job_id']

# Monitorar progresso
while True:
    status_response = requests.get(f'https://sua-app.replit.app/api/v1/jobs/{job_id}')
    status = status_response.json()
    
    print(f"Status: {status['status']}, Progresso: {status['progress']['percentage']}%")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(5)

# Baixar arquivos
if status['status'] == 'completed':
    files_response = requests.get(f'https://sua-app.replit.app/api/v1/jobs/{job_id}/files')
    files = files_response.json()['files']
    
    for file_info in files:
        file_response = requests.get(f"https://sua-app.replit.app{file_info['download_url']}")
        
        with open(file_info['filename'], 'wb') as f:
            f.write(file_response.content)
        
        print(f"Arquivo baixado: {file_info['filename']}")
```

### cURL

```bash
# Criar job
curl -X POST https://sua-app.replit.app/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_keys": ["35250162954987000130550020001854371034511150"]
  }'

# Verificar status
curl https://sua-app.replit.app/api/v1/jobs/JOB_ID

# Listar arquivos
curl https://sua-app.replit.app/api/v1/jobs/JOB_ID/files

# Baixar arquivo
curl -O https://sua-app.replit.app/api/v1/jobs/JOB_ID/files/FILENAME.xml
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function downloadInvoices(invoiceKeys) {
    const baseUrl = 'https://sua-app.replit.app/api/v1';
    
    // Criar job
    const jobResponse = await axios.post(`${baseUrl}/jobs`, {
        invoice_keys: invoiceKeys
    });
    
    const jobId = jobResponse.data.job_id;
    console.log(`Job criado: ${jobId}`);
    
    // Monitorar progresso
    let status;
    do {
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        const statusResponse = await axios.get(`${baseUrl}/jobs/${jobId}`);
        status = statusResponse.data;
        
        console.log(`Progresso: ${status.progress.percentage}%`);
    } while (status.status === 'running');
    
    // Baixar arquivos
    if (status.status === 'completed') {
        const filesResponse = await axios.get(`${baseUrl}/jobs/${jobId}/files`);
        
        for (const file of filesResponse.data.files) {
            const fileResponse = await axios.get(`${baseUrl}${file.download_url}`, {
                responseType: 'stream'
            });
            
            const writer = fs.createWriteStream(file.filename);
            fileResponse.data.pipe(writer);
            
            console.log(`Arquivo baixado: ${file.filename}`);
        }
    }
}

// Uso
downloadInvoices(['35250162954987000130550020001854371034511150']);
```

## Webhooks (Futuro)

Em versões futuras, será possível configurar webhooks para receber notificações quando jobs forem concluídos:

```json
{
    "job_id": "cc9fc653-7b99-45fe-bafb-9cb0c7f2784f",
    "status": "completed",
    "total_files": 2,
    "successful": 2,
    "failed": 0,
    "completed_at": "2025-06-19T04:05:00.000000"
}
```

## Rate Limits

Para evitar sobrecarga do servidor, recomenda-se:
- Máximo de 100 chaves por job
- Máximo de 10 jobs simultâneos por IP
- Intervalo mínimo de 1 segundo entre requests

## Suporte

Para dúvidas sobre a API, consulte a documentação ou entre em contato através dos canais de suporte.