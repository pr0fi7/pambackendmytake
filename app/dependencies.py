"""FastAPI dependency providers that integrate with the DI container"""

# This will be populated by src/main.py after container initialization
_container = None


def set_container(container):
    """Set the global container instance"""
    global _container
    _container = container


def get_auth_service():
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container.auth_service()


def get_message_service():
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container.message_service()


def get_workflow_service():
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container.workflow_service()


def get_provisioner_service():
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container.provisioner_service()


def get_integration_service():
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container.integration_service()


def get_mcp_service():
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container.mcp_service()


def get_auth_deps():
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container.auth_deps()
