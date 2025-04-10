"""
Exceções personalizadas para o domínio da aplicação.
"""

class BaseAppException(Exception):
    """Exceção base para todas as exceções da aplicação."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# Exceções de Tenant
class TenantError(BaseAppException):
    """Exceção base para erros relacionados a tenants."""
    pass


class TenantNotSetError(TenantError):
    """Erro quando o tenant não está configurado."""
    pass


class TenantNotFoundError(TenantError):
    """Erro quando o tenant não é encontrado."""
    pass


# Exceções de Autenticação e Autorização
class AuthError(BaseAppException):
    """Exceção base para erros de autenticação e autorização."""
    pass


class InvalidCredentialsError(AuthError):
    """Erro quando as credenciais são inválidas."""
    pass


class PermissionDeniedError(AuthError):
    """Erro quando o usuário não tem permissão para a ação."""
    pass


class TokenExpiredError(AuthError):
    """Erro quando o token de autenticação expirou."""
    pass


# Exceções de Recursos
class ResourceError(BaseAppException):
    """Exceção base para erros relacionados a recursos."""
    pass


class ResourceNotFoundError(ResourceError):
    """Erro quando um recurso não é encontrado."""
    pass


class ResourceAlreadyExistsError(ResourceError):
    """Erro quando um recurso já existe."""
    pass


class ResourceUpdateError(ResourceError):
    """Erro ao atualizar um recurso."""
    pass


class ResourceDeleteError(ResourceError):
    """Erro ao excluir um recurso."""
    pass


# Exceções de Validação
class ValidationError(BaseAppException):
    """Exceção base para erros de validação."""
    
    def __init__(self, message: str, errors: dict = None):
        self.errors = errors or {}
        super().__init__(message)


# Exceções de Serviços Externos
class ExternalServiceError(BaseAppException):
    """Exceção base para erros em serviços externos."""
    pass


class MessagingError(ExternalServiceError):
    """Erro em serviços de mensagem."""
    pass


class AIServiceError(ExternalServiceError):
    """Erro em serviços de IA."""
    pass


# Exceções de Plugin
class PluginError(BaseAppException):
    """Exceção base para erros relacionados a plugins."""
    pass


class InvalidPluginError(PluginError):
    """Erro quando um plugin é inválido."""
    pass


class PluginNotFoundError(PluginError):
    """Erro quando um plugin não é encontrado."""
    pass


# Exceções de Limites
class LimitError(BaseAppException):
    """Exceção base para erros relacionados a limites."""
    pass


class RateLimitExceededError(LimitError):
    """Erro quando o limite de taxa é excedido."""
    pass


class UsageLimitExceededError(LimitError):
    """Erro quando o limite de uso é excedido."""
    pass


# Exceções de Agendamento
class AppointmentError(BaseAppException):
    """Exceção base para erros relacionados a agendamentos."""
    pass


class SlotUnavailableError(AppointmentError):
    """Erro quando um horário não está disponível."""
    pass


class ConflictingAppointmentError(AppointmentError):
    """Erro quando há conflito de agendamento."""
    pass