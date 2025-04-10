"""
Entidade de Usuário (User) no domínio central.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4


class UserRole(str, Enum):
    """Papéis possíveis para um usuário."""
    
    ADMIN = "admin"              # Administrador (acesso total)
    MANAGER = "manager"          # Gerente (acesso a gestão)
    PROFESSIONAL = "professional"  # Profissional (acesso próprio)
    RECEPTIONIST = "receptionist"  # Recepcionista (agendamentos)
    CLIENT = "client"            # Cliente (acesso limitado)


class UserStatus(str, Enum):
    """Status possíveis para um usuário."""
    
    ACTIVE = "active"        # Usuário ativo
    INACTIVE = "inactive"    # Usuário inativo
    PENDING = "pending"      # Registro pendente
    BLOCKED = "blocked"      # Usuário bloqueado


@dataclass
class Permission:
    """Permissão específica no sistema."""
    
    resource: str
    action: str
    
    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"


@dataclass
class User:
    """
    Entidade de Usuário.
    
    Representa um usuário com acesso ao sistema.
    """
    
    email: str
    username: str
    hashed_password: str
    first_name: str
    last_name: Optional[str] = None
    roles: List[UserRole] = field(default_factory=list)
    permissions: List[Permission] = field(default_factory=list)
    status: UserStatus = UserStatus.ACTIVE
    last_login: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = field(default="")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def activate(self) -> None:
        """Ativa o usuário."""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Desativa o usuário."""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.now()
    
    def block(self) -> None:
        """Bloqueia o usuário."""
        self.status = UserStatus.BLOCKED
        self.updated_at = datetime.now()
    
    def add_role(self, role: UserRole) -> None:
        """
        Adiciona um papel ao usuário.
        
        Args:
            role: Papel a adicionar.
        """
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.now()
    
    def remove_role(self, role: UserRole) -> None:
        """
        Remove um papel do usuário.
        
        Args:
            role: Papel a remover.
        """
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.now()
    
    def add_permission(self, resource: str, action: str) -> None:
        """
        Adiciona uma permissão específica ao usuário.
        
        Args:
            resource: Recurso da permissão.
            action: Ação permitida.
        """
        permission = Permission(resource=resource, action=action)
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now()
    
    def remove_permission(self, resource: str, action: str) -> None:
        """
        Remove uma permissão específica do usuário.
        
        Args:
            resource: Recurso da permissão.
            action: Ação permitida.
        """
        permission = Permission(resource=resource, action=action)
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now()
    
    def update_last_login(self) -> None:
        """Atualiza o timestamp do último login."""
        self.last_login = datetime.now()
        self.updated_at = datetime.now()
    
    def set_password_reset_token(self, token: str, expires_in_hours: int = 24) -> None:
        """
        Define um token de redefinição de senha.
        
        Args:
            token: Token de redefinição.
            expires_in_hours: Horas até expiração.
        """
        self.password_reset_token = token
        self.password_reset_expires = datetime.now().replace(
            hour=datetime.now().hour + expires_in_hours
        )
        self.updated_at = datetime.now()
    
    def clear_password_reset_token(self) -> None:
        """Limpa o token de redefinição de senha."""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.updated_at = datetime.now()
    
    def is_password_reset_token_valid(self) -> bool:
        """
        Verifica se o token de redefinição de senha é válido.
        
        Returns:
            True se válido, False caso contrário.
        """
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        
        return datetime.now() < self.password_reset_expires
    
    def is_active(self) -> bool:
        """
        Verifica se o usuário está ativo.
        
        Returns:
            True se ativo, False caso contrário.
        """
        return self.status == UserStatus.ACTIVE
    
    def has_role(self, role: UserRole) -> bool:
        """
        Verifica se o usuário tem um papel específico.
        
        Args:
            role: Papel a verificar.
            
        Returns:
            True se tem o papel, False caso contrário.
        """
        return role in self.roles
    
    def has_permission(self, resource: str, action: str) -> bool:
        """
        Verifica se o usuário tem uma permissão específica.
        
        Args:
            resource: Recurso da permissão.
            action: Ação permitida.
            
        Returns:
            True se tem a permissão, False caso contrário.
        """
        # Admin tem todas as permissões
        if UserRole.ADMIN in self.roles:
            return True
        
        # Verifica permissão específica
        permission = Permission(resource=resource, action=action)
        return permission in self.permissions
    
    def full_name(self) -> str:
        """
        Obtém o nome completo do usuário.
        
        Returns:
            Nome completo formatado.
        """
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
