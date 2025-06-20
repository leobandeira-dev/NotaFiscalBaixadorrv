# 🤖 Automação CROSSWMS - Download de XMLs NFe

## 📋 Visão Geral

Sistema de automação que simula o comportamento humano real para buscar e baixar XMLs de Notas Fiscais Eletrônicas do site meudanfe.com.br. A automação replica exatamente os passos manuais: abrir navegador, navegar no site, preencher chave, clicar em buscar e fazer download automático.

## 🔧 Pré-requisitos

### 1. Google Chrome
- Baixe e instale a versão mais recente do Google Chrome
- Link: https://www.google.com/chrome/

### 2. ChromeDriver
- Baixe o ChromeDriver compatível com sua versão do Chrome
- Link: https://chromedriver.chromium.org/
- **IMPORTANTE**: Coloque o arquivo `chromedriver.exe` na mesma pasta do `automacao_crosswms.py`

### 3. Python 3.7+
- Baixe e instale Python: https://www.python.org/downloads/
- Durante a instalação, marque "Add Python to PATH"

### 4. Biblioteca Selenium
```bash
pip install selenium
```

## 📁 Estrutura de Pastas

O sistema criará automaticamente:
```
C:\CROSSWMS\
├── XMLs_Baixados\     # XMLs baixados automaticamente
└── logs\              # Logs da automação (futuro)
```

## 🚀 Como Usar

### 1. Preparação
1. Coloque o arquivo `automacao_crosswms.py` em uma pasta
2. Coloque o `chromedriver.exe` na mesma pasta
3. Abra o prompt de comando (cmd) na pasta

### 2. Executar Automação
```bash
python automacao_crosswms.py
```

### 3. Interface da Automação
1. **Campo Chave NFe**: Digite a chave de 44 dígitos
2. **Iniciar Automação**: Clica para começar o processo
3. **Abrir Pasta XMLs**: Abre a pasta onde os XMLs são salvos
4. **Log**: Mostra o progresso em tempo real

### 4. Processo Automático
A automação fará automaticamente:
1. ✅ Abrir Google Chrome
2. ✅ Navegar para meudanfe.com.br
3. ✅ Localizar campo de entrada
4. ✅ Digitar chave NFe (simulando velocidade humana)
5. ✅ Clicar em "Buscar DANFE/XML"
6. ✅ Localizar botão de download
7. ✅ Fazer download do XML
8. ✅ Salvar em C:\CROSSWMS\XMLs_Baixados\
9. ✅ Abrir pasta automaticamente
10. ✅ Opcional: Abrir sistema web para upload

## 🔍 Como Funciona

### Simulação Humana Real
- **Velocidade de digitação**: Simula velocidade humana (50ms por caractere)
- **Movimentos do mouse**: Rola a página para elementos visíveis
- **Tempos de espera**: Aguarda carregamento natural das páginas
- **Headers personalizados**: Remove indicadores de automação

### Detecção Inteligente
- **Campos de entrada**: Testa múltiplos seletores CSS
- **Botões**: Procura por texto e atributos diversos
- **Downloads**: Monitora pasta de destino em tempo real
- **Validação**: Confirma se XML contém a chave solicitada

### Tratamento de Erros
- **NFe não encontrada**: Informa se a nota não existe no sistema
- **Download indisponível**: Detecta quando XML não está público
- **Problemas técnicos**: Log detalhado de todos os passos

## 📝 Exemplo de Uso

```
=== INICIANDO AUTOMAÇÃO REAL ===
[14:30:15] Chave NFe: 35250652684982000181550010001110071066188885
[14:30:16] Navegando para meudanfe.com.br...
[14:30:19] Procurando campo de entrada da chave NFe...
[14:30:20] Campo de entrada encontrado!
[14:30:21] Preenchendo chave NFe...
[14:30:23] Procurando botão de busca...
[14:30:24] Botão de busca encontrado! Clicando...
[14:30:29] Aguardando resultados da busca...
[14:30:30] Procurando botão de download do XML...
[14:30:31] Botão de download encontrado! Iniciando download...
[14:30:35] Aguardando download completar...
[14:30:38] ✅ Download concluído: C:\CROSSWMS\XMLs_Baixados\NFe_35250652684982000181550010001110071066188885.xml
```

## ⚠️ Possíveis Situações

### ✅ Sucesso
- XML baixado na pasta C:\CROSSWMS\XMLs_Baixados\
- Pasta aberta automaticamente
- Opção de abrir sistema web para upload

### ❌ NFe Não Encontrada
- Sistema informa que a chave não existe
- Verificar se chave foi digitada corretamente

### ❌ Download Não Disponível
- NFe existe mas XML não está público
- Usar método manual ou solicitar XML do emissor

### ❌ Erro Técnico
- Verificar se Chrome e ChromeDriver estão atualizados
- Conferir se há conexão com internet
- Consultar log detalhado na interface

## 🔧 Solução de Problemas

### Erro "ChromeDriver não encontrado"
```bash
# Baixar ChromeDriver e colocar na pasta do script
# Verificar versão do Chrome em: chrome://version/
```

### Erro "Selenium não instalado"
```bash
pip install selenium
```

### Erro "Campo não encontrado"
```bash
# Site pode ter mudado - verificar log detalhado
# Tentar novamente após alguns minutos
```

### Chrome não abre
```bash
# Fechar todos os Chrome abertos
# Executar como Administrador
# Verificar antivírus
```

## 🔗 Integração com Sistema Web

Após download bem-sucedido:
1. Sistema oferece abrir automaticamente o CROSSWMS Web
2. Usuário pode fazer upload do XML baixado
3. Campos são preenchidos automaticamente

## 📞 Suporte

Para problemas técnicos:
1. Verificar log detalhado na interface
2. Confirmar pré-requisitos instalados
3. Testar com outra chave NFe
4. Verificar conexão com internet

## 🔄 Atualizações Futuras

- ✅ Processamento em lote (múltiplas chaves)
- ✅ Agendamento automático
- ✅ Integração API SEFAZ
- ✅ Dashboard de monitoramento
- ✅ Relatórios de download

---

**Desenvolvido para CROSSWMS - Sistema de Gestão Logística**