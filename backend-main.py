"""
Aplicação principal do SaaS Multi-Nicho para profissionais de saúde e bem-estar.
Implementa arquitetura hexagonal (ports and adapters) seguindo princípios SOLID.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.di_container import setup_di
from app.utils.logging import setup_logging

# Configuração de logging estruturado
logger = setup_logging()

# Context manager para inicialização/encerramento de recursos
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para inicialização e encerramento de recursos
    na inicialização/desligamento da aplicação.
    """
    # Inicialização de recursos
    logger.info("🚀 Iniciando aplicação")
    
    # Registrar recursos compartilhados na aplicação
    logger.info("🔌 Configurando container de dependências")
    app.state.injector = setup_di()
    
    logger.info("✅ Aplicação iniciada com sucesso")
    yield
    
    # Limpeza de recursos ao encerrar
    logger.info("🛑 Finalizando aplicação")
    # Fechar conexões de banco e outros recursos
    logger.info("👋 Aplicação finalizada")


# Criação da aplicação FastAPI
def create_app() -> FastAPI:
    """
    Factory de criação da aplicação FastAPI com todas as configurações.
    Separado em função para facilitar testes.
    """
    app = FastAPI(
        title="SaaS Multi-Nicho para Saúde e Bem-estar",
        description="API para SaaS modular com arquitetura SOLID",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
    )
    
    # Configuração de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Inclusão de rotas
    app.include_router(api_router, prefix=settings.API_PREFIX)
    
    return app


# Instância da aplicação para ser utilizada pelo servidor ASGI
app = create_app()