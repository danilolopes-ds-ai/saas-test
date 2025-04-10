"""
Interfaces para repositórios seguindo o princípio de Inversão de Dependência (SOLID).
Define contratos para acesso a dados de diferentes entidades.
"""
from typing import List, Optional, Protocol, TypeVar, Generic, Dict, Any
from uuid import UUID

from app.core.entities.appointment import Appointment
from app.core.entities.client import Client
from app.core.entities.professional import Professional
from app.core.entities.user import User


# Tipo genérico para entidades
T = TypeVar('T')


class IRepository(Protocol, Generic[T]):
    """Interface base para repositórios."""
    
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Cria uma nova entidade.
        
        Args:
            data: Dados para criar a entidade.
            
        Returns:
            A entidade criada.
        """
        ...
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Obtém uma entidade pelo ID.
        
        Args:
            entity_id: ID da entidade.
            
        Returns:
            A entidade encontrada ou None.
        """
        ...
    
    async def update(self, entity_id: UUID, data: Dict[str, Any]) -> Optional[T]:
        """
        Atualiza uma entidade.
        
        Args:
            entity_id: ID da entidade.
            data: Dados para atualizar.
            
        Returns:
            A entidade atualizada ou None.
        """
        ...
    
    async def delete(self, entity_id: UUID) -> bool:
        """
        Remove uma entidade.
        
        Args:
            entity_id: ID da entidade.
            
        Returns:
            True se removida com sucesso, False caso contrário.
        """
        ...
    
    async def list(self, filters: Dict[str, Any] = None, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Lista entidades com filtros.
        
        Args:
            filters: Filtros a serem aplicados.
            skip: Número de registros para pular.
            limit: Número máximo de registros para retornar.
            
        Returns:
            Lista de entidades.
        """
        ...


class IAppointmentRepository(IRepository[Appointment], Protocol):
    """Interface para repositório de agendamentos."""
    
    async def find_by_client(self, client_id: UUID) -> List[Appointment]:
        """
        Obtém agendamentos de um cliente.
        
        Args:
            client_id: ID do cliente.
            
        Returns:
            Lista de agendamentos do cliente.
        """
        ...
    
    async def find_by_professional(self, professional_id: UUID) -> List[Appointment]:
        """
        Obtém agendamentos de um profissional.
        
        Args:
            professional_id: ID do profissional.
            
        Returns:
            Lista de agendamentos do profissional.
        """
        ...
    
    async def find_by_date_range(self, start_date: str, end_date: str) -> List[Appointment]:
        """
        Obtém agendamentos em um intervalo de datas.
        
        Args:
            start_date: Data inicial (formato ISO).
            end_date: Data final (formato ISO).
            
        Returns:
            Lista de agendamentos no intervalo.
        """
        ...
    
    async def check_availability(self, professional_id: UUID, start_time: str, end_time: str) -> bool:
        """
        Verifica disponibilidade de um profissional em um horário.
        
        Args:
            professional_id: ID do profissional.
            start_time: Horário inicial (formato ISO).
            end_time: Horário final (formato ISO).
            
        Returns:
            True se disponível, False caso contrário.
        """
        ...


class IClientRepository(IRepository[Client], Protocol):
    """Interface para repositório de clientes."""
    
    async def find_by_phone(self, phone: str) -> Optional[Client]:
        """
        Obtém um cliente pelo telefone.
        
        Args:
            phone: Número de telefone.
            
        Returns:
            O cliente encontrado ou None.
        """
        ...
    
    async def find_by_email(self, email: str) -> Optional[Client]:
        """
        Obtém um cliente pelo email.
        
        Args:
            email: Email do cliente.
            
        Returns:
            O cliente encontrado ou None.
        """
        ...
    
    async def find_active(self) -> List[Client]:
        """
        Obtém clientes ativos.
        
        Returns:
            Lista de clientes ativos.
        """
        ...
    
    async def find_inactive(self, days: int = 30) -> List[Client]:
        """
        Obtém clientes inativos por um período.
        
        Args:
            days: Número de dias sem agendamento para considerar inativo.
            
        Returns:
            Lista de clientes inativos.
        """
        ...


class IProfessionalRepository(IRepository[Professional], Protocol):
    """Interface para repositório de profissionais."""
    
    async def find_available(self, start_time: str, end_time: str) -> List[Professional]:
        """
        Obtém profissionais disponíveis em um horário.
        
        Args:
            start_time: Horário inicial (formato ISO).
            end_time: Horário final (formato ISO).
            
        Returns:
            Lista de profissionais disponíveis.
        """
        ...
    
    async def find_by_speciality(self, speciality: str) -> List[Professional]:
        """
        Obtém profissionais por especialidade.
        
        Args:
            speciality: Especialidade.
            
        Returns:
            Lista de profissionais da especialidade.
        """
        ...


class IUserRepository(IRepository[User], Protocol):
    """Interface para repositório de usuários."""
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Obtém um usuário pelo email.
        
        Args:
            email: Email do usuário.
            
        Returns:
            O usuário encontrado ou None.
        """
        ...
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """
        Obtém um usuário pelo nome de usuário.
        
        Args:
            username: Nome de usuário.
            
        Returns:
            O usuário encontrado ou None.
        """
        ...
