"""
Entidade de Cliente (Client) no domínio central.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class ClientStatus(str, Enum):
    """Status possíveis para um cliente."""
    
    ACTIVE = "active"        # Cliente ativo
    INACTIVE = "inactive"    # Cliente inativo
    LEAD = "lead"            # Potencial cliente (não convertido)
    BLOCKED = "blocked"      # Cliente bloqueado


@dataclass
class Address:
    """Endereço de um cliente."""
    
    street: str
    number: str
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "Brasil"


@dataclass
class ClientNote:
    """Anotação em um cliente."""
    
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[UUID] = None


@dataclass
class Client:
    """
    Entidade de Cliente.
    
    Representa um cliente ou potencial cliente no sistema.
    """
    
    name: str
    phone: str
    email: Optional[str] = None
    status: ClientStatus = ClientStatus.ACTIVE
    birth_date: Optional[datetime] = None
    address: Optional[Address] = None
    notes: List[ClientNote] = field(default_factory=list)
    custom_fields: Dict[str, any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = field(default="")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    last_appointment: Optional[datetime] = None
    
    def activate(self) -> None:
        """Ativa o cliente."""
        self.status = ClientStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Desativa o cliente."""
        self.status = ClientStatus.INACTIVE
        self.updated_at = datetime.now()
    
    def mark_as_lead(self) -> None:
        """Marca o cliente como lead."""
        self.status = ClientStatus.LEAD
        self.updated_at = datetime.now()
    
    def block(self) -> None:
        """Bloqueia o cliente."""
        self.status = ClientStatus.BLOCKED
        self.updated_at = datetime.now()
    
    def add_note(self, content: str, created_by: Optional[UUID] = None) -> None:
        """
        Adiciona uma nota ao cliente.
        
        Args:
            content: Conteúdo da nota.
            created_by: ID do usuário que criou a nota (opcional).
        """
        note = ClientNote(content=content, created_by=created_by)
        self.notes.append(note)
        self.updated_at = datetime.now()
    
    def update_custom_fields(self, fields: Dict[str, any]) -> None:
        """
        Atualiza campos customizados do cliente.
        
        Args:
            fields: Dicionário com campos a atualizar.
        """
        self.custom_fields.update(fields)
        self.updated_at = datetime.now()
    
    def update_address(self, address: Address) -> None:
        """
        Atualiza o endereço do cliente.
        
        Args:
            address: Novo endereço.
        """
        self.address = address
        self.updated_at = datetime.now()
    
    def update_last_appointment(self, appointment_date: datetime) -> None:
        """
        Atualiza a data do último agendamento.
        
        Args:
            appointment_date: Data do último agendamento.
        """
        self.last_appointment = appointment_date
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """
        Verifica se o cliente está ativo.
        
        Returns:
            True se ativo, False caso contrário.
        """
        return self.status == ClientStatus.ACTIVE
    
    def is_lead(self) -> bool:
        """
        Verifica se o cliente é um lead.
        
        Returns:
            True se lead, False caso contrário.
        """
        return self.status == ClientStatus.LEAD
    
    def days_since_last_appointment(self) -> Optional[int]:
        """
        Calcula dias desde o último agendamento.
        
        Returns:
            Número de dias ou None se nunca teve agendamento.
        """
        if not self.last_appointment:
            return None
        
        delta = datetime.now() - self.last_appointment
        return delta.days
