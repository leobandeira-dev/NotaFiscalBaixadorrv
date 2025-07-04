# 🚀 Guia de Conexão - API CROSS XML

## 📋 Pré-requisitos

1. **Conta ativa** no CROSS XML Downloader PRO
2. **Créditos disponíveis** para download de XMLs (R$ 0,06-0,10 por XML)
3. **Credenciais da API** (geradas no painel)

## 🔑 Passo 1: Gerar Credenciais da API

1. Acesse seu painel: `https://sua-aplicacao.replit.app/api-docs`
2. Na seção **"Gerenciamento de Credenciais"**, clique em **"Gerar Credenciais"**
3. Copie e guarde com segurança:
   - **API Key**: `api_xxxxxxxxxxxxxxxx`
   - **API Secret**: `secret_xxxxxxxxxxxxxxxx`

⚠️ **Importante**: Mantenha essas credenciais seguras - elas dão acesso total à sua conta!

## 🌐 Passo 2: URL Base da API

```
URL Base: https://sua-aplicacao.replit.app/api/v1
```

**Substitua `sua-aplicacao.replit.app` pela URL real do seu sistema**

## 🧪 Passo 3: Teste de Conexão

### Python (Recomendado)

```python
import requests
import json

# Suas credenciais
API_KEY = "api_xxxxxxxxxxxxxxxx"
API_SECRET = "secret_xxxxxxxxxxxxxxxx"
BASE_URL = "https://sua-aplicacao.replit.app/api/v1"

# Teste de conectividade
response = requests.get(f"{BASE_URL}/health")
print("Status da API:", response.json())
```

### JavaScript/Node.js

```javascript
const API_KEY = "api_xxxxxxxxxxxxxxxx";
const API_SECRET = "secret_xxxxxxxxxxxxxxxx";
const BASE_URL = "https://sua-aplicacao.replit.app/api/v1";

// Teste de conectividade
fetch(`${BASE_URL}/health`)
  .then(response => response.json())
  .then(data => console.log("Status da API:", data));
```

### cURL (Terminal)

```bash
curl -X GET "https://sua-aplicacao.replit.app/api/v1/health"
```

## 📤 Passo 4: Primeiro Download de XML

### Python - Exemplo Completo

```python
import requests
import json
import time

class CrossXMLAPI:
    def __init__(self, api_key, api_secret, base_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'X-API-Secret': api_secret
        }
    
    def criar_job(self, chaves_xml):
        """Cria um job de download para as chaves fornecidas"""
        url = f"{self.base_url}/jobs"
        data = {"invoice_keys": chaves_xml}
        
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()
    
    def status_job(self, job_id):
        """Verifica o status de um job"""
        url = f"{self.base_url}/jobs/{job_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def baixar_xml(self, job_id, nome_arquivo, pasta_destino="./"):
        """Baixa um arquivo XML específico"""
        url = f"{self.base_url}/jobs/{job_id}/files/{nome_arquivo}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            caminho = f"{pasta_destino}{nome_arquivo}"
            with open(caminho, 'wb') as f:
                f.write(response.content)
            return caminho
        return None

# Exemplo de uso
api = CrossXMLAPI(
    api_key="api_xxxxxxxxxxxxxxxx",
    api_secret="secret_xxxxxxxxxxxxxxxx", 
    base_url="https://sua-aplicacao.replit.app/api/v1"
)

# 1. Criar job com chaves XML
chaves = ["35250513516247000107550010000113401146202508"]
job = api.criar_job(chaves)
job_id = job["job_id"]
print(f"Job criado: {job_id}")

# 2. Aguardar conclusão
while True:
    status = api.status_job(job_id)
    print(f"Status: {status['status']} - Progresso: {status['progress']['percentage']}%")
    
    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        print("Job falhou:", status.get("errors"))
        break
    
    time.sleep(2)

# 3. Baixar arquivos
for arquivo in status["files"]:
    caminho = api.baixar_xml(job_id, arquivo["filename"])
    print(f"XML baixado: {caminho}")
```

### JavaScript - Exemplo Completo

```javascript
class CrossXMLAPI {
    constructor(apiKey, apiSecret, baseUrl) {
        this.apiKey = apiKey;
        this.apiSecret = apiSecret;
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey,
            'X-API-Secret': apiSecret
        };
    }

    async criarJob(chavesXml) {
        const response = await fetch(`${this.baseUrl}/jobs`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ invoice_keys: chavesXml })
        });
        return await response.json();
    }

    async statusJob(jobId) {
        const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
            headers: this.headers
        });
        return await response.json();
    }

    async baixarXml(jobId, nomeArquivo) {
        const response = await fetch(`${this.baseUrl}/jobs/${jobId}/files/${nomeArquivo}`, {
            headers: this.headers
        });
        return await response.blob();
    }
}

// Exemplo de uso
const api = new CrossXMLAPI(
    "api_xxxxxxxxxxxxxxxx",
    "secret_xxxxxxxxxxxxxxxx",
    "https://sua-aplicacao.replit.app/api/v1"
);

async function exemploDownload() {
    // 1. Criar job
    const job = await api.criarJob(["35250513516247000107550010000113401146202508"]);
    console.log("Job criado:", job.job_id);

    // 2. Aguardar conclusão
    let status;
    do {
        status = await api.statusJob(job.job_id);
        console.log(`Status: ${status.status} - ${status.progress.percentage}%`);
        await new Promise(resolve => setTimeout(resolve, 2000));
    } while (status.status === "running");

    // 3. Baixar arquivos
    if (status.status === "completed") {
        for (const arquivo of status.files) {
            const blob = await api.baixarXml(job.job_id, arquivo.filename);
            console.log(`XML baixado: ${arquivo.filename}`);
        }
    }
}

exemploDownload();
```

## 📊 Estrutura de Resposta

### Job Status Response
```json
{
    "job_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "progress": {
        "total_keys": 1,
        "processed": 1,
        "successful": 1,
        "failed": 0,
        "percentage": 100.0
    },
    "files": [
        {
            "filename": "35250513516247000107550010000113401146202508.xml",
            "size": 4165,
            "download_url": "/api/v1/jobs/123.../files/352505..."
        }
    ],
    "extracted_data": [
        {
            "chave_nf": "35250513516247000107550010000113401146202508",
            "numero_nf": "11340",
            "serie_nf": "1",
            "data_emissao": "2025-06-19",
            "valor_total": 1850.00,
            "peso_bruto": 25.5,
            "quantidade_volumes": 3,
            "nome_emitente": "REAL SINALIZACAO LTDA",
            "emitente_cidade": "JOINVILLE",
            "emitente_uf": "SC",
            "destinatario_nome": "CORSUL COMERCIO",
            "destinatario_cidade": "SAO LUIS",
            "destinatario_uf": "MA"
        }
    ]
}
```

## 🔄 Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Status da API |
| `POST` | `/jobs` | Criar job de download |
| `GET` | `/jobs/{job_id}` | Status do job |
| `GET` | `/jobs` | Listar todos os jobs |
| `GET` | `/jobs/{job_id}/files` | Listar arquivos do job |
| `GET` | `/jobs/{job_id}/files/{filename}` | Baixar arquivo XML |

## 💰 Custos por Operação

- **Download XML**: R$ 0,06 - 0,10 por chave (dependendo do volume)
- **Consulta Status**: Gratuito
- **Download Arquivo**: Gratuito (após download inicial)

## 🚨 Limites e Rate Limiting

- **Rate Limit**: 100 requisições por minuto
- **Jobs Simultâneos**: Máximo 5 por usuário
- **Timeout**: 60 segundos por chave
- **Tamanho Máximo**: 1000 chaves por job

## 🛠️ Tratamento de Erros

### Códigos de Status HTTP

- `200` - Sucesso
- `400` - Erro na requisição (dados inválidos)
- `401` - Não autorizado (credenciais inválidas)
- `403` - Sem créditos suficientes
- `404` - Job/arquivo não encontrado
- `429` - Rate limit excedido
- `500` - Erro interno do servidor

### Exemplo de Resposta de Erro

```json
{
    "error": "insufficient_credits",
    "message": "Créditos insuficientes para processar 5 chaves. Saldo atual: 2",
    "details": {
        "required_credits": 5,
        "current_balance": 2,
        "cost_per_key": 0.10
    }
}
```

## 📞 Suporte

- **Documentação Completa**: `/api-docs` no painel
- **Logs de Atividade**: Seção "Histórico" no painel
- **Rate Limits**: Monitoramento em tempo real no dashboard

## 🔧 Dicas de Integração

1. **Cache de Dados**: Armazene dados extraídos para evitar reprocessamento
2. **Retry Logic**: Implemente tentativas automáticas para falhas temporárias  
3. **Polling Inteligente**: Use intervalos progressivos para verificar status
4. **Batch Processing**: Processe chaves em lotes para melhor performance
5. **Error Handling**: Trate todos os códigos de erro adequadamente

---

✅ **API funcionando perfeitamente com downloads otimizados em ~7-8 segundos por chave!**