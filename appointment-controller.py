"""
Controlador REST para gerenciamento de agendamentos.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field, validator

from app.api.dependencies import get_current_user, get_appointment_service
from app.core.entities.appointment import AppointmentStatus
from app.core.entities.user import User
from app.core.exceptions import (
    AppointmentError,
    ResourceNotFoundError,
    SlotUnavailableError,
)
from app.core.services.appointment_service import AppointmentService


logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models
class AppointmentBase(BaseModel):
    """Modelo base para agendamento."""
    
    client_id: UUID
    professional_id: UUID
    start_time: datetime
    end_time: datetime
    service_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Valida se o horário de término é após o início."""
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('O horário de término deve ser após o horário de início')
        return v


class AppointmentCreate(AppointmentBase):
    """Modelo para criação de agendamento."""
    pass


class AppointmentUpdate(BaseModel):
    """Modelo para atualização de agendamento."""
    
    professional_id: Optional[UUID] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    service_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    
    @validator('end_time')
    def end_time_after_start_time(cls, v, values):
        """Valida se o horário de término é após o início."""
        if v and 'start_time' in values and values['start_time'] and v <= values['start_time']:
            raise ValueError('O horário de término deve ser após o horário de início')
        return v


class AppointmentResponse(AppointmentBase):
    """Modelo para resposta de agendamento."""
    
    id: UUID
    status: AppointmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        """Configuração do modelo."""
        
        orm_mode = True


class AppointmentNote(BaseModel):
    """Modelo para nota em agendamento."""
    
    content: str


class AppointmentCancellation(BaseModel):
    """Modelo para cancelamento de agendamento."""
    
    reason: Optional[str] = None


@router.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar agendamento",
    description="Cria um novo agendamento.",
)
async def create_appointment(
    appointment: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Cria um novo agendamento.
    
    - **client_id**: ID do cliente
    - **professional_id**: ID do profissional
    - **start_time**: Horário de início
    - **end_time**: Horário de término
    - **service_id**: ID do serviço (opcional)
    - **title**: Título (opcional)
    - **description**: Descrição (opcional)
    - **location**: Local (opcional)
    - **custom_fields**: Campos customizados (opcional)
    """
    try:
        created = await appointment_service.create_appointment(
            client_id=appointment.client_id,
            professional_id=appointment.professional_id,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            service_id=appointment.service_id,
            title=appointment.title,
            description=appointment.description,
            location=appointment.location,
            custom_fields=appointment.custom_fields,
        )
        return created
    except SlotUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar agendamento",
        )


@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Obter agendamento",
    description="Obtém um agendamento pelo ID.",
)
async def get_appointment(
    appointment_id: UUID = Path(..., description="ID do agendamento"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Obtém um agendamento pelo ID.
    
    - **appointment_id**: ID do agendamento
    """
    try:
        appointment = await appointment_service.get_appointment(appointment_id)
        return appointment
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {appointment_id} não encontrado",
        )
    except Exception as e:
        logger.error(f"Erro ao obter agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter agendamento",
        )


@router.put(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Atualizar agendamento",
    description="Atualiza um agendamento existente.",
)
async def update_appointment(
    appointment: AppointmentUpdate,
    appointment_id: UUID = Path(..., description="ID do agendamento"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Atualiza um agendamento existente.
    
    - **appointment_id**: ID do agendamento
    - **appointment**: Dados para atualização
    """
    try:
        updated = await appointment_service.update_appointment(
            appointment_id=appointment_id,
            data=appointment.dict(exclude_unset=True),
        )
        return updated
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {appointment_id} não encontrado",
        )
    except SlotUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Erro ao atualizar agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar agendamento",
        )


@router.post(
    "/appointments/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    summary="Cancelar agendamento",
    description="Cancela um agendamento existente.",
)
async def cancel_appointment(
    cancellation: AppointmentCancellation,
    appointment_id: UUID = Path(..., description="ID do agendamento"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Cancela um agendamento existente.
    
    - **appointment_id**: ID do agendamento
    - **reason**: Motivo do cancelamento (opcional)
    """
    try:
        canceled = await appointment_service.cancel_appointment(
            appointment_id=appointment_id,
            cancellation_reason=cancellation.reason,
        )
        return canceled
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {appointment_id} não encontrado",
        )
    except AppointmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Erro ao cancelar agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao cancelar agendamento",
        )


@router.post(
    "/appointments/{appointment_id}/confirm",
    response_model=AppointmentResponse,
    summary="Confirmar agendamento",
    description="Confirma um agendamento existente.",
)
async def confirm_appointment(
    appointment_id: UUID = Path(..., description="ID do agendamento"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Confirma um agendamento existente.
    
    - **appointment_id**: ID do agendamento
    """
    try:
        confirmed = await appointment_service.confirm_appointment(
            appointment_id=appointment_id,
        )
        return confirmed
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {appointment_id} não encontrado",
        )
    except AppointmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Erro ao confirmar agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao confirmar agendamento",
        )


@router.post(
    "/appointments/{appointment_id}/complete",
    response_model=AppointmentResponse,
    summary="Concluir agendamento",
    description="Marca um agendamento como concluído.",
)
async def complete_appointment(
    note: Optional[AppointmentNote] = None,
    appointment_id: UUID = Path(..., description="ID do agendamento"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Marca um agendamento como concluído.
    
    - **appointment_id**: ID do agendamento
    - **note**: Nota sobre o atendimento (opcional)
    """
    try:
        completed = await appointment_service.complete_appointment(
            appointment_id=appointment_id,
            notes=note.content if note else None,
        )
        return completed
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {appointment_id} não encontrado",
        )
    except AppointmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Erro ao concluir agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao concluir agendamento",
        )


@router.post(
    "/appointments/{appointment_id}/no-show",
    response_model=AppointmentResponse,
    summary="Marcar não comparecimento",
    description="Marca um agendamento como não comparecido.",
)
async def mark_no_show(
    note: Optional[AppointmentNote] = None,
    appointment_id: UUID = Path(..., description="ID do agendamento"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Marca um agendamento como não comparecido.
    
    - **appointment_id**: ID do agendamento
    - **note**: Nota sobre o não comparecimento (opcional)
    """
    try:
        no_show = await appointment_service.mark_as_no_show(
            appointment_id=appointment_id,
            notes=note.content if note else None,
        )
        return no_show
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {appointment_id} não encontrado",
        )
    except AppointmentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Erro ao marcar não comparecimento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao marcar não comparecimento",
        )


@router.get(
    "/appointments",
    response_model=List[AppointmentResponse],
    summary="Listar agendamentos",
    description="Lista agendamentos com filtros opcionais.",
)
async def list_appointments(
    client_id: Optional[UUID] = Query(None, description="Filtrar por cliente"),
    professional_id: Optional[UUID] = Query(None, description="Filtrar por profissional"),
    status: Optional[List[AppointmentStatus]] = Query(None, description="Filtrar por status"),
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Lista agendamentos com filtros opcionais.
    
    - **client_id**: Filtrar por cliente (opcional)
    - **professional_id**: Filtrar por profissional (opcional)
    - **status**: Filtrar por status (opcional)
    - **start_date**: Data inicial (opcional)
    - **end_date**: Data final (opcional)
    """
    try:
        # Se não informou data final, usar data inicial + 7 dias ou hoje + 7 dias
        if start_date and not end_date:
            end_date = start_date + timedelta(days=7)
        elif not start_date and not end_date:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
        
        # Buscar por cliente
        if client_id:
            appointments = await appointment_service.get_appointments_by_client(
                client_id=client_id,
                status=status,
                start_date=start_date,
                end_date=end_date,
            )
        # Buscar por profissional
        elif professional_id:
            appointments = await appointment_service.get_appointments_by_professional(
                professional_id=professional_id,
                status=status,
                start_date=start_date,
                end_date=end_date,
            )
        # Buscar por intervalo de datas
        else:
            appointments = await appointment_service.get_appointments_by_date_range(
                start_date=start_date,
                end_date=end_date,
                status=status,
            )
        
        return appointments
    except Exception as e:
        logger.error(f"Erro ao listar agendamentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar agendamentos",
        )


@router.get(
    "/appointments/client/{client_id}",
    response_model=List[AppointmentResponse],
    summary="Listar agendamentos por cliente",
    description="Lista agendamentos de um cliente específico.",
)
async def list_client_appointments(
    client_id: UUID = Path(..., description="ID do cliente"),
    status: Optional[List[AppointmentStatus]] = Query(None, description="Filtrar por status"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Lista agendamentos de um cliente específico.
    
    - **client_id**: ID do cliente
    - **status**: Filtrar por status (opcional)
    """
    try:
        appointments = await appointment_service.get_appointments_by_client(
            client_id=client_id,
            status=status,
        )
        return appointments
    except Exception as e:
        logger.error(f"Erro ao listar agendamentos do cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar agendamentos do cliente",
        )


@router.get(
    "/appointments/professional/{professional_id}",
    response_model=List[AppointmentResponse],
    summary="Listar agendamentos por profissional",
    description="Lista agendamentos de um profissional específico.",
)
async def list_professional_appointments(
    professional_id: UUID = Path(..., description="ID do profissional"),
    status: Optional[List[AppointmentStatus]] = Query(None, description="Filtrar por status"),
    start_date: Optional[datetime] = Query(None, description="Data inicial"),
    end_date: Optional[datetime] = Query(None, description="Data final"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Lista agendamentos de um profissional específico.
    
    - **professional_id**: ID do profissional
    - **status**: Filtrar por status (opcional)
    - **start_date**: Data inicial (opcional)
    - **end_date**: Data final (opcional)
    """
    try:
        # Se não informou data final, usar data inicial + 7 dias ou hoje + 7 dias
        if start_date and not end_date:
            end_date = start_date + timedelta(days=7)
        elif not start_date and not end_date:
            start_date = datetime.now()
            end_date = start_date + timedelta(days=7)
        
        appointments = await appointment_service.get_appointments_by_professional(
            professional_id=professional_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )
        return appointments
    except Exception as e:
        logger.error(f"Erro ao listar agendamentos do profissional: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar agendamentos do profissional",
        )


@router.post(
    "/appointments/{appointment_id}/note",
    response_model=AppointmentResponse,
    summary="Adicionar nota ao agendamento",
    description="Adiciona uma nota a um agendamento existente.",
)
async def add_appointment_note(
    note: AppointmentNote,
    appointment_id: UUID = Path(..., description="ID do agendamento"),
    current_user: User = Depends(get_current_user),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Adiciona uma nota a um agendamento existente.
    
    - **appointment_id**: ID do agendamento
    - **note**: Nota a ser adicionada
    """
    try:
        # Primeiro, obter o agendamento
        appointment = await appointment_service.get_appointment(appointment_id)
        
        # Criar lista de notas se não existir
        notes = list(appointment.notes) if appointment.notes else []
        
        # Adicionar nova nota
        notes.append({
            'content': note.content,
            'created_at': datetime.now().isoformat(),
            'created_by': str(current_user.id),
        })
        
        # Atualizar agendamento
        updated = await appointment_service.update_appointment(
            appointment_id=appointment_id,
            data={'notes': notes},
        )
        
        return updated
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agendamento {appointment_id} não encontrado",
        )
    except Exception as e:
        logger.error(f"Erro ao adicionar nota ao agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao adicionar nota ao agendamento",
        )
