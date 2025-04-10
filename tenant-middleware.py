"""
Middleware para gerenciar contexto de tenant nas requisições.
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import TenantNotFoundError
from app.core.services.tenant_context import TenantContext


logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware para configurar contexto de tenant para cada requisição.
    
    Extrai o ID do tenant da requisição e o configura no contexto da aplicação.
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Processa a requisição, extraindo e configurando o tenant_id.
        
        Args:
            request: Requisição HTTP.
            call_next: Próxima middleware ou endpoint.
            
        Returns:
            Resposta HTTP.
        """
        # Tentar extrair tenant_id da requisição
        tenant_id = self._extract_tenant_id(request)
        
        # Obter o contexto de tenant da aplicação
        tenant_context = request.app.state.injector.get(TenantContext)
        
        # Configurar tenant_id no contexto
        tenant_context.set_tenant_id(tenant_id)
        
        # Armazenar tenant_id no estado da requisição para uso em dependências
        request.state.tenant_id = tenant_id
        
        # Processar a requisição
        try:
            logger.debug(f"Requisição para tenant_id: {tenant_id}")
            response = await call_next(request)
            return response
        finally:
            # Limpar contexto após a requisição (opcional dependendo da implementação)
            # tenant_context.reset()
            pass
    
    def _extract_tenant_id(self, request: Request) -> str:
        """
        Extrai o ID do tenant da requisição.
        
        Na versão MVP, retorna o tenant fixo configurado.
        Na versão multi-tenant completa, extrai de:
        - Subdomain
        - Header
        - JWT token
        - Query parameter
        
        Args:
            request: Requisição HTTP.
            
        Returns:
            ID do tenant.
            
        Raises:
            TenantNotFoundError: Se o tenant não for encontrado.
        """
        # MVP: Retornar tenant fixo
        if not settings.MULTI_TENANT_ENABLED:
            return settings.DEFAULT_TENANT_ID
            
        # Multi-tenant: Extrair de diferentes fontes
        tenant_id = None
        
        # 1. Verificar header específico
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
            
        # 2. Extrair de subdomain
        host = request.headers.get("host", "")
        if "." in host and not host.startswith("www."):
            subdomain = host.split(".")[0]
            # Aqui poderia ter uma lógica para mapear subdomain para tenant_id
            tenant_id = subdomain
            
        # 3. Extrair de Authorization token (JWT)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # Aqui poderia ter uma lógica para extrair tenant_id do token
            # tenant_id = decode_jwt(token).get("tenant_id")
            
        # 4. Verificar query parameter
        tenant_id_param = request.query_params.get("tenant_id")
        if tenant_id_param:
            tenant_id = tenant_id_param
            
        # Se não encontrou em nenhum lugar, usar o padrão
        if not tenant_id:
            if settings.DEFAULT_TENANT_ID:
                tenant_id = settings.DEFAULT_TENANT_ID
            else:
                raise TenantNotFoundError("ID do tenant não encontrado na requisição")
                
        return tenant_id


# Dependency para obter o tenant_id da requisição atual
async def get_tenant_id(request: Request) -> str:
    """
    Dependency para obter o tenant_id da requisição atual.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        ID do tenant.
        
    Raises:
        TenantNotFoundError: Se o tenant não estiver configurado.
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise TenantNotFoundError("ID do tenant não está configurado para esta requisição")
    return tenant_id


# Dependency para obter o contexto de tenant
async def get_tenant_context(request: Request) -> TenantContext:
    """
    Dependency para obter o contexto de tenant.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Contexto de tenant.
    """
    return request.app.state.injector.get(TenantContext)
