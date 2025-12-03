import logging
import subprocess

from app.config import settings
from app.core.enums import VMScriptNameEnum
from app.models.auth.user import ReadUserModel
from app.repositories.auth.auth import AuthRepository


class ProvisionerService:
    """
    Service for provisioning cloud resources.
    """

    def __init__(self, auth_repository: AuthRepository) -> None:
        self._auth_repository = auth_repository

        self.vm_name = settings.VM_NAME
        self.vm_ip = settings.VM_IP
        self.vm_zone = settings.VM_ZONE
        self.scripts_location = settings.VM_SCRIPTS_LOCATION

    def _get_script_path(self, script: VMScriptNameEnum) -> str:
        return f"{self.scripts_location}/{script.value}"

    def _create_server_host(self, port: int) -> str:
        return f"http://{self.vm_ip}:{port}"

    @staticmethod
    def _get_backend_branch_name() -> str:
        if settings.ENVIRONMENT in ("local", "uat"):
            return "develop"
        return "main"

    def create_client(self, user_id: int, backend_port: int) -> None:
        # Use user_id as client name
        client_name = str(user_id)
        logging.info(f"Provisioning client: {client_name}")

        script_path = self._get_script_path(VMScriptNameEnum.CREATE_CLIENT)

        environment = settings.ENVIRONMENT

        command = [
            "gcloud", "compute",
            "ssh", self.vm_name,
            "--zone", self.vm_zone,
            "--command",
            f"sudo {script_path} {client_name} {backend_port} {environment}"
        ]

        logging.info(f"Executing command: {' '.join(command)}")
        self.run_ssh_command(command)

        self.update_user_server_host(user_id, backend_port)

        logging.info(f"Client {client_name} provisioned successfully.")

    def update_user_server_host(self, user_id: int, backend_port: int) -> None:
        user = ReadUserModel.model_validate(
            self._auth_repository.get(id=user_id)
        )
        if not user:
            logging.error(f"User with ID {user_id} not found.")
            return

        user.server_host = self._create_server_host(backend_port)

        self._auth_repository.update(
            user.model_dump(),
            id=user_id,
        )

        logging.info(f"Updated backend port for user ID {user_id} to {backend_port}.")

    @staticmethod
    def run_ssh_command(command: list[str]) -> str:
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)

            if result.stdout:
                logging.info("----- SSH STDOUT -----")
                logging.info(result.stdout)

            if result.stderr:
                logging.info("----- SSH STDERR -----")
                logging.info(result.stderr)

            logging.info("Command executed successfully.")
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error("----- SSH COMMAND FAILED -----")

            logging.error(f"Return Code: {e.returncode}")

            if e.stdout:
                logging.error("----- STDOUT -----")
                logging.error(e.stdout)

            if e.stderr:
                logging.error("----- STDERR -----")
                logging.error(e.stderr)

            logging.error(f"Exception: {e}")
            return ""
