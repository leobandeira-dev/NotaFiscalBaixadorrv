# CROSS XML Downloader PRO - API v2.0

## Visão Geral

A API REST do CROSS XML Downloader PRO permite integração automatizada para download e processamento completo de arquivos XML de notas fiscais brasileiras (NFe). A API oferece endpoints para criar jobs de download, monitorar progresso, extrair dados estruturados e baixar arquivos XML com informações detalhadas.

**✨ Performance Ultra-Otimizada:** Sistema com automação otimizada que reduz tempo de processamento em 87% (de ~57s para ~7s por XML).

**🔍 Extração Completa de Dados:** Processamento automático de todos os campos da NFe incluindo dados empresariais, financeiros e logísticos.

**Base URL:** `https://crossxml.com.br/api/v1`

## Dados Extraídos Automaticamente

### 🏢 Informações da Empresa Emitente
- CNPJ/CPF, Razão Social, Nome Fantasia
- Endereço completo (logradouro, número, bairro, cidade, UF, CEP)
- Telefone, Inscrição Estadual

### 📋 Dados da Nota Fiscal
- Número da NF, Série, Data de Emissão
- Valor Total, Chave de Acesso (44 dígitos)
- Natureza da Operação, Tipo de Documento

### 🛍️ Informações de Produtos
- Código, Descrição, Quantidade
- Valor Unitário, Valor Total
- Unidade de Medida, NCM, CFOP

### 🚚 Dados Logísticos
- Peso Bruto/Líquido, Quantidade de Volumes
- Dados do Destinatário (CNPJ, endereço completo)
- Informações de Transporte, Transportadora

### 💰 Informações Financeiras
- Formas de Pagamento, Vencimentos
- Impostos (ICMS, IPI, PIS, COFINS)
- Descontos, Frete, Outras Despesas

## Exemplo Prático Validado

### 🔍 Teste com Chave Real
**Chave de Teste:** `35250513516247000107550010000113401146202508`

Esta chave foi **validada** e retorna dados completos:

```json
{
  "empresa_emitente": {
    "cnpj": "13516247000107",
    "razao_social": "REAL SINALIZACAO INDUSTRIA COMERCIO E SERVICOS LTDA ME",
    "nome_fantasia": "REAL SINALIZACAO",
    "endereco": "RUA ORCO, 143, JARDIM ADELFIORE - São Paulo/SP",
    "cep": "05223110",
    "telefone": "(11) 3917-5139"
  },
  "nota_fiscal": {
    "numero": "11340",
    "serie": "1",
    "data_emissao": "2025-05-27",
    "valor_total": "R$ 13.585,25",
    "chave_acesso": "35250513516247000107550010000113401146202508"
  },
  "destinatario": {
    "cnpj": "22525037000176",
    "razao_social": "FORT CLEAN - DISTRIBUIDORA LTDA",
    "endereco": "RUA PIAUI, 588, NOVA IMPERATRIZ - Imperatriz/MA",
    "cep": "65907100",
    "telefone": "(99) 99171-4951"
  },
  "transporte": {
    "peso_bruto": "1.225 kg",
    "quantidade_volumes": 62,
    "transportadora": "CLIENTE RETIRA"
  },
  "produto": {
    "codigo": "000.001",
    "descricao": "ADESIVO FIXADOR",
    "quantidade": "1.225,0000 KG",
    "valor_unitario": "R$ 11,09",
    "ncm": "35061090"
  }
}
```

**⚡ Performance:** Processamento em ~7 segundos com extração completa de todos os dados estruturados.

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
    "service": "XML Downloader API",
    "timestamp": "2025-06-19T04:00:00.000000"
}
```

### 2. Criar Job de Download

Cria um novo job para download de XMLs de notas fiscais.

**Endpoint:** `POST /api/v1/jobs`

**Body (Exemplo com Chave Validada):**
```json
{
    "invoice_keys": [
        "35250513516247000107550010000113401146202508"
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

**Resposta (Exemplo Real com Chave Validada):**
```json
{
    "job_id": "2d2076f3-9bc9-4274-8961-0b3e84b36da7",
    "status": "completed",
    "progress": {
        "total_keys": 1,
        "processed": 1,
        "successful": 1,
        "failed": 0,
        "percentage": 100.0
    },
    "files": [
        "35250513516247000107550010000113401146202508.xml"
    ],
    "errors": [],
    "created_at": "2025-07-04T20:58:48.171131",
    "completed_at": "2025-07-04T21:05:52.000000"
}
```

### 📊 Dados Extraídos Automaticamente

Quando o job é concluído, o sistema automaticamente extrai e armazena **todas as informações** do XML:

```json
{
    "xml_data": {
        "cnpj_emitente": "13516247000107",
        "nome_emitente": "REAL SINALIZACAO INDUSTRIA COMERCIO E SERVICOS LTDA ME",
        "numero_nf": "11340",
        "serie_nf": "1",
        "data_emissao": "2025-05-27",
        "valor_total": 13585.25,
        "peso_bruto": 1225.0,
        "quantidade_volumes": 62,
        "remetente_razao": "REAL SINALIZACAO INDUSTRIA COMERCIO E SERVICOS LTDA ME",
        "remetente_cidade": "SAO PAULO",
        "remetente_uf": "SP",
        "remetente_endereco": "RUA ORCO, 143, JARDIM ADELFIORE",
        "remetente_cep": "05223110",
        "destinatario_cnpj_cpf": "22525037000176",
        "destinatario_razao": "FORT CLEAN - DISTRIBUIDORA LTDA",
        "destinatario_cidade": "IMPERATRIZ",
        "destinatario_uf": "MA",
        "destinatario_endereco": "RUA PIAUI, 588, NOVA IMPERATRIZ",
        "destinatario_cep": "65907100"
    },
    "processing_time": "~7 segundos",
    "auto_generated": {
        "danfe_available": true,
        "transport_labels_available": true,
        "structured_data_ready": true
    }
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
        "response_time": "7.4s",
        "optimization_status": "active",
        "performance_improvement": "87% faster than baseline"
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
response = requests.post('https://crossxml.com.br/api/v1/jobs', json={
    'invoice_keys': ['35250513516247000107550010000113401146202508']
})

job_data = response.json()
job_id = job_data['job_id']

# Monitorar progresso
while True:
    status_response = requests.get(f'https://crossxml.com.br/api/v1/jobs/{job_id}')
    status = status_response.json()
    
    print(f"Status: {status['status']}, Progresso: {status['progress']['percentage']}%")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(5)

# Baixar arquivos
if status['status'] == 'completed':
    files_response = requests.get(f'https://crossxml.com.br/api/v1/jobs/{job_id}/files')
    files = files_response.json()['files']
    
    for file_info in files:
        file_response = requests.get(f"https://crossxml.com.br{file_info['download_url']}")
        
        with open(file_info['filename'], 'wb') as f:
            f.write(file_response.content)
        
        print(f"Arquivo baixado: {file_info['filename']}")
```

### cURL

```bash
# Criar job
curl -X POST https://crossxml.com.br/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_keys": ["35250513516247000107550010000113401146202508"]
  }'

# Verificar status
curl https://crossxml.com.br/api/v1/jobs/JOB_ID

# Listar arquivos
curl https://crossxml.com.br/api/v1/jobs/JOB_ID/files

# Baixar arquivo
curl -O https://crossxml.com.br/api/v1/jobs/JOB_ID/files/FILENAME.xml
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function downloadInvoices(invoiceKeys) {
    const baseUrl = 'https://crossxml.com.br/api/v1';
    
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

## Performance e Rate Limits

### Performance Otimizada
- **⚡ Velocidade Ultra-Rápida:** Processamento médio de 7,4 segundos por XML (87% mais rápido que versões anteriores)
- **🚀 Automação Inteligente:** Sistema com estratégia de busca por texto direto, evitando seletores lentos
- **🔄 Fallback Automático:** Sistema reverte para método tradicional quando necessário
- **📊 Monitoramento:** Logs detalhados de performance para cada download

### Melhorias Técnicas Implementadas (v2.0)
- **Speed-Optimized Automation:** Nova versão `SpeedOptimizedInvoiceDownloader` que pula seletores convencionais
- **Text Search Strategy:** Uso de Ctrl+F + TreeWalker JavaScript para localização ultra-rápida de botões
- **Reduced Timeouts:** Timeouts otimizados para ambiente de produção (3s→2s, 5s→2s, 0.8s→0.3s)
- **Direct JavaScript Execution:** Execução direta de cliques via JavaScript, evitando interações lentas do WebDriver
- **Intelligent Fallback:** Sistema automaticamente usa método original se otimização falhar

### Rate Limits
Para evitar sobrecarga do servidor, recomenda-se:
- Máximo de 100 chaves por job
- Máximo de 10 jobs simultâneos por IP
- Intervalo mínimo de 1 segundo entre requests
- Para volumes maiores, considere usar múltiplos jobs menores para melhor performance

## Suporte

Para dúvidas sobre a API, consulte a documentação ou entre em contato através dos canais de suporte.