"""
Entidade de Agendamento (Appointment) no domínio central.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List
from uuid import UUID, uuid4


class AppointmentStatus(str, Enum):
    """Status possíveis para um agendamento."""
    
    SCHEDULED = "scheduled"  # Agendado
    CONFIRMED = "confirmed"  # Confirmado pelo cliente
    CANCELED = "canceled"    # Cancelado
    COMPLETED = "completed"  # Concluído
    NO_SHOW = "no_show"      # Cliente não compareceu


@dataclass
class AppointmentNote:
    """Anotação em um agendamento."""
    
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[UUID] = None


@dataclass
class Appointment:
    """
    Entidade de Agendamento.
    
    Representa um horário agendado entre um cliente e um profissional.
    """
    
    client_id: UUID
    professional_id: UUID
    start_time: datetime
    end_time: datetime
    service_id: Optional[UUID] = None
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    notes: List[AppointmentNote] = field(default_factory=list)
    custom_fields: Dict[str, any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = field(default="")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def confirm(self) -> None:
        """Confirma o agendamento."""
        self.status = AppointmentStatus.CONFIRMED
        self.updated_at = datetime.now()
    
    def cancel(self) -> None:
        """Cancela o agendamento."""
        self.status = AppointmentStatus.CANCELED
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Marca o agendamento como concluído."""
        self.status = AppointmentStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def mark_no_show(self) -> None:
        """Marca o agendamento como não comparecido."""
        self.status = AppointmentStatus.NO_SHOW
        self.updated_at = datetime.now()
    
    def add_note(self, content: str, created_by: Optional[UUID] = None) -> None:
        """
        Adiciona uma nota ao agendamento.
        
        Args:
            content: Conteúdo da nota.
            created_by: ID do usuário que criou a nota (opcional).
        """
        note = AppointmentNote(content=content, created_by=created_by)
        self.notes.append(note)
        self.updated_at = datetime.now()
    
    def update_custom_fields(self, fields: Dict[str, any]) -> None:
        """
        Atualiza campos customizados do agendamento.
        
        Args:
            fields: Dicionário com campos a atualizar.
        """
        self.custom_fields.update(fields)
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """
        Verifica se o agendamento está ativo (não cancelado).
        
        Returns:
            True se ativo, False caso contrário.
        """
        return self.status not in [AppointmentStatus.CANCELED, AppointmentStatus.NO_SHOW]
    
    def is_upcoming(self) -> bool:
        """
        Verifica se o agendamento é futuro.
        
        Returns:
            True se futuro, False caso contrário.
        """
        return self.start_time > datetime.now()
    
    def duration_minutes(self) -> int:
        """
        Calcula a duração do agendamento em minutos.
        
        Returns:
            Duração em minutos.
        """
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
