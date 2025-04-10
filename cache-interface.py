"""
Interface para serviços de cache seguindo o princípio de Inversão de Dependência.
Define o contrato que qualquer implementação de cache deve seguir.
"""
from typing import Any, Dict, List, Optional, Protocol, Union, TypeVar, Generic

# Tipo genérico para valor de cache
T = TypeVar('T')


class ICache(Protocol):
    """Interface para serviços de cache."""
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave para buscar.
            
        Returns:
            O valor armazenado ou None se não encontrado.
        """
        ...
    
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
        ...
    
    async def delete(self, key: str) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave para remover.
            
        Returns:
            True se removido com sucesso, False caso contrário.
        """
        ...
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave para verificar.
            
        Returns:
            True se existe, False caso contrário.
        """
        ...
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Incrementa um valor numérico no cache.
        
        Args:
            key: Chave para incrementar.
            amount: Valor a incrementar (padrão: 1).
            
        Returns:
            Novo valor após incremento.
        """
        ...
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Define o tempo de expiração para uma chave.
        
        Args:
            key: Chave para definir expiração.
            seconds: Tempo em segundos.
            
        Returns:
            True se definido com sucesso, False caso contrário.
        """
        ...
    
    async def clear(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            True se limpo com sucesso, False caso contrário.
        """
        ...
    
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
        ...
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Obtém múltiplos valores do cache.
        
        Args:
            keys: Lista de chaves para buscar.
            
        Returns:
            Dicionário com chaves e valores encontrados.
        """
        ...
    
    async def set_many(self, values: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Define múltiplos valores no cache.
        
        Args:
            values: Dicionário com chaves e valores para armazenar.
            ttl: Tempo de vida em segundos (opcional).
            
        Returns:
            True se todos armazenados com sucesso, False caso contrário.
        """
        ...
    
    async def delete_many(self, keys: List[str]) -> int:
        """
        Remove múltiplos valores do cache.
        
        Args:
            keys: Lista de chaves para remover.
            
        Returns:
            Número de chaves removidas.
        """
        ...
    
    async def health_check(self) -> bool:
        """
        Verifica se o serviço de cache está operacional.
        
        Returns:
            True se operacional, False caso contrário.
        """
        ...
