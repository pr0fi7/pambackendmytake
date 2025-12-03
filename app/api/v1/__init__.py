from fastapi import APIRouter

from .auth import api as auth_api
from .messages import api as messages_api
from .integrations import api as integrations_api
from .workflows import api as workflows_api
from .mcp import api as mcp_api


router = APIRouter(prefix="/v1")

router.include_router(auth_api.router, tags=["auth"])
router.include_router(messages_api.router, tags=["messages"])
router.include_router(integrations_api.router, tags=["integrations"])
router.include_router(workflows_api.router, tags=["workflows"])
router.include_router(mcp_api.router, tags=["mcp"])
