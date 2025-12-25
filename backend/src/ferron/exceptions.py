from fastapi import HTTPException, status

from src.ferron.constants import TemplateType
from src.ferron.schemas import TemplateConfig


class FerronException(HTTPException):
    pass


class GlobalConfigAlreadyExists(FerronException):
    def __init__(self, message: str = "Global configuration already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "global_config_already_exists",
                "message": message
            }
        )


class ConfigNotFound(FerronException):
    def __init__(self, config_type: str = "Configuration"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "config_not_found",
                "message": f"{config_type} not found"
            }
        )


class VirtualHostNameAlreadyExists(FerronException):
    def __init__(self, virtual_host_name: str = "<virtual_host_name>"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "virtual_host_name_already_exists",
                "message": f"Virtual host name '{virtual_host_name}' already exists"
            }
        )


class TemplateConfigAndTemplateTypeMismatch(HTTPException):
    def __init__(self, template_name: TemplateType, config: TemplateConfig):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "template_config_and_template_type_mismatch",
                "message": f"{config.__class__.__name__} is not compatible with template {template_name.value}"
            }
        )

class FileSystemException(HTTPException):
    pass

class FileNotFound(FileSystemException):
    def __init__(self, file_name: str)-> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "file_not_found",
                "message": f"File '{file_name}' not found"
            }
        )
