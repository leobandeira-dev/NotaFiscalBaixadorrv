# XML Downloader

Sistema completo para download automático em lote de arquivos XML de notas fiscais, com interface web e API REST.

## Funcionalidades

### Interface Web
- **Interface intuitiva** com tema escuro Bootstrap
- **Upload em lote** de chaves de notas fiscais
- **Progresso em tempo real** com barra de progresso animada
- **Download individual** de arquivos XML
- **Validação automática** do formato das chaves (44 dígitos)
- **Logs detalhados** para monitoramento

### API REST
- **Endpoints RESTful** para integração com sistemas externos
- **Processamento assíncrono** com jobs em background
- **Monitoramento de progresso** via polling
- **Download programático** de arquivos
- **Suporte a CORS** para aplicações web

### Automação
- **Selenium WebDriver** para automação completa do navegador
- **Chrome headless** otimizado para performance
- **Detecção inteligente** de elementos da página
- **Extração robusta** de conteúdo XML
- **Tratamento de erros** abrangente

## Instalação e Configuração

O sistema está configurado para execução no Replit com todas as dependências já instaladas:

```bash
# O sistema iniciará automaticamente com:
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Dependências
- Python 3.11
- Flask + Flask-CORS
- Selenium WebDriver
- Chrome/Chromium browser
- Bootstrap 5 (CDN)
- Font Awesome 6 (CDN)

## Uso da Interface Web

1. **Acesse a aplicação** no navegador
2. **Cole as chaves** de notas fiscais (uma por linha) no campo de texto
3. **Clique em "Iniciar Downloads"** para começar o processamento
4. **Acompanhe o progresso** na tela de monitoramento
5. **Baixe os arquivos** individualmente quando concluído

### Formato das Chaves
As chaves devem ter exatamente 44 dígitos numéricos:
```
35250162954987000130550020001854371034511150
```

## Uso da API REST

### URL Base
```
https://sua-aplicacao.replit.app/api/v1
```

### Endpoints Principais

#### Verificar Status da API
```bash
GET /api/v1/health
```

#### Criar Job de Download
```bash
POST /api/v1/jobs
Content-Type: application/json

{
    "invoice_keys": [
        "35250162954987000130550020001854371034511150",
        "35250162954987000130550020001854371034511151"
    ]
}
```

#### Monitorar Progresso
```bash
GET /api/v1/jobs/{job_id}
```

#### Listar Arquivos Baixados
```bash
GET /api/v1/jobs/{job_id}/files
```

#### Baixar Arquivo XML
```bash
GET /api/v1/jobs/{job_id}/files/{filename}
```

### Exemplo com cURL
```bash
# Criar job
curl -X POST https://sua-app.replit.app/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"invoice_keys": ["35250162954987000130550020001854371034511150"]}'

# Verificar status (substitua JOB_ID)
curl https://sua-app.replit.app/api/v1/jobs/JOB_ID

# Baixar arquivo (substitua JOB_ID e FILENAME)
curl -O https://sua-app.replit.app/api/v1/jobs/JOB_ID/files/FILENAME.xml
```

## Cliente Python

Use o cliente Python incluído para integração fácil:

```python
from api_client_example import MeuDANFeAPIClient

# Inicializar cliente
client = MeuDANFeAPIClient("https://sua-app.replit.app")

# Baixar XMLs automaticamente
invoice_keys = ["35250162954987000130550020001854371034511150"]
files = client.download_invoices(invoice_keys, "./downloads")

print(f"Baixados {len(files)} arquivos XML")
```

## Estrutura do Projeto

```
├── app.py                 # Aplicação Flask principal com API
├── automation.py          # Sistema de automação com Selenium
├── main.py               # Ponto de entrada da aplicação
├── templates/            # Templates HTML Jinja2
│   ├── index.html        # Página inicial com formulário
│   └── download.html     # Página de progresso
├── static/               # Arquivos estáticos
│   ├── css/custom.css    # Estilos personalizados
│   └── js/main.js        # JavaScript para validação
├── downloads/            # Diretório para arquivos baixados
├── api_client_example.py # Cliente Python de exemplo
└── API_DOCUMENTATION.md  # Documentação completa da API
```

## Tecnologias Utilizadas

### Backend
- **Flask**: Framework web Python
- **Selenium**: Automação de navegador
- **Chrome WebDriver**: Controle do navegador
- **Threading**: Processamento em background
- **UUID**: Geração de IDs únicos para jobs

### Frontend
- **Bootstrap 5**: Framework CSS responsivo
- **Font Awesome**: Biblioteca de ícones
- **JavaScript Vanilla**: Interatividade e validação
- **AJAX**: Atualizações em tempo real

### Automação
- **Selenium WebDriver**: Controle programático do navegador
- **Chrome Headless**: Navegador sem interface gráfica
- **Strategy Pattern**: Múltiplas estratégias de extração XML
- **Retry Logic**: Tentativas automáticas em caso de falha

## Configuração para Produção

### Variáveis de Ambiente
- `SESSION_SECRET`: Chave secreta para sessões Flask
- `DATABASE_URL`: URL do banco PostgreSQL (configurado mas não usado)

### Otimizações
- **Gunicorn**: Servidor WSGI para produção
- **Worker processes**: Múltiplos workers para concorrência
- **Connection pooling**: Pool de conexões do banco
- **Headless Chrome**: Performance otimizada

## Monitoramento e Logs

O sistema inclui logging detalhado para monitoramento:

```python
# Níveis de log configurados
DEBUG: Detalhes de automação Selenium
INFO:  Progresso de jobs e operações principais
ERROR: Falhas e exceções
```

### Métricas Disponíveis
- Número total de jobs processados
- Taxa de sucesso/falha por job
- Tempo médio de processamento
- Tamanho dos arquivos baixados
- Erros por tipo

## Limitações e Considerações

### Rate Limiting
- Recomendado: máximo 100 chaves por job
- Intervalo entre requests: mínimo 1 segundo
- Jobs simultâneos: máximo 10 por IP

### Tratamento de Erros
- **Chaves inválidas**: Validação de formato
- **Conexão**: Retry automático em falhas temporárias
- **Timeout**: Timeout configurável para operações
- **Recursos**: Cleanup automático de WebDriver

### Segurança
- **Input validation**: Validação rigorosa de entrada
- **CORS**: Configurado para APIs cross-origin
- **Session management**: Sessões seguras Flask
- **Error handling**: Não exposição de informações sensíveis

## Desenvolvimento

### Executar Localmente
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python main.py
```

### Testes
```bash
# Testar conexão
python -c "from automation import InvoiceDownloader; d = InvoiceDownloader(); print(d.test_connection())"

# Testar API
curl http://localhost:5000/api/v1/health
```

## Changelog

- **2025-06-19**: Sistema completo implementado
- **2025-06-19**: API REST adicionada
- **2025-06-19**: Cliente Python criado
- **2025-06-19**: Documentação completa
- **2025-06-19**: Pronto para produção

## Suporte

Para dúvidas ou problemas:
1. Consulte a documentação da API em `API_DOCUMENTATION.md`
2. Verifique os logs na interface web
3. Use o endpoint `/api/v1/test` para diagnóstico
4. Examine o código de exemplo em `api_client_example.py`

## Licença

Sistema desenvolvido para automação de downloads do MeuDANFe.com.br.
Uso responsável conforme os termos de serviço do site.