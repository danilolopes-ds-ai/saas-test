"""
Router principal da API.
Agrega todos os controllers em um único router.
"""
from fastapi import APIRouter

from app.api.controllers import (
    appointment_controller,
    client_controller,
    faq_controller,
    health_controller,
    professional_controller,
    user_controller,
)


# Router principal, sem prefixo (será adicionado na app)
api_router = APIRouter()

# Adicionar routers dos controllers
api_router.include_router(
    health_controller.router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    user_controller.router,
    prefix="/users",
    tags=["Usuários"],
)

api_router.include_router(
    client_controller.router,
    prefix="/clients",
    tags=["Clientes"],
)

api_router.include_router(
    professional_controller.router,
    prefix="/professionals",
    tags=["Profissionais"],
)

api_router.include_router(
    appointment_controller.router,
    prefix="/appointments",
    tags=["Agendamentos"],
)

api_router.include_router(
    faq_controller.router,
    prefix="/faq",
    tags=["FAQ"],
)
