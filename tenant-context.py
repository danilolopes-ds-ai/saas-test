"""
Implementação do contexto de tenant para suporte a multi-tenancy.
"""
from contextvars import ContextVar
from typing import Optional

from app.core.exceptions import TenantNotSetError


class TenantContext:
    """
    Contexto de tenant para gerenciar o ID do tenant atual.
    
    Usa ContextVar para garantir isolamento em ambiente assíncrono
    mesmo com múltiplas requisições concorrentes.
    """
    
    def __init__(self, default_tenant_id: Optional[str] = None):
        """
        Inicializa o contexto de tenant.
        
        Args:
            default_tenant_id: ID de tenant padrão (opcional, para desenvolvimento)
        """
        # ContextVar para armazenar o tenant_id da requisição atual
        self._tenant_id_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=default_tenant_id)
    
    @property
    def tenant_id(self) -> str:
        """
        Obtém o ID do tenant atual.
        
        Returns:
            str: ID do tenant atual.
            
        Raises:
            TenantNotSetError: Se o ID do tenant não estiver definido e não houver padrão.
        """
        tenant_id = self._tenant_id_var.get()
        if tenant_id is None:
            raise TenantNotSetError("ID do tenant não está configurado no contexto atual")
        return tenant_id
    
    def set_tenant_id(self, tenant_id: str) -> None:
        """
        Define o ID do tenant para o contexto atual.
        
        Args:
            tenant_id: ID do tenant a ser definido.
        """
        self._tenant_id_var.set(tenant_id)
    
    def reset(self) -> None:
        """
        Redefine o ID do tenant para o valor padrão (útil para testes).
        """
        self._tenant_id_var.set(None)
    
    def __str__(self) -> str:
        """Representação em string do contexto."""
        try:
            return f"TenantContext(tenant_id={self.tenant_id})"
        except TenantNotSetError:
            return "TenantContext(tenant_id=None)"
