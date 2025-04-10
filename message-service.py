"""
Serviço para envio de mensagens através de diferentes canais.
"""
import logging
from typing import Dict, List, Optional, Any

from app.adapters.messaging.message_provider_factory import MessageProviderFactory
from app.core.exceptions import MessagingError
from app.core.interfaces.message_provider import MessageAttachment, MessageResponse
from app.core.services.tenant_context import TenantContext


logger = logging.getLogger(__name__)


class MessageService:
    """
    Serviço que gerencia o envio de mensagens.
    
    Implementa lógica para envio de mensagens através de diferentes canais
    (WhatsApp, SMS, Email) usando a factory de provedores.
    """
    
    def __init__(
        self,
        provider_factory: MessageProviderFactory,
        tenant_context: TenantContext,
    ):
        """
        Inicializa o serviço de mensagens.
        
        Args:
            provider_factory: Factory de provedores de mensagem.
            tenant_context: Contexto de tenant.
        """
        self.provider_factory = provider_factory
        self.tenant_context = tenant_context
        
        logger.info("Serviço de mensagens inicializado")
    
    async def send_message(
        self,
        channel: str,
        to: str,
        template_id: str,
        params: Dict[str, Any],
        tenant_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia uma mensagem usando um template.
        
        Args:
            channel: Canal de envio (whatsapp, sms, email).
            to: Destinatário da mensagem.
            template_id: ID do template a ser usado.
            params: Parâmetros para preenchimento do template.
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            provider_id: ID específico do provedor (opcional).
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
            
        Raises:
            MessagingError: Se houver erro no envio.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Mapear canal para provedor específico se não informado
        if not provider_id:
            provider_id = self._map_channel_to_provider(channel)
        
        try:
            # Obter provedor e enviar mensagem
            provider = self.provider_factory.get_provider(tenant, provider_id)
            
            response = await provider.send(
                to=to,
                template_id=template_id,
                params=params,
                attachments=attachments,
            )
            
            # Logar resultado
            if response.success:
                logger.info(f"Mensagem enviada com sucesso. Canal: {channel}, Provedor: {provider_id}")
            else:
                logger.warning(f"Falha ao enviar mensagem. Canal: {channel}, Erro: {response.error}")
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            
            # Tentar com fallback
            try:
                return await self._send_with_fallback(
                    tenant=tenant,
                    to=to,
                    template_id=template_id,
                    params=params,
                    attachments=attachments,
                )
            except MessagingError as fallback_error:
                logger.error(f"Todos os fallbacks falharam: {str(fallback_error)}")
                raise MessagingError(f"Falha ao enviar mensagem: {str(e)}")
    
    async def send_raw_message(
        self,
        channel: str,
        to: str,
        content: str,
        subject: Optional[str] = None,
        tenant_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia uma mensagem direta sem template.
        
        Args:
            channel: Canal de envio (whatsapp, sms, email).
            to: Destinatário da mensagem.
            content: Conteúdo da mensagem.
            subject: Assunto (para email).
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            provider_id: ID específico do provedor (opcional).
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
            
        Raises:
            MessagingError: Se houver erro no envio.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Mapear canal para provedor específico se não informado
        if not provider_id:
            provider_id = self._map_channel_to_provider(channel)
        
        try:
            # Obter provedor e enviar mensagem
            provider = self.provider_factory.get_provider(tenant, provider_id)
            
            response = await provider.send_raw(
                to=to,
                content=content,
                subject=subject,
                attachments=attachments,
            )
            
            # Logar resultado
            if response.success:
                logger.info(f"Mensagem direta enviada com sucesso. Canal: {channel}, Provedor: {provider_id}")
            else:
                logger.warning(f"Falha ao enviar mensagem direta. Canal: {channel}, Erro: {response.error}")
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem direta: {str(e)}")
            
            # Tentar com fallback
            try:
                return await self._send_raw_with_fallback(
                    tenant=tenant,
                    to=to,
                    content=content,
                    subject=subject,
                    attachments=attachments,
                )
            except MessagingError as fallback_error:
                logger.error(f"Todos os fallbacks falharam: {str(fallback_error)}")
                raise MessagingError(f"Falha ao enviar mensagem direta: {str(e)}")
    
    async def _send_with_fallback(
        self,
        tenant: str,
        to: str,
        template_id: str,
        params: Dict[str, Any],
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia uma mensagem com fallback para outros provedores.
        
        Args:
            tenant: ID do tenant.
            to: Destinatário da mensagem.
            template_id: ID do template a ser usado.
            params: Parâmetros para preenchimento do template.
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
            
        Raises:
            MessagingError: Se todos os provedores falharem.
        """
        async def send_with_provider(provider):
            return await provider.send(
                to=to,
                template_id=template_id,
                params=params,
                attachments=attachments,
            )
        
        return await self.provider_factory.try_with_fallback(tenant, send_with_provider)
    
    async def _send_raw_with_fallback(
        self,
        tenant: str,
        to: str,
        content: str,
        subject: Optional[str] = None,
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia uma mensagem direta com fallback para outros provedores.
        
        Args:
            tenant: ID do tenant.
            to: Destinatário da mensagem.
            content: Conteúdo da mensagem.
            subject: Assunto (para email).
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
            
        Raises:
            MessagingError: Se todos os provedores falharem.
        """
        async def send_raw_with_provider(provider):
            return await provider.send_raw(
                to=to,
                content=content,
                subject=subject,
                attachments=attachments,
            )
        
        return await self.provider_factory.try_with_fallback(tenant, send_raw_with_provider)
    
    def _map_channel_to_provider(self, channel: str) -> str:
        """
        Mapeia um canal para um provedor específico.
        
        Args:
            channel: Canal (whatsapp, sms, email).
            
        Returns:
            ID do provedor para o canal.
        """
        channel_map = {
            "whatsapp": "whatsapp",
            "sms": "sms",
            "email": "email",
            "push": "push",
        }
        
        return channel_map.get(channel.lower(), channel.lower())
