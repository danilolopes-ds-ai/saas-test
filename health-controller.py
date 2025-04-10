"""
Controlador para endpoints de saúde e monitoramento do sistema.
"""
import logging
from fastapi import APIRouter, Depends, Request, status
from typing import Dict, Any

from app.adapters.cache.redis_cache import RedisCache
from app.adapters.db.database import Database
from app.core.interfaces.ai_service import IAIService


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Verifica se a API está funcionando.",
)
async def health_check():
    """
    Endpoint básico para verificar se a API está respondendo.
    
    Returns:
        Resposta com status OK.
    """
    return {"status": "ok"}


@router.get(
    "/detailed",
    status_code=status.HTTP_200_OK,
    summary="Health Check Detalhado",
    description="Verifica a saúde de todos os componentes do sistema.",
)
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """
    Endpoint para verificar a saúde de todos os componentes do sistema.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Resposta com status de cada componente.
    """
    # Obter dependências via DI container
    injector = request.app.state.injector
    database = injector.get(Database)
    redis = injector.get(RedisCache)
    ai_service = injector.get(IAIService)
    
    results = {
        "api": {"status": "ok"}
    }
    
    # Verificar banco de dados
    try:
        await database.health_check()
        results["database"] = {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro no health check do banco de dados: {str(e)}")
        results["database"] = {"status": "error", "message": str(e)}
    
    # Verificar Redis
    try:
        redis_health = await redis.health_check()
        results["redis"] = {"status": "ok" if redis_health else "error"}
    except Exception as e:
        logger.error(f"Erro no health check do Redis: {str(e)}")
        results["redis"] = {"status": "error", "message": str(e)}
    
    # Verificar serviço de IA
    try:
        ai_health = await ai_service.health_check()
        results["ai_service"] = {"status": "ok" if ai_health else "error"}
    except Exception as e:
        logger.error(f"Erro no health check do serviço de IA: {str(e)}")
        results["ai_service"] = {"status": "error", "message": str(e)}
    
    # Status geral
    results["overall"] = {
        "status": "ok" if all(component["status"] == "ok" for component in results.values()) else "degraded"
    }
    
    return results


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Verifica se a aplicação está pronta para receber tráfego.",
)
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    Endpoint para verificar se a aplicação está pronta para receber tráfego.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Resposta com status de prontidão.
    """
    # Verificar se o container de DI está inicializado
    if not hasattr(request.app.state, "injector"):
        return {"status": "not_ready", "reason": "DI container not initialized"}
    
    # Verificar conectividade com o banco de dados
    try:
        database = request.app.state.injector.get(Database)
        db_health = await database.health_check()
        if not db_health:
            return {"status": "not_ready", "reason": "Database not available"}
    except Exception as e:
        logger.error(f"Erro no readiness check (database): {str(e)}")
        return {"status": "not_ready", "reason": f"Database error: {str(e)}"}
    
    return {"status": "ready"}


@router.get(
    "/version",
    status_code=status.HTTP_200_OK,
    summary="Versão da API",
    description="Retorna informações sobre a versão da API.",
)
async def version_info() -> Dict[str, Any]:
    """
    Endpoint para obter informações sobre a versão da API.
    
    Returns:
        Resposta com informações de versão.
    """
    # Informações sobre a versão (em um cenário real, viria de um arquivo de configuração)
    return {
        "version": "0.1.0",
        "name": "SaaS Multi-Nicho para Saúde e Bem-estar",
        "environment": "development",
    }
