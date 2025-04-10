"""
Configurações da aplicação baseadas em variáveis de ambiente.
Utiliza Pydantic para validação de tipos.
"""
import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas de variáveis de ambiente.
    Inclui validações e valores padrão.
    """

    # API
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Segurança
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 dias
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: Optional[str]) -> Any:
        """Validação especial para URL de banco de dados."""
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user="postgres",
            password="postgres",
            host="db",
            port="5432",
            path="/saas",
        )
    
    # Redis
    REDIS_URL: RedisDsn
    
    @validator("REDIS_URL", pre=True)
    def validate_redis_url(cls, v: Optional[str]) -> Any:
        """Validação especial para URL do Redis."""
        if isinstance(v, str):
            return v
        return RedisDsn.build(
            scheme="redis",
            host="redis",
            port="6379",
            path="/0",
        )
    
    # LocalAI
    LOCAL_AI_URL: AnyHttpUrl = "http://local-ai:8080"
    
    # Tenant
    DEFAULT_TENANT_ID: str = "tenant_pilates_mvp"
    MULTI_TENANT_ENABLED: bool = False  # Desabilitado para MVP
    
    # Plugins
    PLUGINS_ENABLED: bool = True
    PLUGINS_AUTO_DISCOVER: bool = True
    
    # Integração WhatsApp
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None
    
    # Caminhos e diretórios
    STATIC_DIR: str = "static"
    TEMP_DIR: str = "tmp"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instância global das configurações
settings = Settings()
