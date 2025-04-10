"""
Entidade de Profissional (Professional) no domínio central.
"""
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4


class ProfessionalStatus(str, Enum):
    """Status possíveis para um profissional."""
    
    ACTIVE = "active"        # Profissional ativo
    INACTIVE = "inactive"    # Profissional inativo
    ON_LEAVE = "on_leave"    # Profissional em licença temporária


@dataclass
class WorkingHours:
    """Horário de trabalho para um dia da semana."""
    
    day_of_week: int  # 0 = Segunda, 6 = Domingo
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None


@dataclass
class Speciality:
    """Especialidade de um profissional."""
    
    name: str
    description: Optional[str] = None
    id: UUID = field(default_factory=uuid4)


@dataclass
class TimeOff:
    """Período de folga ou indisponibilidade."""
    
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None  # Regra iCal para recorrência


@dataclass
class Professional:
    """
    Entidade de Profissional.
    
    Representa um profissional que presta serviços no sistema.
    """
    
    name: str
    email: str
    phone: Optional[str] = None
    specialities: List[Speciality] = field(default_factory=list)
    working_hours: List[WorkingHours] = field(default_factory=list)
    time_off: List[TimeOff] = field(default_factory=list)
    bio: Optional[str] = None
    status: ProfessionalStatus = ProfessionalStatus.ACTIVE
    custom_fields: Dict[str, any] = field(default_factory=dict)
    color: Optional[str] = None  # Cor para calendário
    id: UUID = field(default_factory=uuid4)
    user_id: Optional[UUID] = None  # Referência ao usuário de sistema
    tenant_id: str = field(default="")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def activate(self) -> None:
        """Ativa o profissional."""
        self.status = ProfessionalStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Desativa o profissional."""
        self.status = ProfessionalStatus.INACTIVE
        self.updated_at = datetime.now()
    
    def set_on_leave(self) -> None:
        """Marca o profissional como em licença."""
        self.status = ProfessionalStatus.ON_LEAVE
        self.updated_at = datetime.now()
    
    def add_speciality(self, speciality: Speciality) -> None:
        """
        Adiciona uma especialidade ao profissional.
        
        Args:
            speciality: Especialidade a adicionar.
        """
        self.specialities.append(speciality)
        self.updated_at = datetime.now()
    
    def add_working_hours(self, working_hours: WorkingHours) -> None:
        """
        Adiciona um horário de trabalho.
        
        Args:
            working_hours: Horário a adicionar.
        """
        self.working_hours.append(working_hours)
        self.updated_at = datetime.now()
    
    def add_time_off(self, time_off: TimeOff) -> None:
        """
        Adiciona um período de folga.
        
        Args:
            time_off: Período a adicionar.
        """
        self.time_off.append(time_off)
        self.updated_at = datetime.now()
    
    def update_custom_fields(self, fields: Dict[str, any]) -> None:
        """
        Atualiza campos customizados do profissional.
        
        Args:
            fields: Dicionário com campos a atualizar.
        """
        self.custom_fields.update(fields)
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """
        Verifica se o profissional está ativo.
        
        Returns:
            True se ativo, False caso contrário.
        """
        return self.status == ProfessionalStatus.ACTIVE
    
    def has_speciality(self, speciality_name: str) -> bool:
        """
        Verifica se o profissional tem uma especialidade.
        
        Args:
            speciality_name: Nome da especialidade.
            
        Returns:
            True se tem a especialidade, False caso contrário.
        """
        return any(s.name.lower() == speciality_name.lower() for s in self.specialities)
    
    def works_on_day(self, day_of_week: int) -> bool:
        """
        Verifica se o profissional trabalha em um dia da semana.
        
        Args:
            day_of_week: Dia da semana (0 = Segunda, 6 = Domingo).
            
        Returns:
            True se trabalha no dia, False caso contrário.
        """
        return any(wh.day_of_week == day_of_week for wh in self.working_hours)
    
    def get_working_hours_for_day(self, day_of_week: int) -> List[WorkingHours]:
        """
        Obtém os horários de trabalho para um dia da semana.
        
        Args:
            day_of_week: Dia da semana (0 = Segunda, 6 = Domingo).
            
        Returns:
            Lista de horários de trabalho para o dia.
        """
        return [wh for wh in self.working_hours if wh.day_of_week == day_of_week]
