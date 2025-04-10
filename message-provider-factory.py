"""
Factory para provedores de mensagens com suporte a fallback.
"""
import logging
from typing import Dict, List, Optional

from app.core.exceptions import MessagingError
from app.core.interfaces.message_provider import IMessageProvider


logger = logging.getLogger(__name__)


class MessageProviderFactory:
    """
    Factory para provedores de mensagem que gerencia fallbacks.
    
    Permite configurar múltiplos provedores de mensagem (WhatsApp, SMS, Email)
    e gerencia a estratégia de fallback caso um provedor falhe.
    """
    
    def __init__(
        self,
        providers: Dict[str, IMessageProvider],
        fallback_config: Dict[str, List[str]],
    ):
        """
        Inicializa a factory com provedores disponíveis.
        
        Args:
            providers: Dicionário com provedores disponíveis.
            fallback_config: Configuração de fallback por tenant.
        """
        self.providers = providers
        self.fallback_config = fallback_config
        
        # Validar configuração
        self._validate_providers()
        
        logger.info(f"MessageProviderFactory inicializada com {len(providers)} provedores")
    
    def get_provider(self, tenant_id: str, provider_id: Optional[str] = None) -> IMessageProvider:
        """
        Obtém um provedor de mensagem para um tenant.
        
        Args:
            tenant_id: ID do tenant.
            provider_id: ID do provedor (opcional, usa o padrão do tenant).
            
        Returns:
            Provedor de mensagem.
            
        Raises:
            MessagingError: Se o provedor não for encontrado.
        """
        # Se não especificou provedor, usar o primeiro da lista de fallback
        if not provider_id:
            fallback_order = self.get_fallback_order(tenant_id)
            if not fallback_order:
                raise MessagingError(f"Não há provedores configurados para o tenant {tenant_id}")
            
            provider_id = fallback_order[0]
        
        # Verificar se o provedor existe
        if provider_id not in self.providers:
            raise MessagingError(f"Provedor {provider_id} não encontrado")
        
        return self.providers[provider_id]
    
    def get_fallback_order(self, tenant_id: str) -> List[str]:
        """
        Obtém a ordem de fallback para um tenant.
        
        Args:
            tenant_id: ID do tenant.
            
        Returns:
            Lista com ordem de provedores para fallback.
        """
        # Verificar se há configuração específica para o tenant
        if tenant_id in self.fallback_config:
            return self.fallback_config[tenant_id]
        
        # Usar configuração padrão
        if "default" in self.fallback_config:
            return self.fallback_config["default"]
        
        # Se não há configuração, usar todos os provedores disponíveis
        return list(self.providers.keys())
    
    def try_with_fallback(self, tenant_id: str, send_method: callable) -> any:
        """
        Tenta enviar uma mensagem com fallback.
        
        Args:
            tenant_id: ID do tenant.
            send_method: Método para enviar a mensagem, recebe o provedor como parâmetro.
            
        Returns:
            Resultado do envio.
            
        Raises:
            MessagingError: Se todos os provedores falharem.
        """
        fallback_order = self.get_fallback_order(tenant_id)
        last_error = None
        
        # Tentar cada provedor na ordem de fallback
        for provider_id in fallback_order:
            if provider_id not in self.providers:
                logger.warning(f"Provedor {provider_id} não encontrado, pulando")
                continue
            
            provider = self.providers[provider_id]
            
            try:
                logger.debug(f"Tentando enviar com provedor {provider_id}")
                result = send_method(provider)
                logger.debug(f"Envio bem-sucedido com provedor {provider_id}")
                return result
            except Exception as e:
                logger.error(f"Falha ao enviar com provedor {provider_id}: {str(e)}")
                last_error = e
        
        # Se chegou aqui, todos os provedores falharam
        raise MessagingError(f"Todos os provedores falharam: {str(last_error)}")
    
    def _validate_providers(self) -> None:
        """
        Valida se a configuração de fallback usa apenas provedores disponíveis.
        
        Raises:
            MessagingError: Se a configuração for inválida.
        """
        for tenant_id, providers_list in self.fallback_config.items():
            for provider_id in providers_list:
                if provider_id not in self.providers:
                    logger.warning(f"Provedor {provider_id} na configuração de fallback não existe")
