"""
Container de injeção de dependência para a aplicação.
Implementa o princípio de Dependency Inversion (SOLID).
"""
import logging
from typing import Dict

from injector import Binder, Injector, Module, provider, singleton

from app.adapters.db.database import Database
from app.adapters.db.repositories import (
    AppointmentRepository, 
    ClientRepository, 
    ProfessionalRepository,
    UserRepository,
)
from app.adapters.messaging.message_provider_factory import MessageProviderFactory
from app.adapters.messaging.twilio_provider import TwilioWhatsAppProvider
from app.adapters.messaging.email_provider import SMTPEmailProvider
from app.adapters.api.local_ai_service import LocalAIService
from app.core.config import settings
from app.core.interfaces.message_provider import IMessageProvider
from app.core.interfaces.repositories import (
    IAppointmentRepository, 
    IClientRepository, 
    IProfessionalRepository,
    IUserRepository,
)
from app.core.interfaces.ai_service import IAIService
from app.core.services.tenant_context import TenantContext
from app.core.services.message_service import MessageService
from app.core.services.user_service import UserService
from app.core.services.appointment_service import AppointmentService
from app.core.services.faq_service import FAQService
from app.adapters.cache.redis_cache import RedisCache
from app.core.interfaces.cache import ICache
from app.plugins.manager import PluginManager


logger = logging.getLogger(__name__)


class ApplicationModule(Module):
    """Módulo principal para configuração de dependências."""
    
    @singleton
    @provider
    def provide_tenant_context(self) -> TenantContext:
        """Fornece o contexto de tenant."""
        return TenantContext(default_tenant_id=settings.DEFAULT_TENANT_ID)
    
    @singleton
    @provider
    def provide_database(self) -> Database:
        """Fornece a conexão com o banco de dados."""
        return Database(
            db_url=str(settings.DATABASE_URL),
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
        )
    
    @singleton
    @provider
    def provide_cache(self) -> ICache:
        """Fornece o serviço de cache."""
        return RedisCache(redis_url=str(settings.REDIS_URL))
    
    @singleton
    @provider
    def provide_appointment_repository(
        self, database: Database, tenant_context: TenantContext
    ) -> IAppointmentRepository:
        """Fornece o repositório de agendamentos."""
        return AppointmentRepository(database, tenant_context)
    
    @singleton
    @provider
    def provide_client_repository(
        self, database: Database, tenant_context: TenantContext
    ) -> IClientRepository:
        """Fornece o repositório de clientes."""
        return ClientRepository(database, tenant_context)
    
    @singleton
    @provider
    def provide_professional_repository(
        self, database: Database, tenant_context: TenantContext
    ) -> IProfessionalRepository:
        """Fornece o repositório de profissionais."""
        return ProfessionalRepository(database, tenant_context)
    
    @singleton
    @provider
    def provide_user_repository(
        self, database: Database, tenant_context: TenantContext
    ) -> IUserRepository:
        """Fornece o repositório de usuários."""
        return UserRepository(database, tenant_context)
    
    @singleton
    @provider
    def provide_message_providers(self) -> Dict[str, IMessageProvider]:
        """Fornece os provedores de mensagem disponíveis."""
        providers = {}
        
        # Adicionar provedor de WhatsApp se configurado
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            providers["whatsapp"] = TwilioWhatsAppProvider(
                account_sid=settings.TWILIO_ACCOUNT_SID,
                auth_token=settings.TWILIO_AUTH_TOKEN,
                whatsapp_number=settings.TWILIO_WHATSAPP_NUMBER or "",
            )
        
        # Adicionar provedor de fallback (SMS, Email, etc.)
        providers["email"] = SMTPEmailProvider()
        
        return providers
    
    @singleton
    @provider
    def provide_message_provider_factory(
        self, providers: Dict[str, IMessageProvider]
    ) -> MessageProviderFactory:
        """Fornece a factory de provedores de mensagem."""
        # Configuração de fallback
        fallback_config = {
            # Default: WhatsApp -> Email
            "default": ["whatsapp", "email"],
        }
        
        return MessageProviderFactory(
            providers=providers,
            fallback_config=fallback_config,
        )
    
    @singleton
    @provider
    def provide_message_service(
        self, provider_factory: MessageProviderFactory, tenant_context: TenantContext
    ) -> MessageService:
        """Fornece o serviço de mensagens."""
        return MessageService(
            provider_factory=provider_factory,
            tenant_context=tenant_context,
        )
    
    @singleton
    @provider
    def provide_ai_service(self, cache: ICache) -> IAIService:
        """Fornece o serviço de IA."""
        return LocalAIService(
            api_url=str(settings.LOCAL_AI_URL),
            cache=cache,
        )
    
    @singleton
    @provider
    def provide_plugin_manager(self) -> PluginManager:
        """Fornece o gerenciador de plugins."""
        return PluginManager()
    
    @singleton
    @provider
    def provide_faq_service(
        self, ai_service: IAIService, tenant_context: TenantContext
    ) -> FAQService:
        """Fornece o serviço de FAQ."""
        return FAQService(
            ai_service=ai_service,
            tenant_context=tenant_context,
        )
    
    @singleton
    @provider
    def provide_appointment_service(
        self,
        appointment_repository: IAppointmentRepository,
        message_service: MessageService,
        tenant_context: TenantContext,
    ) -> AppointmentService:
        """Fornece o serviço de agendamentos."""
        return AppointmentService(
            repository=appointment_repository,
            message_service=message_service,
            tenant_context=tenant_context,
        )


def setup_di() -> Injector:
    """
    Configura e retorna o container de injeção de dependência.
    
    Returns:
        Injector: Container de injeção de dependência configurado.
    """
    injector = Injector([ApplicationModule()])
    logger.info("Container de injeção de dependência configurado com sucesso")
    return injector
