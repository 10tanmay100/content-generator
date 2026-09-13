"""Shared FastAPI dependencies."""
from app.services.cosmos_service import CosmosService, cosmos_service


def get_cosmos() -> CosmosService:
    return cosmos_service
