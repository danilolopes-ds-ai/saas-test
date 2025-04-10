"""
Serviço para gerenciamento de FAQ com RAG (Retrieval Augmented Generation).
"""
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from app.core.exceptions import AIServiceError
from app.core.interfaces.ai_service import IAIService
from app.core.services.tenant_context import TenantContext


logger = logging.getLogger(__name__)


@dataclass
class FAQItem:
    """Item de FAQ com pergunta, resposta e metadados."""
    
    id: str
    question: str
    answer: str
    tags: List[str]
    similarity: Optional[float] = None


class FAQService:
    """
    Serviço para gerenciar perguntas frequentes com RAG.
    
    Implementa funcionalidades para armazenar, pesquisar e responder
    perguntas frequentes usando IA e busca semântica.
    """
    
    def __init__(
        self,
        ai_service: IAIService,
        tenant_context: TenantContext,
    ):
        """
        Inicializa o serviço de FAQ.
        
        Args:
            ai_service: Serviço de IA para geração de embeddings e respostas.
            tenant_context: Contexto de tenant.
        """
        self.ai_service = ai_service
        self.tenant_context = tenant_context
        
        # No MVP, usaremos uma simples coleção em memória por tenant
        # Em produção, isso seria um banco de dados de vetores (Qdrant, Pinecone, etc.)
        self._faq_items: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Serviço de FAQ inicializado")
    
    async def add_faq_item(
        self,
        question: str,
        answer: str,
        tags: List[str] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        """
        Adiciona um item ao FAQ.
        
        Args:
            question: Pergunta.
            answer: Resposta.
            tags: Tags para categorização (opcional).
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            
        Returns:
            ID do item adicionado.
            
        Raises:
            AIServiceError: Se houver erro ao gerar embeddings.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Gerar embedding para a pergunta
        try:
            embedding = await self.ai_service.generate_embeddings(question)
        except Exception as e:
            logger.error(f"Erro ao gerar embedding para FAQ: {str(e)}")
            raise AIServiceError(f"Falha ao gerar embedding: {str(e)}")
        
        # Criar item
        item_id = str(uuid4())
        item = {
            "id": item_id,
            "question": question,
            "answer": answer,
            "tags": tags or [],
            "embedding": embedding,
            "tenant_id": tenant,
        }
        
        # Armazenar no "banco de dados"
        if tenant not in self._faq_items:
            self._faq_items[tenant] = []
        
        self._faq_items[tenant].append(item)
        
        logger.info(f"Item FAQ adicionado: {item_id}")
        return item_id
    
    async def search_faq(
        self,
        query: str,
        tags: List[str] = None,
        top_k: int = 3,
        similarity_threshold: float = 0.6,
        tenant_id: Optional[str] = None,
    ) -> List[FAQItem]:
        """
        Busca itens de FAQ similares à query.
        
        Args:
            query: Pergunta do usuário.
            tags: Filtrar por tags (opcional).
            top_k: Número máximo de resultados.
            similarity_threshold: Limite mínimo de similaridade.
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            
        Returns:
            Lista de itens de FAQ similares.
            
        Raises:
            AIServiceError: Se houver erro ao gerar embeddings.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Verificar se há itens para o tenant
        if tenant not in self._faq_items or not self._faq_items[tenant]:
            return []
        
        # Gerar embedding para a query
        try:
            query_embedding = await self.ai_service.generate_embeddings(query)
        except Exception as e:
            logger.error(f"Erro ao gerar embedding para busca FAQ: {str(e)}")
            raise AIServiceError(f"Falha ao gerar embedding: {str(e)}")
        
        # Calcular similaridade com cada item
        results = []
        for item in self._faq_items[tenant]:
            # Aplicar filtro de tags se especificado
            if tags and not any(tag in item["tags"] for tag in tags):
                continue
            
            # Calcular similaridade de cosseno entre embeddings
            similarity = self._cosine_similarity(query_embedding, item["embedding"])
            
            # Aplicar threshold de similaridade
            if similarity >= similarity_threshold:
                results.append({
                    "id": item["id"],
                    "question": item["question"],
                    "answer": item["answer"],
                    "tags": item["tags"],
                    "similarity": similarity,
                })
        
        # Ordenar por similaridade
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Converter para objetos FAQItem
        faq_items = [
            FAQItem(
                id=r["id"],
                question=r["question"],
                answer=r["answer"],
                tags=r["tags"],
                similarity=r["similarity"],
            )
            for r in results[:top_k]
        ]
        
        return faq_items
    
    async def get_faq_item(
        self,
        item_id: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[FAQItem]:
        """
        Obtém um item de FAQ pelo ID.
        
        Args:
            item_id: ID do item.
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            
        Returns:
            O item encontrado ou None.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Verificar se há itens para o tenant
        if tenant not in self._faq_items:
            return None
        
        # Buscar pelo ID
        for item in self._faq_items[tenant]:
            if item["id"] == item_id:
                return FAQItem(
                    id=item["id"],
                    question=item["question"],
                    answer=item["answer"],
                    tags=item["tags"],
                )
        
        return None
    
    async def update_faq_item(
        self,
        item_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        tags: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[FAQItem]:
        """
        Atualiza um item de FAQ.
        
        Args:
            item_id: ID do item.
            question: Nova pergunta (opcional).
            answer: Nova resposta (opcional).
            tags: Novas tags (opcional).
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            
        Returns:
            O item atualizado ou None se não encontrado.
            
        Raises:
            AIServiceError: Se houver erro ao gerar embeddings.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Verificar se há itens para o tenant
        if tenant not in self._faq_items:
            return None
        
        # Buscar o item pelo ID
        for i, item in enumerate(self._faq_items[tenant]):
            if item["id"] == item_id:
                # Atualizar campos específicos
                if question:
                    item["question"] = question
                    # Atualizar embedding se a pergunta mudou
                    try:
                        item["embedding"] = await self.ai_service.generate_embeddings(question)
                    except Exception as e:
                        logger.error(f"Erro ao gerar embedding para FAQ atualizado: {str(e)}")
                        raise AIServiceError(f"Falha ao gerar embedding: {str(e)}")
                
                if answer:
                    item["answer"] = answer
                
                if tags is not None:
                    item["tags"] = tags
                
                # Atualizar no "banco de dados"
                self._faq_items[tenant][i] = item
                
                logger.info(f"Item FAQ atualizado: {item_id}")
                
                return FAQItem(
                    id=item["id"],
                    question=item["question"],
                    answer=item["answer"],
                    tags=item["tags"],
                )
        
        return None
    
    async def delete_faq_item(
        self,
        item_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Remove um item de FAQ.
        
        Args:
            item_id: ID do item.
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            
        Returns:
            True se removido com sucesso, False caso contrário.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Verificar se há itens para o tenant
        if tenant not in self._faq_items:
            return False
        
        # Buscar e remover o item
        for i, item in enumerate(self._faq_items[tenant]):
            if item["id"] == item_id:
                self._faq_items[tenant].pop(i)
                logger.info(f"Item FAQ removido: {item_id}")
                return True
        
        return False
    
    async def list_faq_items(
        self,
        tags: List[str] = None,
        tenant_id: Optional[str] = None,
    ) -> List[FAQItem]:
        """
        Lista todos os itens de FAQ, com filtro opcional por tags.
        
        Args:
            tags: Filtrar por tags (opcional).
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            
        Returns:
            Lista de itens de FAQ.
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Verificar se há itens para o tenant
        if tenant not in self._faq_items:
            return []
        
        # Filtrar por tags se especificado
        if tags:
            filtered_items = [
                item for item in self._faq_items[tenant]
                if any(tag in item["tags"] for tag in tags)
            ]
        else:
            filtered_items = self._faq_items[tenant]
        
        # Converter para objetos FAQItem
        faq_items = [
            FAQItem(
                id=item["id"],
                question=item["question"],
                answer=item["answer"],
                tags=item["tags"],
            )
            for item in filtered_items
        ]
        
        return faq_items
    
    async def answer_question(
        self,
        question: str,
        tags: List[str] = None,
        tenant_id: Optional[str] = None,
        similarity_threshold: float = 0.7,
        use_ai_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Responde uma pergunta usando RAG (busca + geração).
        
        Primeiro busca nas FAQs existentes, e se não encontrar uma resposta
        com similaridade suficiente, usa IA para gerar uma resposta.
        
        Args:
            question: Pergunta do usuário.
            tags: Filtrar por tags (opcional).
            tenant_id: ID do tenant (opcional, usa o contexto atual).
            similarity_threshold: Limite mínimo de similaridade para usar FAQ.
            use_ai_fallback: Se deve usar IA para gerar resposta quando não encontrar.
            
        Returns:
            Dicionário com a resposta e metadados.
        """
        # Buscar FAQs similares
        faq_items = await self.search_faq(
            query=question,
            tags=tags,
            tenant_id=tenant_id,
            top_k=3,
            similarity_threshold=0.5,  # Threshold mais baixo para ter contexto
        )
        
        # Verificar se encontrou uma resposta com similaridade suficiente
        if faq_items and faq_items[0].similarity >= similarity_threshold:
            # Usar a resposta do FAQ
            best_match = faq_items[0]
            return {
                "answer": best_match.answer,
                "source": "faq",
                "faq_item_id": best_match.id,
                "similarity": best_match.similarity,
            }
        
        # Se não encontrou ou tem baixa similaridade, usar IA para gerar resposta
        if use_ai_fallback:
            try:
                # Preparar contexto com FAQs encontradas
                context = ""
                if faq_items:
                    context = "Informações relevantes:\n"
                    for item in faq_items:
                        context += f"P: {item.question}\nR: {item.answer}\n\n"
                
                # Sistema para a IA
                system = """
                Você é um assistente de FAQ para profissionais de saúde e bem-estar.
                Responda de forma concisa, clara e útil.
                Use apenas as informações fornecidas no contexto se disponíveis.
                Se não houver informações suficientes, indique isso de forma educada.
                """
                
                # Prompt combinando contexto e pergunta
                prompt = f"""
                {context}
                
                Pergunta do usuário: {question}
                
                Responda de forma direta e concisa.
                """
                
                # Gerar resposta
                ai_response = await self.ai_service.generate_response(
                    prompt=prompt,
                    system=system,
                )
                
                return {
                    "answer": ai_response,
                    "source": "ai",
                    "faq_items": [item.id for item in faq_items],
                }
            except Exception as e:
                logger.error(f"Erro ao gerar resposta com IA: {str(e)}")
                # Retornar a melhor resposta do FAQ mesmo abaixo do threshold
                if faq_items:
                    best_match = faq_items[0]
                    return {
                        "answer": best_match.answer,
                        "source": "faq_fallback",
                        "faq_item_id": best_match.id,
                        "similarity": best_match.similarity,
                        "error": str(e),
                    }
        
        # Se chegou aqui, não encontrou resposta e não usou/falhou IA
        return {
            "answer": "Desculpe, não encontrei uma resposta para esta pergunta.",
            "source": "default",
        }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcula a similaridade de cosseno entre dois vetores.
        
        Args:
            vec1: Primeiro vetor.
            vec2: Segundo vetor.
            
        Returns:
            Similaridade de cosseno (0 a 1).
        """
        # Verificar tamanhos
        if len(vec1) != len(vec2):
            raise ValueError("Os vetores devem ter o mesmo tamanho")
        
        # Calcular produto escalar
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calcular magnitudes
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        # Evitar divisão por zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        # Calcular similaridade
        return dot_product / (magnitude1 * magnitude2)
    
    async def initialize_default_faqs(self, tenant_id: Optional[str] = None) -> None:
        """
        Inicializa o FAQ com perguntas e respostas padrão para um tenant.
        
        Args:
            tenant_id: ID do tenant (opcional, usa o contexto atual).
        """
        # Usar tenant_id específico ou do contexto
        tenant = tenant_id or self.tenant_context.tenant_id
        
        # Verificar se já tem itens
        if tenant in self._faq_items and self._faq_items[tenant]:
            logger.info(f"FAQ já inicializado para tenant {tenant}")
            return
        
        # Perguntas e respostas padrão para Pilates/Fitness
        default_faqs = [
            {
                "question": "Como funciona o agendamento de aulas?",
                "answer": "O agendamento pode ser feito pelo aplicativo, site ou WhatsApp. Você pode ver os horários disponíveis e escolher o que melhor se adapta à sua agenda. É recomendável agendar com pelo menos 24h de antecedência.",
                "tags": ["agendamento", "aulas"],
            },
            {
                "question": "Posso cancelar uma aula agendada?",
                "answer": "Sim, você pode cancelar aulas com até 6 horas de antecedência sem custo. Cancelamentos com menos de 6 horas podem resultar na perda da sessão, dependendo do seu plano.",
                "tags": ["cancelamento", "aulas", "agendamento"],
            },
            {
                "question": "Quais são os planos disponíveis?",
                "answer": "Oferecemos planos mensais com frequências de 1x, 2x ou 3x por semana, além de pacotes trimestrais com desconto. Também temos opções de aulas avulsas para quem prefere maior flexibilidade.",
                "tags": ["planos", "preços", "pagamento"],
            },
            {
                "question": "Preciso trazer algum material para as aulas?",
                "answer": "Não é necessário trazer nenhum material, fornecemos todos os equipamentos necessários. Apenas recomendamos o uso de roupas confortáveis, meias antiderrapantes (para Pilates) e uma garrafa de água.",
                "tags": ["aulas", "materiais", "equipamentos"],
            },
            {
                "question": "Qual a duração das aulas?",
                "answer": "Nossas aulas têm duração de 50 minutos, com 10 minutos de intervalo entre as sessões para troca de alunos e higienização dos equipamentos.",
                "tags": ["aulas", "duração"],
            },
        ]
        
        # Adicionar ao sistema
        for faq in default_faqs:
            await self.add_faq_item(
                question=faq["question"],
                answer=faq["answer"],
                tags=faq["tags"],
                tenant_id=tenant,
            )
        
        logger.info(f"FAQ inicializado com {len(default_faqs)} itens para tenant {tenant}")
