"""
Dependências para os endpoints da API.
Implementa funções para injeção de dependência com FastAPI.
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.entities.user import User, UserRole
from app.core.exceptions import AuthError, TenantNotSetError
from app.core.services.appointment_service import AppointmentService
from app.core.services.faq_service import FAQService
from app.core.services.message_service import MessageService
from app.core.services.tenant_context import TenantContext
from app.core.services.user_service import UserService


logger = logging.getLogger(__name__)

# OAuth2 scheme para autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# Dependência para obter usuário atual
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    request: Request = None,
    user_service: UserService = None,
) -> User:
    """
    Dependência para obter o usuário atual através do token JWT.
    
    Args:
        token: Token de acesso JWT.
        request: Requisição HTTP (injetada pelo FastAPI).
        user_service: Serviço de usuário (injetado via di_container).
        
    Returns:
        Usuário autenticado.
        
    Raises:
        HTTPException: Se o token for inválido ou usuário não encontrado.
    """
    try:
        # Obter o serviço via DI container se não for injetado diretamente
        if not user_service and request:
            user_service = request.app.state.injector.get(UserService)
        
        # Decodificar token e obter usuário
        user = await user_service.get_user_from_token(token)
        
        if not user:
            raise AuthError("Usuário não encontrado")
        
        # Verificar se o usuário está ativo
        if not user.is_active():
            raise AuthError("Usuário inativo")
        
        return user
    except AuthError as e:
        logger.warning(f"Falha na autenticação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro na autenticação",
        )


# Dependência para verificar papéis do usuário
def check_role(allowed_roles: list[UserRole]):
    """
    Factory de dependência para verificar papéis do usuário.
    
    Args:
        allowed_roles: Lista de papéis permitidos.
        
    Returns:
        Função de dependência.
    """
    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        """
        Verifica se o usuário tem um dos papéis permitidos.
        
        Args:
            current_user: Usuário atual.
            
        Returns:
            Usuário se tiver acesso.
            
        Raises:
            HTTPException: Se o usuário não tiver permissão.
        """
        # Administradores têm acesso a tudo
        if UserRole.ADMIN in current_user.roles:
            return current_user
            
        # Verificar papel do usuário
        for role in current_user.roles:
            if role in allowed_roles:
                return current_user
                
        logger.warning(f"Acesso negado para usuário {current_user.id}. Necessário: {allowed_roles}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este recurso",
        )
    
    return _check_role


# Dependência para obter o contexto de tenant
async def get_tenant_context(request: Request) -> TenantContext:
    """
    Dependência para obter o contexto de tenant.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Contexto de tenant.
    """
    return request.app.state.injector.get(TenantContext)


# Dependência para obter o tenant_id atual
async def get_current_tenant_id(tenant_context: TenantContext = Depends(get_tenant_context)) -> str:
    """
    Dependência para obter o tenant_id atual.
    
    Args:
        tenant_context: Contexto de tenant.
        
    Returns:
        ID do tenant atual.
        
    Raises:
        HTTPException: Se o tenant não estiver configurado.
    """
    try:
        return tenant_context.tenant_id
    except TenantNotSetError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant não configurado para esta requisição",
        )


# Dependência para obter o serviço de agendamentos
async def get_appointment_service(request: Request) -> AppointmentService:
    """
    Dependência para obter o serviço de agendamentos.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Serviço de agendamentos.
    """
    return request.app.state.injector.get(AppointmentService)


# Dependência para obter o serviço de mensagens
async def get_message_service(request: Request) -> MessageService:
    """
    Dependência para obter o serviço de mensagens.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Serviço de mensagens.
    """
    return request.app.state.injector.get(MessageService)


# Dependência para obter o serviço de FAQ
async def get_faq_service(request: Request) -> FAQService:
    """
    Dependência para obter o serviço de FAQ.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Serviço de FAQ.
    """
    return request.app.state.injector.get(FAQService)
