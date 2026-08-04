"""Composition root for the version 1 API router."""

from fastapi import APIRouter

from app.api.v1.admin_api_tokens import router as admin_api_tokens_router
from app.api.v1.admin_audit import router as admin_audit_router
from app.api.v1.admin_blog import router as admin_blog_router
from app.api.v1.admin_contacts import router as admin_contacts_router
from app.api.v1.admin_experiences import router as admin_experiences_router
from app.api.v1.admin_health import router as admin_health_router
from app.api.v1.admin_media import router as admin_media_router
from app.api.v1.admin_pages import router as admin_pages_router
from app.api.v1.admin_projects import router as admin_projects_router
from app.api.v1.admin_site_configuration import router as admin_site_configuration_router
from app.api.v1.admin_skills import router as admin_skills_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.integration_resources import router as integration_resources_router
from app.api.v1.public_blog import router as public_blog_router
from app.api.v1.public_contacts import router as public_contacts_router
from app.api.v1.public_experiences import router as public_experiences_router
from app.api.v1.public_media import router as public_media_router
from app.api.v1.public_pages import router as public_pages_router
from app.api.v1.public_projects import router as public_projects_router
from app.api.v1.public_site_configuration import router as public_site_configuration_router
from app.api.v1.public_skills import router as public_skills_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(admin_health_router)
api_v1_router.include_router(admin_media_router)
api_v1_router.include_router(admin_site_configuration_router)
api_v1_router.include_router(admin_skills_router)
api_v1_router.include_router(admin_experiences_router)
api_v1_router.include_router(admin_projects_router)
api_v1_router.include_router(admin_blog_router)
api_v1_router.include_router(admin_api_tokens_router)
api_v1_router.include_router(admin_audit_router)
api_v1_router.include_router(admin_contacts_router)
api_v1_router.include_router(admin_pages_router)
api_v1_router.include_router(public_site_configuration_router)
api_v1_router.include_router(public_skills_router)
api_v1_router.include_router(public_experiences_router)
api_v1_router.include_router(public_media_router)
api_v1_router.include_router(public_projects_router)
api_v1_router.include_router(public_blog_router)
api_v1_router.include_router(public_contacts_router)
api_v1_router.include_router(public_pages_router)
api_v1_router.include_router(integration_resources_router)
