# SaaS Atendimento Flui

Sistema SaaS Multi-Nicho para profissionais de saúde e bem-estar, com foco inicial em Pilates.

## Visão Geral

O Flui é uma plataforma SaaS modular para gerenciamento de atendimentos, agendamentos e comunicação com clientes, desenvolvida com arquitetura hexagonal (ports and adapters) seguindo princípios SOLID.

## Tecnologias Principais

- **Backend**: FastAPI (Python)
- **Banco de Dados**: PostgreSQL com SQLAlchemy
- **Cache**: Redis
- **Mensageria**: WhatsApp (Twilio) e Email (SMTP)
- **IA**: Serviço local de IA (LocalAI) para FAQ e assistência
- **Containerização**: Docker e Docker Compose

## Funcionalidades

- Gerenciamento de usuários e autenticação
- Cadastro de clientes e profissionais
- Sistema de agendamentos
- Comunicação automatizada via WhatsApp/Email
- FAQ inteligente com IA
- Sistema de plugins para extensão de funcionalidades
- Multi-tenancy (configurável)

## Estrutura do Projeto

O projeto segue uma arquitetura hexagonal com clara separação entre:

- **Core**: Regras de negócio e interfaces
- **Adapters**: Implementações concretas (banco de dados, mensageria, etc.)
- **API**: Controllers e rotas

## Requisitos

- Python 3.10+
- Docker e Docker Compose
- PostgreSQL
- Redis

## Configuração e Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/danilolopes-ds-ai/saas-test.git
   cd saas-test
   ```

2. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

3. Inicie os serviços com Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Acesse a documentação da API:
   ```
   http://localhost:8000/api/docs
   ```

## Desenvolvimento

Para ambiente de desenvolvimento:

```bash
# Instalar dependências de desenvolvimento
pip install -r backend-requirements-dev.txt

# Executar testes
pytest

# Executar servidor de desenvolvimento
uvicorn app.main:app --reload
```

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Danilo Lopes - danilolopes.ai@icloud.com
