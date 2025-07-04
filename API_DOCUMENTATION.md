# CROSS XML Downloader API v1.0

## Visão Geral

A API REST do CROSS XML permite integração automatizada para download em lote de arquivos XML de notas fiscais brasileiras. A API oferece endpoints para criar jobs de download, monitorar progresso, baixar arquivos XML e acessar dados estruturados extraídos automaticamente.

## **Dupla Funcionalidade: JSON + XML**

A API retorna **ambos os formatos** para cada chave processada:

1. **Dados JSON Estruturados**: 19 campos extraídos automaticamente (número NF, valor, peso, emitente, destinatário, etc.) para integração rápida em sistemas
2. **Arquivos XML Originais**: Documentos fiscais completos (~4KB cada) para compliance, auditoria e geração de DANFE

Esta dupla funcionalidade permite usar dados estruturados para lógica de negócio e manter XMLs originais para requisitos fiscais/legais.

**Base URL:** `https://sua-aplicacao.replit.app/api/v1`

**Versão:** 1.0 (Julho 2025)

**Performance:** Download otimizado em ~7.4 segundos por chave

## Dados Extraídos Automaticamente

Para cada chave de 44 dígitos processada, a API extrai e estrutura **19 campos de dados**:

### Dados Básicos da NFe
- Chave da nota (44 dígitos)
- Número e série da nota
- Data de emissão
- Valor total (R$)

### Dados do Emitente/Remetente
- CNPJ, razão social
- Cidade, UF, endereço, CEP

### Dados do Destinatário
- CNPJ/CPF, razão social
- Cidade, UF, endereço, CEP

### Dados de Transporte
- Peso bruto (kg)
- Quantidade de volumes

## Autenticação

A API suporta autenticação via API Key para usuários registrados. Acesse `/api-docs` na interface web para gerar suas credenciais.

## Endpoints

### 1. Health Check

Verifica se a API está funcionando.

**Endpoint:** `GET /api/v1/health`

**Resposta:**
```json
{
    "status": "healthy",
    "version": "1.0",
    "title": "CROSS XML Downloader API",
    "timestamp": "2025-07-04T21:35:00.000000"
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
    "files": {
        "35250162954987000130550020001854371034511150.xml": "/api/v1/jobs/cc9fc653/files/35250162954987000130550020001854371034511150.xml",
        "35250162954987000130550020001854371034511151.xml": "/api/v1/jobs/cc9fc653/files/35250162954987000130550020001854371034511151.xml"
    },
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

**Endpoint:** `GET /api/v1/test-connection`

**Resposta:**
```json
{
    "status": "success",
    "message": "Connection test completed",
    "timestamp": "2025-07-04T21:38:00.000000"
}
```

## Exemplo Completo de Dados Retornados

Quando você processa uma chave como `42250485179240000239550020004175361171503396`, recebe:

### 1. Arquivo XML Original (4.165 bytes)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe42250485179240000239550020004175361171503396">
      <!-- Dados completos da NFe -->
    </infNFe>
  </NFe>
</nfeProc>
```

### 2. Dados Estruturados Extraídos
```json
{
  "invoice_key": "42250485179240000239550020004175361171503396",
  "numero_nf": "417536",
  "serie_nf": "2", 
  "data_emissao": "2025-04-17",
  "valor_total": 9150.00,
  "cnpj_emitente": "85179240000239",
  "nome_emitente": "CORSUL COMERCIO E REPRESENTACOES DO SUL LTDA",
  "remetente_cidade": "JOINVILLE",
  "remetente_uf": "SC",
  "remetente_endereco": "RUA GUARUJA, 434, ITAUM",
  "remetente_cep": "89210300",
  "destinatario_cnpj_cpf": "00655209000193",
  "destinatario_razao": "CONSORCIO DE ALUMINIO DO MARANHAO",
  "destinatario_cidade": "SAO LUIS",
  "destinatario_uf": "MA",
  "destinatario_endereco": "RODOVIA BR 135, SN, DISTRITO INDUSTRIAL",
  "destinatario_cep": "65095050",
  "peso_bruto": 16.2,
  "quantidade_volumes": 2
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

## Estrutura de Preços via API

### Créditos XML
- **Starter**: 100 créditos por R$ 10,00 (R$ 0,10/XML)
- **Professional**: 500 créditos por R$ 40,00 (R$ 0,08/XML)
- **Enterprise**: 1.000 créditos por R$ 70,00 (R$ 0,07/XML)
- **Corporate**: 2.000 créditos por R$ 120,00 (R$ 0,06/XML)

### Recursos Inclusos
- **DANFE**: Sempre gratuito
- **Dados Estruturados**: Inclusos em cada processamento
- **API Unlimited**: Sem limite de requisições

## Exemplos de Uso

### Python com Dados Estruturados

```python
import requests
import time

# Configuração
BASE_URL = 'https://sua-app.replit.app/api/v1'
INVOICE_KEYS = ['42250485179240000239550020004175361171503396']

# Criar job
response = requests.post(f'{BASE_URL}/jobs', json={
    'invoice_keys': INVOICE_KEYS
})

job_data = response.json()
job_id = job_data['job_id']
print(f"Job criado: {job_id}")

# Monitorar progresso (otimizado em ~7.4s)
while True:
    status_response = requests.get(f'{BASE_URL}/jobs/{job_id}')
    status = status_response.json()
    
    print(f"Status: {status['status']}, Progresso: {status['progress']['percentage']}%")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(2)  # Verificação a cada 2 segundos

# Processar resultados
if status['status'] == 'completed':
    # 1. Dados estruturados no status do job
    xml_data = status.get('xml_data', {})
    print(f"NF: {xml_data.get('numero_nf')}")
    print(f"Emitente: {xml_data.get('nome_emitente')}")
    print(f"Valor: R$ {xml_data.get('valor_total')}")
    print(f"Peso: {xml_data.get('peso_bruto')} kg")
    print(f"Volumes: {xml_data.get('quantidade_volumes')}")
    
    # 2. Baixar arquivo XML original
    files_response = requests.get(f'{BASE_URL}/jobs/{job_id}/files')
    files = files_response.json()['files']
    
    for file_info in files:
        file_response = requests.get(f"https://sua-app.replit.app{file_info['download_url']}")
        
        with open(file_info['filename'], 'wb') as f:
            f.write(file_response.content)
        
        print(f"XML baixado: {file_info['filename']} ({file_info['size']} bytes)")
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