"""
Interface para serviços de IA seguindo o princípio de Inversão de Dependência.
Define o contrato que qualquer serviço de IA deve implementar.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Protocol, Any


class AIModel(str, Enum):
    """Modelos de IA suportados."""
    
    PHI3_MINI = "phi-3-mini"
    GPT4ALL_FALCON = "gpt4all-falcon"
    ALL_MINILM = "all-minilm"  # Para embeddings


@dataclass
class AIResponse:
    """Resposta de uma requisição de IA."""
    
    text: str
    model: str
    token_usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Resultado de busca vetorial."""
    
    id: str
    similarity: float
    metadata: Dict[str, Any]


class IAIService(Protocol):
    """Interface para serviços de IA."""
    
    async def generate_response(
        self, 
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> str:
        """
        Gera uma resposta de texto a partir de um prompt.
        
        Args:
            prompt: Texto de entrada.
            system: Prompt de sistema (opcional).
            model: Modelo a ser usado (opcional).
            temperature: Temperatura para geração (mais alta = mais criativa).
            max_tokens: Máximo de tokens a gerar.
            
        Returns:
            Texto gerado.
        """
        ...
    
    async def generate_embeddings(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Gera embeddings (representações vetoriais) para um texto.
        
        Args:
            text: Texto para gerar embeddings.
            model: Modelo a ser usado (opcional).
            
        Returns:
            Lista de valores do vetor de embedding.
        """
        ...
    
    async def health_check(self) -> bool:
        """
        Verifica se o serviço de IA está operacional.
        
        Returns:
            True se operacional, False caso contrário.
        """
        ...
