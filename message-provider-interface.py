"""
Interface para provedores de mensagem seguindo o princípio de Inversão de Dependência.
Define o contrato que todos os provedores de mensagem (WhatsApp, SMS, Email) devem implementar.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Protocol, Any


class MessageChannel(str, Enum):
    """Canais de mensagem suportados."""
    
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


@dataclass
class MessageTemplate:
    """Modelo de mensagem com variáveis."""
    
    id: str
    content: str
    variables: List[str]


@dataclass
class MessageAttachment:
    """Anexo para mensagem."""
    
    type: str
    url: Optional[str] = None
    content: Optional[bytes] = None
    filename: Optional[str] = None


@dataclass
class MessageResponse:
    """Resposta de envio de mensagem."""
    
    success: bool
    message_id: Optional[str] = None
    provider: Optional[str] = None
    channel: Optional[str] = None
    error: Optional[str] = None


class IMessageProvider(Protocol):
    """Interface para provedores de mensagem."""
    
    async def send(
        self,
        to: str,
        template_id: str,
        params: Dict[str, Any],
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia uma mensagem usando um template.
        
        Args:
            to: Destinatário da mensagem.
            template_id: ID do template a ser usado.
            params: Parâmetros para preenchimento do template.
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
        """
        ...
    
    async def send_raw(
        self,
        to: str,
        content: str,
        subject: Optional[str] = None,
        attachments: Optional[List[MessageAttachment]] = None,
    ) -> MessageResponse:
        """
        Envia uma mensagem direta sem template.
        
        Args:
            to: Destinatário da mensagem.
            content: Conteúdo da mensagem.
            subject: Assunto (para email).
            attachments: Anexos opcionais.
            
        Returns:
            MessageResponse: Resposta do envio.
        """
        ...
    
    async def get_template(self, template_id: str) -> Optional[MessageTemplate]:
        """
        Obtém um template por ID.
        
        Args:
            template_id: ID do template.
            
        Returns:
            O template encontrado ou None.
        """
        ...
