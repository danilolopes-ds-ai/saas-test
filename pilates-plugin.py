"""
Plugin para o nicho de Pilates/Fitness.
"""
import logging
from typing import Dict, List, Any

from app.plugins.manager import NichoPlugin


logger = logging.getLogger(__name__)


class PilatesFitnessPlugin(NichoPlugin):
    """
    Plugin para o nicho de Pilates e Fitness.
    
    Fornece templates, campos customizados e fluxos específicos para
    profissionais de Pilates e Fitness.
    """
    
    @property
    def id(self) -> str:
        """ID único do plugin."""
        return "pilates_fitness"
    
    @property
    def version(self) -> str:
        """Versão do plugin."""
        return "1.0.0"
    
    @property
    def name(self) -> str:
        """Nome amigável do plugin."""
        return "Pilates e Fitness"
    
    @property
    def nicho_id(self) -> str:
        """ID do nicho."""
        return "pilates"
    
    def initialize(self) -> None:
        """Inicializa o plugin."""
        logger.info(f"Inicializando plugin {self.name} v{self.version}")
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Retorna templates de mensagem específicos para Pilates/Fitness.
        
        Returns:
            Lista de templates.
        """
        return [
            {
                "id": "confirmacao_aula",
                "name": "Confirmação de Aula",
                "content": "Olá {{nome}}, confirmamos sua aula de {{modalidade}} para {{data}} às {{hora}}. Responda S para confirmar.",
                "variables": ["nome", "modalidade", "data", "hora"],
                "channel": "whatsapp",
            },
            {
                "id": "lembrete_aula",
                "name": "Lembrete de Aula",
                "content": "Lembrete: Sua aula de {{modalidade}} está agendada para amanhã às {{hora}}. Até lá!",
                "variables": ["modalidade", "hora"],
                "channel": "whatsapp",
            },
            {
                "id": "boas_vindas",
                "name": "Boas-vindas",
                "content": "Olá {{nome}}, bem-vindo(a) ao {{studio}}! Estamos felizes em tê-lo(a) como aluno(a). Qualquer dúvida estamos à disposição.",
                "variables": ["nome", "studio"],
                "channel": "whatsapp",
            },
            {
                "id": "recuperacao_aluno",
                "name": "Recuperação de Aluno",
                "content": "Olá {{nome}}, sentimos sua falta nas aulas! Já faz {{dias}} dias desde sua última visita. Que tal agendar uma aula? Temos horários disponíveis para você.",
                "variables": ["nome", "dias"],
                "channel": "whatsapp",
            },
            {
                "id": "aniversario",
                "name": "Aniversário",
                "content": "Olá {{nome}}, toda a equipe do {{studio}} deseja um feliz aniversário! Como presente, você ganhou uma aula extra este mês. Aproveite!",
                "variables": ["nome", "studio"],
                "channel": "whatsapp",
            },
        ]
    
    def get_fields(self) -> List[Dict[str, Any]]:
        """
        Retorna campos customizados para Pilates/Fitness.
        
        Returns:
            Lista de campos customizados.
        """
        return [
            {
                "id": "modalidade",
                "name": "Modalidade",
                "type": "select",
                "entity": "appointment",
                "options": [
                    "Pilates Solo", 
                    "Pilates Aparelho", 
                    "Funcional", 
                    "Yoga", 
                    "Personal", 
                    "Avaliação Física"
                ],
                "required": True,
            },
            {
                "id": "nivel",
                "name": "Nível",
                "type": "select",
                "entity": "client",
                "options": ["Iniciante", "Intermediário", "Avançado"],
                "required": False,
            },
            {
                "id": "restricoes",
                "name": "Restrições Físicas",
                "type": "text",
                "entity": "client",
                "required": False,
            },
            {
                "id": "objetivo",
                "name": "Objetivo",
                "type": "select",
                "entity": "client",
                "options": [
                    "Reabilitação", 
                    "Fortalecimento", 
                    "Flexibilidade", 
                    "Postura", 
                    "Emagrecimento", 
                    "Qualidade de Vida"
                ],
                "multiple": True,
                "required": False,
            },
            {
                "id": "plano",
                "name": "Plano",
                "type": "select",
                "entity": "client",
                "options": [
                    "Mensal 1x", 
                    "Mensal 2x", 
                    "Mensal 3x", 
                    "Trimestral", 
                    "Semestral", 
                    "Avulso"
                ],
                "required": False,
            },
        ]
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """
        Retorna fluxos de trabalho específicos para Pilates/Fitness.
        
        Returns:
            Lista de fluxos de trabalho.
        """
        return [
            {
                "id": "confirmacao_24h",
                "name": "Confirmação 24h antes",
                "description": "Envia mensagem de confirmação 24h antes da aula",
                "trigger": "schedule.before_24h",
                "enabled": True,
                "actions": [
                    {
                        "type": "send_message",
                        "template": "confirmacao_aula",
                        "channel": "whatsapp",
                    }
                ],
            },
            {
                "id": "lembrete_1h",
                "name": "Lembrete 1h antes",
                "description": "Envia lembrete 1h antes da aula",
                "trigger": "schedule.before_1h",
                "enabled": True,
                "actions": [
                    {
                        "type": "send_message",
                        "template": "lembrete_aula",
                        "channel": "whatsapp",
                    }
                ],
            },
            {
                "id": "recuperacao_alunos",
                "name": "Recuperação de Alunos",
                "description": "Envia mensagem para alunos inativos após 15 dias",
                "trigger": "client.inactive_days",
                "trigger_params": {"days": 15},
                "enabled": True,
                "actions": [
                    {
                        "type": "send_message",
                        "template": "recuperacao_aluno",
                        "channel": "whatsapp",
                    }
                ],
            },
            {
                "id": "aniversario_aluno",
                "name": "Aniversário de Aluno",
                "description": "Envia mensagem de aniversário",
                "trigger": "client.birthday",
                "enabled": True,
                "actions": [
                    {
                        "type": "send_message",
                        "template": "aniversario",
                        "channel": "whatsapp",
                    }
                ],
            },
        ]
