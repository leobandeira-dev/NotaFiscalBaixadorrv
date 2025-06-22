# CROSS XML Downloader PRO

![CROSS XML](https://img.shields.io/badge/CROSS_XML-Downloader_PRO-8A05BE?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3+-green?style=for-the-badge&logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=for-the-badge&logo=postgresql)

## 🎯 Sobre o Projeto

**CROSS XML Downloader PRO** é uma plataforma SaaS completa para automação de download de XMLs de notas fiscais brasileiras e geração de etiquetas de transporte. Desenvolvida especificamente para transportadoras e embarcadores que precisam acessar XMLs usando chaves de nota fiscal.

### 📊 Funcionalidades Principais

- **Download Automatizado de XMLs** - Acesse qualquer XML usando a chave da nota fiscal (44 dígitos)
- **Geração de DANFE** - Sempre gratuita, layout oficial SEFAZ
- **Etiquetas de Transporte Integrada** - Sistema multi-layout com QR codes e logos personalizadas
- **Importação via Email** - Processamento automático de XMLs recebidos por email
- **API REST Completa** - Integração com sistemas externos
- **Sistema de Créditos** - Cobrança por uso com pacotes flexíveis

### 💰 Pricing

- **XML Download**: R$ 0,06 - 0,10 por arquivo (volume-based)
- **DANFE**: Sempre gratuito
- **Etiquetas de Transporte**: R$ 49,90/mês
- **Período de Teste**: 7 dias grátis para novos usuários

## 🚀 Tecnologias Utilizadas

### Backend
- **Python 3.11** - Linguagem principal
- **Flask** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **PostgreSQL** - Banco de dados principal
- **Selenium** - Automação web para download de XMLs
- **Gunicorn** - Servidor WSGI para produção

### Frontend
- **HTML5/CSS3** - Interface responsiva
- **Bootstrap 5** - Framework CSS
- **JavaScript** - Interatividade e AJAX
- **Font Awesome** - Ícones

### Integrações
- **Stripe** - Processamento de pagamentos
- **Google OAuth** - Autenticação social
- **SendGrid** - Envio de emails

### Automação
- **Chrome WebDriver** - Navegação automatizada
- **ReportLab** - Geração de PDFs
- **BrazilFiscalReport** - DANFE oficial SEFAZ

## 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL 15+
- Chrome/Chromium
- Node.js (para alguns recursos)

## 🛠️ Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/cross-xml-downloader.git
cd cross-xml-downloader
```

### 2. Configuração do ambiente

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Database
DATABASE_URL=postgresql://usuario:senha@localhost:5432/crossxml

# Flask
SESSION_SECRET=sua_chave_secreta_aqui

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=seu_client_id
GOOGLE_OAUTH_CLIENT_SECRET=seu_client_secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...

# Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha
```

### 4. Configuração do banco

```bash
# Criar banco de dados
createdb crossxml

# Executar migrações (se disponível)
python -c "from new_app import app, db; app.app_context().push(); db.create_all()"
```

### 5. Executar a aplicação

```bash
# Desenvolvimento
python main.py

# Produção
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

A aplicação estará disponível em `http://localhost:5000`

## 📊 Estrutura do Projeto

```
cross-xml-downloader/
├── 📁 static/              # Arquivos estáticos (CSS, JS, images)
├── 📁 templates/           # Templates HTML
├── 📁 downloads/           # XMLs baixados
├── 📁 attached_assets/     # Assets anexados
├── 📄 new_app.py          # Aplicação principal
├── 📄 models.py           # Modelos do banco de dados
├── 📄 automation_fixed.py # Sistema de automação
├── 📄 stripe_integration.py # Integração Stripe
├── 📄 email_processor.py  # Processamento de emails
├── 📄 danfe_generator.py  # Gerador de DANFE
├── 📄 requirements.txt    # Dependências Python
└── 📄 README.md          # Documentação
```

## 🔧 Configuração de Produção

### Deploy no Replit

1. Importe o projeto no Replit
2. Configure as variáveis de ambiente no painel Secrets
3. Execute o comando de inicialização:

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### Deploy no Heroku

```bash
# Login no Heroku
heroku login

# Criar aplicação
heroku create cross-xml-downloader

# Configurar banco PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main
```

## 📡 API REST

### Autenticação

```bash
# Gerar credenciais API
curl -X POST https://crossxml.com.br/api/generate-credentials \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

### Endpoints principais

```bash
# Criar job de download
curl -X POST https://crossxml.com.br/api/v1/jobs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "invoice_keys": ["42250485179240000239550020004175341622314954"],
    "callback_url": "https://webhook.example.com"
  }'

# Verificar status do job
curl https://crossxml.com.br/api/v1/jobs/{job_id} \
  -H "X-API-Key: YOUR_API_KEY"

# Download do arquivo
curl https://crossxml.com.br/api/v1/jobs/{job_id}/files/{filename} \
  -H "X-API-Key: YOUR_API_KEY" \
  -o arquivo.xml
```

## 🏗️ Arquitetura do Sistema

### Fluxo de Download de XML

1. **Entrada do usuário** - Chaves de 44 dígitos via interface web ou API
2. **Validação** - Verificação do formato e créditos disponíveis
3. **Automação** - Selenium navega automaticamente no sistema fiscal
4. **Processamento** - XML extraído e salvo no banco de dados
5. **Entrega** - Arquivo disponibilizado para download

### Sistema de Créditos

- **Trial**: 7 dias gratuitos para novos usuários
- **Pacotes**: 100, 500, 1000, 2000 créditos
- **Cobrança**: Por uso, débito automático via Stripe
- **Relatórios**: Histórico completo de uso

### Segurança

- **Autenticação**: Google OAuth + sessões Flask
- **Rate Limiting**: Proteção contra abuso
- **Logs**: Monitoramento completo de atividades
- **HTTPS**: Criptografia end-to-end

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

- **Website**: [crossxml.com.br](https://crossxml.com.br)
- **Email**: suporte@crossxml.com.br
- **Documentação**: [docs.crossxml.com.br](https://docs.crossxml.com.br)

## 📈 Status do Projeto

- ✅ Download automatizado de XMLs
- ✅ Geração de DANFE
- ✅ Sistema de créditos
- ✅ API REST completa
- ✅ Etiquetas de transporte
- ✅ Importação via email
- ✅ Google OAuth
- ✅ Integração Stripe
- 🔄 Dashboard analytics
- 🔄 App mobile

---

**CROSS XML Downloader PRO** - Acesse qualquer XML usando a chave da nota fiscal