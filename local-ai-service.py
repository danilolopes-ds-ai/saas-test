"""
Adaptador para integração com serviço LocalAI.
"""
import json
import logging
from typing import Dict, List, Optional, Any

import httpx

from app.core.exceptions import AIServiceError
from app.core.interfaces.ai_service import IAIService, AIModel, AIResponse, SearchResult
from app.core.interfaces.cache import ICache


logger = logging.getLogger(__name__)


class LocalAIService:
    """
    Implementação do serviço de IA usando LocalAI.
    
    Fornece acesso a modelos de linguagem locais através do LocalAI.
    """
    
    def __init__(
        self,
        api_url: str,
        cache: ICache,
        timeout: int = 60,
    ):
        """
        Inicializa o serviço de IA local.
        
        Args:
            api_url: URL da API do LocalAI.
            cache: Serviço de cache para otimizar requisições.
            timeout: Tempo limite para requisições em segundos.
        """
        self.api_url = api_url.rstrip('/')
        self.cache = cache
        self.timeout = timeout
        
        logger.info(f"Serviço LocalAI inicializado com URL: {api_url}")
    
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
            temperature: Temperatura para geração.
            max_tokens: Máximo de tokens a gerar.
            
        Returns:
            Texto gerado.
            
        Raises:
            AIServiceError: Se houver erro na geração.
        """
        # Verificar cache
        cache_key = f"ai_response:{hash(f'{prompt}|{system}|{model}|{temperature}|{max_tokens}')}"
        
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            logger.debug(f"Resposta obtida do cache: {cache_key[:20]}...")
            return cached_response
        
        # Definir modelo padrão se não informado
        model_name = model or AIModel.PHI3_MINI
        
        try:
            # Preparar payload para API
            payload = {
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Adicionar system prompt se fornecido
            if system:
                payload["system"] = system
            
            # Fazer requisição
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/completions",
                    json=payload,
                )
                
                # Verificar erros de API
                response.raise_for_status()
                
                # Processar resposta
                result = response.json()
                
                if "choices" not in result or not result["choices"]:
                    raise AIServiceError("Resposta inválida do serviço de IA")
                
                text = result["choices"][0]["text"]
                
                # Armazenar em cache (1 hora)
                await self.cache.set(cache_key, text, ttl=3600)
                
                return text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao gerar resposta: {str(e)}")
            raise AIServiceError(f"Erro no serviço de IA (status {e.response.status_code})")
            
        except httpx.TimeoutException:
            logger.error("Timeout ao gerar resposta")
            raise AIServiceError("Timeout na requisição ao serviço de IA")
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            raise AIServiceError(f"Falha ao gerar resposta: {str(e)}")
    
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
            
        Raises:
            AIServiceError: Se houver erro na geração.
        """
        # Verificar cache
        cache_key = f"embedding:{hash(text)}"
        
        cached_embedding = await self.cache.get(cache_key)
        if cached_embedding:
            logger.debug(f"Embedding obtido do cache: {cache_key[:20]}...")
            return cached_embedding
        
        # Definir modelo padrão se não informado
        model_name = model or AIModel.ALL_MINILM
        
        try:
            # Preparar payload para API
            payload = {
                "model": model_name,
                "input": text,
            }
            
            # Fazer requisição
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/embeddings",
                    json=payload,
                )
                
                # Verificar erros de API
                response.raise_for_status()
                
                # Processar resposta
                result = response.json()
                
                if "data" not in result or not result["data"]:
                    raise AIServiceError("Resposta inválida do serviço de embeddings")
                
                embedding = result["data"][0]["embedding"]
                
                # Armazenar em cache (1 dia)
                await self.cache.set(cache_key, embedding, ttl=86400)
                
                return embedding
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao gerar embedding: {str(e)}")
            raise AIServiceError(f"Erro no serviço de embeddings (status {e.response.status_code})")
            
        except httpx.TimeoutException:
            logger.error("Timeout ao gerar embedding")
            raise AIServiceError("Timeout na requisição ao serviço de embeddings")
            
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise AIServiceError(f"Falha ao gerar embedding: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Verifica se o serviço de IA está operacional.
        
        Returns:
            True se operacional, False caso contrário.
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.api_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Falha no health check do serviço de IA: {str(e)}")
            return False
