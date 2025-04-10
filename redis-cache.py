"""
Adaptador para serviço de cache usando Redis.
"""
import json
import logging
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from app.core.exceptions import CacheError
from app.core.interfaces.cache import ICache


logger = logging.getLogger(__name__)


class RedisCache:
    """
    Implementação de cache usando Redis.
    
    Implementa a interface ICache para fornecer funcionalidades de cache
    distribuído usando Redis.
    """
    
    def __init__(
        self,
        redis_url: str,
        prefix: str = "saas:",
    ):
        """
        Inicializa o adaptador de cache Redis.
        
        Args:
            redis_url: URL de conexão com o Redis.
            prefix: Prefixo para todas as chaves (para separar ambientes).
        """
        self.redis_url = redis_url
        self.prefix = prefix
        
        try:
            # Conectar ao Redis
            self.redis = redis.from_url(redis_url, decode_responses=True)
            logger.info(f"Cache Redis inicializado: {self._masked_url(redis_url)}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            raise CacheError(f"Falha na conexão com Redis: {str(e)}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave para buscar.
            
        Returns:
            O valor armazenado ou None se não encontrado.
        """
        try:
            prefixed_key = self._prefix_key(key)
            value = await self.redis.get(prefixed_key)
            
            if value is None:
                return None
            
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Erro ao obter do cache: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Define um valor no cache.
        
        Args:
            key: Chave para armazenar.
            value: Valor a ser armazenado.
            ttl: Tempo de vida em segundos (opcional).
            
        Returns:
            True se armazenado com sucesso, False caso contrário.
        """
        try:
            prefixed_key = self._prefix_key(key)
            serialized = self._serialize(value)
            
            if ttl:
                result = await self.redis.setex(prefixed_key, ttl, serialized)
            else:
                result = await self.redis.set(prefixed_key, serialized)
            
            return result == "OK"
        except Exception as e:
            logger.error(f"Erro ao definir no cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave para remover.
            
        Returns:
            True se removido com sucesso, False caso contrário.
        """
        try:
            prefixed_key = self._prefix_key(key)
            result = await self.redis.delete(prefixed_key)
            return result > 0
        except Exception as e:
            logger.error(f"Erro ao remover do cache: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave para verificar.
            
        Returns:
            True se existe, False caso contrário.
        """
        try:
            prefixed_key = self._prefix_key(key)
            result = await self.redis.exists(prefixed_key)
            return result > 0
        except Exception as e:
            logger.error(f"Erro ao verificar existência no cache: {str(e)}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Incrementa um valor numérico no cache.
        
        Args:
            key: Chave para incrementar.
            amount: Valor a incrementar (padrão: 1).
            
        Returns:
            Novo valor após incremento.
        """
        try:
            prefixed_key = self._prefix_key(key)
            result = await self.redis.incrby(prefixed_key, amount)
            return result
        except Exception as e:
            logger.error(f"Erro ao incrementar no cache: {str(e)}")
            raise CacheError(f"Falha ao incrementar: {str(e)}")
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Define o tempo de expiração para uma chave.
        
        Args:
            key: Chave para definir expiração.
            seconds: Tempo em segundos.
            
        Returns:
            True se definido com sucesso, False caso contrário.
        """
        try:
            prefixed_key = self._prefix_key(key)
            result = await self.redis.expire(prefixed_key, seconds)
            return result > 0
        except Exception as e:
            logger.error(f"Erro ao definir expiração no cache: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """
        Limpa todo o cache do aplicativo (apenas chaves com o prefixo).
        
        Returns:
            True se limpo com sucesso, False caso contrário.
        """
        try:
            # Buscar todas as chaves com o prefixo
            pattern = f"{self.prefix}*"
            cursor = 0
            count = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                
                if keys:
                    await self.redis.delete(*keys)
                    count += len(keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cache limpo: {count} chaves removidas")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False
    
    async def get_or_set(self, key: str, value_factory: callable, ttl: Optional[int] = None) -> Any:
        """
        Obtém um valor do cache. Se não existir, define usando uma factory.
        
        Args:
            key: Chave para buscar/armazenar.
            value_factory: Função assíncrona que retorna o valor caso não exista no cache.
            ttl: Tempo de vida em segundos (opcional).
            
        Returns:
            Valor do cache ou resultado da factory.
        """
        # Tentar obter do cache
        value = await self.get(key)
        
        if value is not None:
            return value
        
        # Se não existe, calcular valor
        value = await value_factory()
        
        # Armazenar em cache para uso futuro
        await self.set(key, value, ttl)
        
        return value
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Obtém múltiplos valores do cache.
        
        Args:
            keys: Lista de chaves para buscar.
            
        Returns:
            Dicionário com chaves e valores encontrados.
        """
        try:
            # Aplicar prefixo em todas as chaves
            prefixed_keys = [self._prefix_key(key) for key in keys]
            
            # Buscar valores
            values = await self.redis.mget(prefixed_keys)
            
            # Preparar resultado
            result = {}
            for i, key in enumerate(keys):
                if values[i] is not None:
                    result[key] = self._deserialize(values[i])
            
            return result
        except Exception as e:
            logger.error(f"Erro ao obter múltiplos valores do cache: {str(e)}")
            return {}
    
    async def set_many(self, values: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Define múltiplos valores no cache.
        
        Args:
            values: Dicionário com chaves e valores para armazenar.
            ttl: Tempo de vida em segundos (opcional).
            
        Returns:
            True se todos armazenados com sucesso, False caso contrário.
        """
        try:
            # Preparar valores para armazenamento
            pipeline = self.redis.pipeline()
            
            for key, value in values.items():
                prefixed_key = self._prefix_key(key)
                serialized = self._serialize(value)
                
                pipeline.set(prefixed_key, serialized)
                if ttl:
                    pipeline.expire(prefixed_key, ttl)
            
            # Executar todas as operações
            results = await pipeline.execute()
            
            # Verificar se todas as operações foram bem-sucedidas
            set_results = results[::2] if ttl else results
            return all(result == "OK" for result in set_results)
        except Exception as e:
            logger.error(f"Erro ao definir múltiplos valores no cache: {str(e)}")
            return False
    
    async def delete_many(self, keys: List[str]) -> int:
        """
        Remove múltiplos valores do cache.
        
        Args:
            keys: Lista de chaves para remover.
            
        Returns:
            Número de chaves removidas.
        """
        try:
            if not keys:
                return 0
                
            # Aplicar prefixo em todas as chaves
            prefixed_keys = [self._prefix_key(key) for key in keys]
            
            # Remover chaves
            result = await self.redis.delete(*prefixed_keys)
            return result
        except Exception as e:
            logger.error(f"Erro ao remover múltiplos valores do cache: {str(e)}")
            return 0
    
    async def health_check(self) -> bool:
        """
        Verifica se o serviço de cache está operacional.
        
        Returns:
            True se operacional, False caso contrário.
        """
        try:
            pong = await self.redis.ping()
            return pong
        except Exception as e:
            logger.warning(f"Falha no health check do Redis: {str(e)}")
            return False
    
    def _prefix_key(self, key: str) -> str:
        """
        Adiciona o prefixo à chave.
        
        Args:
            key: Chave original.
            
        Returns:
            Chave com prefixo.
        """
        return f"{self.prefix}{key}"
    
    def _serialize(self, value: Any) -> str:
        """
        Serializa um valor para armazenamento no Redis.
        
        Args:
            value: Valor a serializar.
            
        Returns:
            Valor serializado em string.
        """
        if isinstance(value, (str, int, float, bool)) or value is None:
            return json.dumps(value)
        else:
            return json.dumps(value)
    
    def _deserialize(self, value: str) -> Any:
        """
        Desserializa um valor do Redis.
        
        Args:
            value: Valor serializado.
            
        Returns:
            Valor desserializado.
        """
        try:
            return json.loads(value)
        except Exception:
            return value
    
    def _masked_url(self, url: str) -> str:
        """
        Mascara a senha na URL para exibição segura no log.
        
        Args:
            url: URL original com senha.
            
        Returns:
            URL com senha mascarada.
        """
        if '@' in url:
            protocol_auth, rest = url.split('@', 1)
            if ':' in protocol_auth:
                auth_parts = protocol_auth.split(':')
                if len(auth_parts) >= 3:  # protocol:user:pass
                    auth_parts[-1] = '******'
                    protocol_auth = ':'.join(auth_parts)
                
            return f"{protocol_auth}@{rest}"
        return url
