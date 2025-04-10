"""
Adaptador para envio de mensagens WhatsApp via Twilio.
"""
import logging
from typing import Dict, List, Optional, Any

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.core.exceptions import MessagingError
from app.core.interfaces.message_provider import (
    IMessageProvider,
    MessageAttachment,
    MessageResponse,
    MessageTemplate,
)


logger = logging.getLogger(__name__)


class TwilioWhatsAppProvider:
    """
    Implementação de provedor de mensagens WhatsApp via Twilio.
    
    Usa a API da Twilio para enviar mensagens de WhatsApp.
    """
    
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        whatsapp_number: str,
    ):
        """
        Inicializa o provedor WhatsApp.
        
        Args:
            account_sid: SID da conta Twilio.
            auth_token: Token de autenticação Twilio.
            whatsapp_number: Número de WhatsApp configurado no Twilio.
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.whatsapp_number = whatsapp_number
        
        # Inicializar cliente Twilio
        self.client = Client(account_sid, auth_token)
        
        # Templates disponíveis (na versão completa, viria do banco/tenant)
        self._templates = {
            "appointment_confirmation": MessageTemplate(
                id="appointment_confirmation",
                content="Olá {{name}}, confirmamos seu agendamento de {{service}} com {{professional}} para {{date}} às {{time}}. Responda com SIM para confirmar.",
                variables=["name", "service", "professional", "date", "time"],
            ),
            "appointment_reminder": MessageTemplate(
                id="appointment_reminder",
                content="Olá {{name}}, lembrete do seu agendamento de {{service}} amanhã às {{time}}. Até lá!",
                variables=["name", "service", "time"],
            ),
            "welcome": MessageTemplate(
                id="welcome",
                content="Olá {{name}}, bem-vindo(a) à {{business}}! Estamos felizes em tê-lo(a) como cliente.",
                variables=["name", "business"],
            ),
        }
        
        logger.info(f"Provedor TwilioWhatsApp inicializado para o número {whatsapp_number}")
    
    async def send(
        self,
        to: str,
        template_id: str,
        params: Dict[str, Any],
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia mensagem WhatsApp usando um template.
        
        Args:
            to: Número do destinatário.
            template_id: ID do template a ser usado.
            params: Parâmetros para preenchimento do template.
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
            
        Raises:
            MessagingError: Se houver erro no envio.
        """
        try:
            # Obter template
            template = await self.get_template(template_id)
            if not template:
                raise MessagingError(f"Template {template_id} não encontrado")
            
            # Formatar mensagem com os parâmetros
            message_body = template.content
            for key, value in params.items():
                placeholder = "{{" + key + "}}"
                message_body = message_body.replace(placeholder, str(value))
            
            # Preparar número de destino no formato do Twilio
            to_formatted = self._format_phone_number(to)
            from_formatted = f"whatsapp:{self.whatsapp_number}"
            
            # Enviar mensagem
            media_urls = self._prepare_attachment_urls(attachments) if attachments else None
            
            message = self.client.messages.create(
                body=message_body,
                from_=from_formatted,
                to=to_formatted,
                media_url=media_urls,
            )
            
            logger.info(f"Mensagem WhatsApp enviada. SID: {message.sid}")
            
            return MessageResponse(
                success=True,
                message_id=message.sid,
                provider="twilio_whatsapp",
                channel="whatsapp",
            )
            
        except TwilioRestException as e:
            logger.error(f"Erro Twilio ao enviar WhatsApp: {str(e)}")
            return MessageResponse(
                success=False,
                provider="twilio_whatsapp",
                channel="whatsapp",
                error=f"Erro Twilio: {e.msg}",
            )
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
            return MessageResponse(
                success=False,
                provider="twilio_whatsapp",
                channel="whatsapp",
                error=str(e),
            )
    
    async def send_raw(
        self,
        to: str,
        content: str,
        subject: Optional[str] = None,  # Não usado para WhatsApp
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia mensagem WhatsApp direta sem template.
        
        Args:
            to: Número do destinatário.
            content: Conteúdo da mensagem.
            subject: Não usado para WhatsApp.
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
            
        Raises:
            MessagingError: Se houver erro no envio.
        """
        try:
            # Preparar número de destino no formato do Twilio
            to_formatted = self._format_phone_number(to)
            from_formatted = f"whatsapp:{self.whatsapp_number}"
            
            # Enviar mensagem
            media_urls = self._prepare_attachment_urls(attachments) if attachments else None
            
            message = self.client.messages.create(
                body=content,
                from_=from_formatted,
                to=to_formatted,
                media_url=media_urls,
            )
            
            logger.info(f"Mensagem direta WhatsApp enviada. SID: {message.sid}")
            
            return MessageResponse(
                success=True,
                message_id=message.sid,
                provider="twilio_whatsapp",
                channel="whatsapp",
            )
            
        except TwilioRestException as e:
            logger.error(f"Erro Twilio ao enviar WhatsApp direto: {str(e)}")
            return MessageResponse(
                success=False,
                provider="twilio_whatsapp",
                channel="whatsapp",
                error=f"Erro Twilio: {e.msg}",
            )
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp direto: {str(e)}")
            return MessageResponse(
                success=False,
                provider="twilio_whatsapp",
                channel="whatsapp",
                error=str(e),
            )
    
    async def get_template(self, template_id: str) -> Optional[MessageTemplate]:
        """
        Obtém um template por ID.
        
        Args:
            template_id: ID do template.
            
        Returns:
            O template encontrado ou None.
        """
        return self._templates.get(template_id)
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Formata um número de telefone para o formato esperado pelo Twilio.
        
        Args:
            phone: Número de telefone.
            
        Returns:
            Número formatado.
        """
        # Remover caracteres não numéricos
        clean_number = ''.join(filter(str.isdigit, phone))
        
        # Verificar se já tem código do país
        if not clean_number.startswith('55'):
            # Adicionar código do Brasil
            clean_number = '55' + clean_number
        
        # Formatar para WhatsApp
        return f"whatsapp:+{clean_number}"
    
    def _prepare_attachment_urls(self, attachments: List[MessageAttachment]) -> List[str]:
        """
        Prepara URLs de anexos para envio via Twilio.
        
        Args:
            attachments: Lista de anexos.
            
        Returns:
            Lista de URLs para os anexos.
        """
        urls = []
        for attachment in attachments:
            if attachment.url:
                urls.append(attachment.url)
            # Twilio não suporta anexos por conteúdo diretamente, seria necessário
            # fazer upload para um serviço de armazenamento e usar a URL
        
        return urls
