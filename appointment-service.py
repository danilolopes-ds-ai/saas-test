"""
Serviço para gerenciamento de agendamentos.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.core.entities.appointment import Appointment, AppointmentStatus
from app.core.exceptions import (
    AppointmentError,
    ConflictingAppointmentError,
    ResourceNotFoundError,
    SlotUnavailableError,
)
from app.core.interfaces.repositories import IAppointmentRepository
from app.core.services.message_service import MessageService
from app.core.services.tenant_context import TenantContext


logger = logging.getLogger(__name__)


class AppointmentService:
    """
    Serviço para gerenciamento de agendamentos.
    
    Implementa a lógica de negócio relacionada a agendamentos,
    incluindo criação, atualização, cancelamento, e verificação
    de disponibilidade.
    """
    
    def __init__(
        self,
        repository: IAppointmentRepository,
        message_service: MessageService,
        tenant_context: TenantContext,
    ):
        """
        Inicializa o serviço de agendamentos.
        
        Args:
            repository: Repositório de agendamentos.
            message_service: Serviço de mensagens.
            tenant_context: Contexto de tenant.
        """
        self.repository = repository
        self.message_service = message_service
        self.tenant_context = tenant_context
        
        logger.info("Serviço de agendamentos inicializado")
    
    async def create_appointment(
        self,
        client_id: UUID,
        professional_id: UUID,
        start_time: datetime,
        end_time: datetime,
        service_id: Optional[UUID] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Appointment:
        """
        Cria um novo agendamento.
        
        Args:
            client_id: ID do cliente.
            professional_id: ID do profissional.
            start_time: Horário de início.
            end_time: Horário de término.
            service_id: ID do serviço (opcional).
            title: Título do agendamento (opcional).
            description: Descrição (opcional).
            location: Local (opcional).
            custom_fields: Campos customizados (opcional).
            
        Returns:
            O agendamento criado.
            
        Raises:
            ConflictingAppointmentError: Se há conflito com outro agendamento.
            SlotUnavailableError: Se o horário não está disponível.
        """
        # Verificar disponibilidade do horário
        is_available = await self.repository.check_availability(
            professional_id=professional_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )
        
        if not is_available:
            raise SlotUnavailableError("O horário selecionado não está disponível")
        
        # Criar agendamento
        tenant_id = self.tenant_context.tenant_id
        
        appointment = Appointment(
            client_id=client_id,
            professional_id=professional_id,
            start_time=start_time,
            end_time=end_time,
            service_id=service_id,
            title=title,
            description=description,
            location=location,
            custom_fields=custom_fields or {},
            tenant_id=tenant_id,
        )
        
        # Persistir no repositório
        created_appointment = await self.repository.create(appointment.__dict__)
        
        # Enviar notificação
        await self._notify_appointment_created(created_appointment)
        
        logger.info(f"Agendamento criado: {created_appointment.id}")
        return created_appointment
    
    async def get_appointment(self, appointment_id: UUID) -> Appointment:
        """
        Obtém um agendamento pelo ID.
        
        Args:
            appointment_id: ID do agendamento.
            
        Returns:
            O agendamento encontrado.
            
        Raises:
            ResourceNotFoundError: Se o agendamento não for encontrado.
        """
        appointment = await self.repository.get_by_id(appointment_id)
        
        if not appointment:
            raise ResourceNotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        return appointment
    
    async def update_appointment(
        self,
        appointment_id: UUID,
        data: Dict[str, Any],
    ) -> Appointment:
        """
        Atualiza um agendamento.
        
        Args:
            appointment_id: ID do agendamento.
            data: Dados para atualização.
            
        Returns:
            O agendamento atualizado.
            
        Raises:
            ResourceNotFoundError: Se o agendamento não for encontrado.
            ConflictingAppointmentError: Se a mudança gera conflito.
        """
        # Verificar se o agendamento existe
        appointment = await self.repository.get_by_id(appointment_id)
        
        if not appointment:
            raise ResourceNotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar se está alterando data/hora e profissional
        if ('start_time' in data or 'end_time' in data) and appointment.status != AppointmentStatus.CANCELED:
            # Preparar horários para verificação
            new_start = data.get('start_time', appointment.start_time)
            new_end = data.get('end_time', appointment.end_time)
            
            # Se forem strings, converter para datetime
            if isinstance(new_start, str):
                new_start = datetime.fromisoformat(new_start)
            if isinstance(new_end, str):
                new_end = datetime.fromisoformat(new_end)
            
            # Verificar disponibilidade
            professional_id = data.get('professional_id', appointment.professional_id)
            
            is_available = await self.repository.check_availability(
                professional_id=professional_id,
                start_time=new_start.isoformat(),
                end_time=new_end.isoformat(),
                exclude_appointment_id=appointment_id,
            )
            
            if not is_available:
                raise SlotUnavailableError("O novo horário selecionado não está disponível")
        
        # Atualizar agendamento
        data['updated_at'] = datetime.now()
        updated_appointment = await self.repository.update(appointment_id, data)
        
        # Enviar notificação se houve mudança relevante
        if ('start_time' in data or 'end_time' in data or 
            'professional_id' in data or 'status' in data):
            await self._notify_appointment_updated(updated_appointment)
        
        logger.info(f"Agendamento atualizado: {appointment_id}")
        return updated_appointment
    
    async def cancel_appointment(
        self,
        appointment_id: UUID,
        cancellation_reason: Optional[str] = None,
    ) -> Appointment:
        """
        Cancela um agendamento.
        
        Args:
            appointment_id: ID do agendamento.
            cancellation_reason: Motivo do cancelamento (opcional).
            
        Returns:
            O agendamento cancelado.
            
        Raises:
            ResourceNotFoundError: Se o agendamento não for encontrado.
            AppointmentError: Se o agendamento já estiver cancelado.
        """
        # Verificar se o agendamento existe
        appointment = await self.repository.get_by_id(appointment_id)
        
        if not appointment:
            raise ResourceNotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar se já está cancelado
        if appointment.status == AppointmentStatus.CANCELED:
            raise AppointmentError("O agendamento já está cancelado")
        
        # Cancelar agendamento
        data = {
            'status': AppointmentStatus.CANCELED,
            'updated_at': datetime.now(),
        }
        
        if cancellation_reason:
            # Adicionar nota com motivo do cancelamento
            note = {
                'content': f"Cancelamento: {cancellation_reason}",
                'created_at': datetime.now().isoformat(),
            }
            if appointment.notes:
                notes = list(appointment.notes)
                notes.append(note)
                data['notes'] = notes
            else:
                data['notes'] = [note]
        
        canceled_appointment = await self.repository.update(appointment_id, data)
        
        # Enviar notificação
        await self._notify_appointment_canceled(canceled_appointment, cancellation_reason)
        
        logger.info(f"Agendamento cancelado: {appointment_id}")
        return canceled_appointment
    
    async def confirm_appointment(self, appointment_id: UUID) -> Appointment:
        """
        Confirma um agendamento.
        
        Args:
            appointment_id: ID do agendamento.
            
        Returns:
            O agendamento confirmado.
            
        Raises:
            ResourceNotFoundError: Se o agendamento não for encontrado.
            AppointmentError: Se o agendamento já estiver confirmado ou cancelado.
        """
        # Verificar se o agendamento existe
        appointment = await self.repository.get_by_id(appointment_id)
        
        if not appointment:
            raise ResourceNotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar status atual
        if appointment.status == AppointmentStatus.CONFIRMED:
            raise AppointmentError("O agendamento já está confirmado")
        
        if appointment.status == AppointmentStatus.CANCELED:
            raise AppointmentError("Não é possível confirmar um agendamento cancelado")
        
        # Confirmar agendamento
        data = {
            'status': AppointmentStatus.CONFIRMED,
            'updated_at': datetime.now(),
        }
        
        confirmed_appointment = await self.repository.update(appointment_id, data)
        
        # Enviar notificação
        await self._notify_appointment_confirmed(confirmed_appointment)
        
        logger.info(f"Agendamento confirmado: {appointment_id}")
        return confirmed_appointment
    
    async def complete_appointment(self, appointment_id: UUID, notes: Optional[str] = None) -> Appointment:
        """
        Marca um agendamento como concluído.
        
        Args:
            appointment_id: ID do agendamento.
            notes: Anotações sobre o atendimento (opcional).
            
        Returns:
            O agendamento concluído.
            
        Raises:
            ResourceNotFoundError: Se o agendamento não for encontrado.
            AppointmentError: Se o agendamento estiver cancelado.
        """
        # Verificar se o agendamento existe
        appointment = await self.repository.get_by_id(appointment_id)
        
        if not appointment:
            raise ResourceNotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar status atual
        if appointment.status == AppointmentStatus.CANCELED:
            raise AppointmentError("Não é possível completar um agendamento cancelado")
        
        # Marcar como concluído
        data = {
            'status': AppointmentStatus.COMPLETED,
            'updated_at': datetime.now(),
        }
        
        if notes:
            # Adicionar nota sobre o atendimento
            note = {
                'content': notes,
                'created_at': datetime.now().isoformat(),
            }
            if appointment.notes:
                notes_list = list(appointment.notes)
                notes_list.append(note)
                data['notes'] = notes_list
            else:
                data['notes'] = [note]
        
        completed_appointment = await self.repository.update(appointment_id, data)
        
        logger.info(f"Agendamento completado: {appointment_id}")
        return completed_appointment
    
    async def mark_as_no_show(self, appointment_id: UUID, notes: Optional[str] = None) -> Appointment:
        """
        Marca um agendamento como não comparecido.
        
        Args:
            appointment_id: ID do agendamento.
            notes: Anotações sobre o não comparecimento (opcional).
            
        Returns:
            O agendamento atualizado.
            
        Raises:
            ResourceNotFoundError: Se o agendamento não for encontrado.
            AppointmentError: Se o agendamento estiver cancelado.
        """
        # Verificar se o agendamento existe
        appointment = await self.repository.get_by_id(appointment_id)
        
        if not appointment:
            raise ResourceNotFoundError(f"Agendamento {appointment_id} não encontrado")
        
        # Verificar status atual
        if appointment.status == AppointmentStatus.CANCELED:
            raise AppointmentError("Não é possível marcar como não comparecido um agendamento cancelado")
        
        # Marcar como não comparecido
        data = {
            'status': AppointmentStatus.NO_SHOW,
            'updated_at': datetime.now(),
        }
        
        if notes:
            # Adicionar nota sobre o não comparecimento
            note = {
                'content': f"Não compareceu: {notes}",
                'created_at': datetime.now().isoformat(),
            }
            if appointment.notes:
                notes_list = list(appointment.notes)
                notes_list.append(note)
                data['notes'] = notes_list
            else:
                data['notes'] = [note]
        
        no_show_appointment = await self.repository.update(appointment_id, data)
        
        # Enviar notificação
        await self._notify_appointment_no_show(no_show_appointment)
        
        logger.info(f"Agendamento marcado como não comparecido: {appointment_id}")
        return no_show_appointment
    
    async def get_appointments_by_client(
        self,
        client_id: UUID,
        status: Optional[List[AppointmentStatus]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Appointment]:
        """
        Obtém agendamentos de um cliente.
        
        Args:
            client_id: ID do cliente.
            status: Lista de status para filtrar (opcional).
            start_date: Data inicial (opcional).
            end_date: Data final (opcional).
            
        Returns:
            Lista de agendamentos do cliente.
        """
        filters = {"client_id": client_id}
        
        if status:
            filters["status"] = status
        
        if start_date and end_date:
            appointments = await self.repository.find_by_date_range(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
            
            # Filtrar por cliente
            return [a for a in appointments if str(a.client_id) == str(client_id)]
        else:
            return await self.repository.find_by_client(client_id)
    
    async def get_appointments_by_professional(
        self,
        professional_id: UUID,
        status: Optional[List[AppointmentStatus]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Appointment]:
        """
        Obtém agendamentos de um profissional.
        
        Args:
            professional_id: ID do profissional.
            status: Lista de status para filtrar (opcional).
            start_date: Data inicial (opcional).
            end_date: Data final (opcional).
            
        Returns:
            Lista de agendamentos do profissional.
        """
        filters = {"professional_id": professional_id}
        
        if status:
            filters["status"] = status
        
        if start_date and end_date:
            appointments = await self.repository.find_by_date_range(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
            
            # Filtrar por profissional
            return [a for a in appointments if str(a.professional_id) == str(professional_id)]
        else:
            return await self.repository.find_by_professional(professional_id)
    
    async def get_appointments_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[List[AppointmentStatus]] = None,
    ) -> List[Appointment]:
        """
        Obtém agendamentos em um intervalo de datas.
        
        Args:
            start_date: Data inicial.
            end_date: Data final.
            status: Lista de status para filtrar (opcional).
            
        Returns:
            Lista de agendamentos no intervalo.
        """
        appointments = await self.repository.find_by_date_range(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        
        # Filtrar por status
        if status:
            return [a for a in appointments if a.status in status]
        
        return appointments
    
    async def _notify_appointment_created(self, appointment: Appointment) -> None:
        """
        Envia notificação de criação de agendamento.
        
        Args:
            appointment: Agendamento criado.
        """
        try:
            # Obter dados para notificação
            # Na implementação real, buscaria detalhes do cliente e profissional
            params = {
                "nome": "Cliente",  # placeholder
                "modalidade": appointment.custom_fields.get("modalidade", "Sessão"),
                "data": appointment.start_time.strftime("%d/%m/%Y"),
                "hora": appointment.start_time.strftime("%H:%M"),
            }
            
            # Enviar WhatsApp
            await self.message_service.send_message(
                channel="whatsapp",
                to="5511999999999",  # placeholder
                template_id="confirmacao_aula",
                params=params,
            )
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de agendamento criado: {str(e)}")
    
    async def _notify_appointment_updated(self, appointment: Appointment) -> None:
        """
        Envia notificação de atualização de agendamento.
        
        Args:
            appointment: Agendamento atualizado.
        """
        try:
            # Implementação similar à notificação de criação
            pass
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de agendamento atualizado: {str(e)}")
    
    async def _notify_appointment_canceled(
        self,
        appointment: Appointment,
        reason: Optional[str] = None,
    ) -> None:
        """
        Envia notificação de cancelamento de agendamento.
        
        Args:
            appointment: Agendamento cancelado.
            reason: Motivo do cancelamento (opcional).
        """
        try:
            # Implementação similar à notificação de criação
            pass
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de agendamento cancelado: {str(e)}")
    
    async def _notify_appointment_confirmed(self, appointment: Appointment) -> None:
        """
        Envia notificação de confirmação de agendamento.
        
        Args:
            appointment: Agendamento confirmado.
        """
        try:
            # Implementação similar à notificação de criação
            pass
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de agendamento confirmado: {str(e)}")
    
    async def _notify_appointment_no_show(self, appointment: Appointment) -> None:
        """
        Envia notificação de não comparecimento.
        
        Args:
            appointment: Agendamento não comparecido.
        """
        try:
            # Implementação similar à notificação de criação
            pass
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de não comparecimento: {str(e)}")
