"""
Adaptador para conexão com banco de dados PostgreSQL.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url

from app.core.exceptions import DatabaseError


logger = logging.getLogger(__name__)


class Database:
    """
    Classe para gerenciar conexão e operações no banco de dados.
    
    Implementa padrão adapter para o sistema de banco de dados.
    """
    
    def __init__(
        self,
        db_url: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        echo: bool = False,
    ):
        """
        Inicializa a conexão com o banco de dados.
        
        Args:
            db_url: URL de conexão com o banco.
            pool_size: Tamanho do pool de conexões.
            max_overflow: Máximo de conexões extras além do pool.
            echo: Se True, exibe queries SQL no log.
        """
        self.db_url = db_url
        
        try:
            # Criar engine assíncrona para operações regulares
            self.engine = create_async_engine(
                db_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                echo=echo,
                pool_pre_ping=True,  # Verifica conexão antes de usar
            )
            
            # Sessão assíncrona para a aplicação
            self.async_session = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            
            logger.info(f"Conexão com banco de dados inicializada: {self._masked_url(db_url)}")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
            raise DatabaseError(f"Falha na conexão com o banco de dados: {str(e)}")
    
    async def get_session(self) -> AsyncSession:
        """
        Obtém uma sessão do banco de dados para uso em um contexto assíncrono.
        
        Returns:
            AsyncSession: Sessão assíncrona do SQLAlchemy.
        """
        return self.async_session()
    
    async def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """
        Executa uma query SQL diretamente.
        
        Args:
            query: String SQL a executar.
            params: Parâmetros para a query (opcional).
            
        Returns:
            Resultado da query.
            
        Raises:
            DatabaseError: Se houver erro na execução.
        """
        async with self.async_session() as session:
            try:
                result = await session.execute(text(query), params or {})
                return result
            except Exception as e:
                logger.error(f"Erro ao executar query: {str(e)}")
                raise DatabaseError(f"Falha na execução da query: {str(e)}")
    
    async def fetch_one(self, query: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Executa uma query e retorna a primeira linha.
        
        Args:
            query: String SQL a executar.
            params: Parâmetros para a query (opcional).
            
        Returns:
            Primeira linha como dicionário ou None.
            
        Raises:
            DatabaseError: Se houver erro na execução.
        """
        async with self.async_session() as session:
            try:
                result = await session.execute(text(query), params or {})
                row = result.first()
                return dict(row._mapping) if row else None
            except Exception as e:
                logger.error(f"Erro ao executar fetch_one: {str(e)}")
                raise DatabaseError(f"Falha ao buscar registro: {str(e)}")
    
    async def fetch_all(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Executa uma query e retorna todas as linhas.
        
        Args:
            query: String SQL a executar.
            params: Parâmetros para a query (opcional).
            
        Returns:
            Lista de linhas como dicionários.
            
        Raises:
            DatabaseError: Se houver erro na execução.
        """
        async with self.async_session() as session:
            try:
                result = await session.execute(text(query), params or {})
                return [dict(row._mapping) for row in result.all()]
            except Exception as e:
                logger.error(f"Erro ao executar fetch_all: {str(e)}")
                raise DatabaseError(f"Falha ao buscar registros: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Verifica se a conexão com o banco está funcional.
        
        Returns:
            True se ok, False caso contrário.
        """
        try:
            async with self.async_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Falha no health check do banco: {str(e)}")
            return False
    
    def _masked_url(self, url: str) -> str:
        """
        Mascara a senha na URL para exibição segura no log.
        
        Args:
            url: URL original com senha.
            
        Returns:
            URL com senha mascarada.
        """
        parsed = make_url(url)
        if parsed.password:
            return str(parsed).replace(parsed.password, '******')
        return str(parsed)
