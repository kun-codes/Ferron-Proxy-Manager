import asyncio
import os

import aiodocker
import aiofiles
import jinja2
from aiofiles import os as aiofiles_os

from src.config import settings
from src.ferron import schemas
from src.ferron.constants import SUB_CONFIG_PATH, ConfigFileLocation, TemplateType
from src.ferron.exceptions import FerronContainerNotFoundException, FileNotFound, TemplateConfigAndTemplateTypeMismatch
from src.ferron.schemas import (
    GlobalTemplateConfig,
    TemplateConfig,
    UpdateLoadBalancerConfig,
    UpdateReverseProxyConfig,
    UpdateStaticFileConfig,
)

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATES_DIR = os.path.join(_CURRENT_DIR, "templates")

environment = jinja2.Environment(loader=jinja2.FileSystemLoader(_TEMPLATES_DIR), enable_async=True)


async def render_template(template_type: TemplateType, template_config: TemplateConfig) -> str:
    template = environment.get_template(template_type.value)

    if template_type == TemplateType.GLOBAL_CONFIG:
        if not isinstance(template_config, GlobalTemplateConfig):
            raise TemplateConfigAndTemplateTypeMismatch(template_type, template_config)

        protocol_fields = {"is_h1_protocol_enabled", "is_h2_protocol_enabled", "is_h3_protocol_enabled"}

        global_config = template_config.model_dump(exclude=protocol_fields)

        is_h1_protocol_enabled: bool = template_config.is_h1_protocol_enabled
        is_h2_protocol_enabled: bool = template_config.is_h2_protocol_enabled
        is_h3_protocol_enabled: bool = template_config.is_h3_protocol_enabled

        global_config["protocols"] = []
        if is_h1_protocol_enabled:
            global_config["protocols"].append("h1")
        if is_h2_protocol_enabled:
            global_config["protocols"].append("h2")
        if is_h3_protocol_enabled:
            global_config["protocols"].append("h3")

        text = await template.render_async(**global_config)

        return text
    elif template_type == TemplateType.REVERSE_PROXY_CONFIG:
        if not isinstance(template_config, UpdateReverseProxyConfig):
            raise TemplateConfigAndTemplateTypeMismatch(template_type, template_config)

        # render_async() will ignore the id field in UpdateReverseProxyConfig
        text = await template.render_async(**template_config.model_dump())

        return text
    elif template_type == TemplateType.LOAD_BALANCER_CONFIG:
        if not isinstance(template_config, UpdateLoadBalancerConfig):
            raise TemplateConfigAndTemplateTypeMismatch(template_type, template_config)

        # render_async() will ignore the id field in UpdateLoadBalancerConfig
        text = await template.render_async(**template_config.model_dump())

        return text
    elif template_type == TemplateType.STATIC_FILE_CONFIG:
        if not isinstance(template_config, UpdateStaticFileConfig):
            raise TemplateConfigAndTemplateTypeMismatch(template_type, template_config)

        # render_async() will ignore the id field in UpdateStaticFileConfig
        text = await template.render_async(**template_config.model_dump())

        return text


async def write_config(path: str, text: str) -> None:
    """
    atomically writes `text` to file at `path` with 644 permissions
    """
    target_dir = os.path.dirname(path)

    await aiofiles_os.makedirs(target_dir, exist_ok=True)

    # atomic write by writing to a temp file and then atomically replacing the target file
    ## have to temp file in the same directory as target to avoid cross-device link errors
    async with aiofiles.tempfile.NamedTemporaryFile(mode="w+", delete=False, dir=target_dir) as temp_file:
        await temp_file.write(text)
        temp_file_name = temp_file.name

    ## permissions are being set to 644 so that ferron can read the config files
    await asyncio.to_thread(os.chmod, temp_file_name, 0o644)

    ## replace atomically
    await aiofiles_os.replace(temp_file_name, path)


async def read_config(path: str) -> str:
    try:
        async with aiofiles.open(path, "r") as f:
            return await f.read()
    except FileNotFoundError:
        raise FileNotFound(path)


async def write_global_config_to_file(global_config_data: schemas.GlobalTemplateConfig) -> None:
    """
    helper function to write global config to config file
    """
    # writing to config files
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    ## writing to global config
    rendered_config = await render_template(TemplateType.GLOBAL_CONFIG, global_config_data)

    await write_config(ConfigFileLocation.GLOBAL_CONFIG.value, rendered_config)

    ## checking if main config has include statement for global config and write to main config file if not
    has_include_statement = False
    for line in main_config_text.splitlines():
        if line.strip() == f'include "{ConfigFileLocation.GLOBAL_CONFIG.value}"':
            has_include_statement = True
            break

    if not has_include_statement:
        new_main_config_text = main_config_text + f'include "{ConfigFileLocation.GLOBAL_CONFIG.value}"\n'
        await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)


async def write_reverse_proxy_config_to_file(reverse_proxy_config_data: schemas.UpdateReverseProxyConfig) -> None:
    """
    helper function to write reverse proxy config to config file
    """
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    rendered_config = await render_template(TemplateType.REVERSE_PROXY_CONFIG, reverse_proxy_config_data)

    await write_config(f"{SUB_CONFIG_PATH}/{reverse_proxy_config_data.id}_reverse_proxy.kdl", rendered_config)

    has_include_statement = False
    for line in main_config_text.splitlines():
        if line.strip() == f'include "{SUB_CONFIG_PATH}/{reverse_proxy_config_data.id}_reverse_proxy.kdl"':
            has_include_statement = True
            break

    if not has_include_statement:
        new_main_config_text = (
            main_config_text + f'include "{SUB_CONFIG_PATH}/{reverse_proxy_config_data.id}_reverse_proxy.kdl"\n'
        )
        await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)


async def delete_reverse_proxy_config_from_file(reverse_proxy_id: int) -> None:
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    include_line = f'include "{SUB_CONFIG_PATH}/{reverse_proxy_id}_reverse_proxy.kdl"'

    lines = [line for line in main_config_text.splitlines() if line.strip() != include_line]
    new_main_config_text = "\n".join(lines) + ("\n" if lines else "")

    await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)

    await aiofiles_os.remove(f"{SUB_CONFIG_PATH}/{reverse_proxy_id}_reverse_proxy.kdl")


async def write_load_balancer_config_to_file(load_balancer_config_data: schemas.UpdateLoadBalancerConfig) -> None:
    """
    helper function to write load balancer config to config file
    """
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    rendered_config = await render_template(TemplateType.LOAD_BALANCER_CONFIG, load_balancer_config_data)

    await write_config(f"{SUB_CONFIG_PATH}/{load_balancer_config_data.id}_load_balancer.kdl", rendered_config)

    has_include_statement = False
    for line in main_config_text.splitlines():
        if line.strip() == f'include "{SUB_CONFIG_PATH}/{load_balancer_config_data.id}_load_balancer.kdl"':
            has_include_statement = True
            break

    if not has_include_statement:
        new_main_config_text = (
            main_config_text + f'include "{SUB_CONFIG_PATH}/{load_balancer_config_data.id}_load_balancer.kdl"\n'
        )
        await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)


async def delete_load_balancer_config_from_file(load_balancer_id: int) -> None:
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    include_line = f'include "{SUB_CONFIG_PATH}/{load_balancer_id}_load_balancer.kdl"'

    lines = [line for line in main_config_text.splitlines() if line.strip() != include_line]
    new_main_config_text = "\n".join(lines) + ("\n" if lines else "")

    await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)

    await aiofiles_os.remove(f"{SUB_CONFIG_PATH}/{load_balancer_id}_load_balancer.kdl")


async def write_static_file_config_to_file(static_file_config_data: schemas.UpdateStaticFileConfig) -> None:
    """
    helper function to write static file config to config file
    """
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    rendered_config = await render_template(TemplateType.STATIC_FILE_CONFIG, static_file_config_data)

    await write_config(f"{SUB_CONFIG_PATH}/{static_file_config_data.id}_static_file.kdl", rendered_config)

    has_include_statement = False
    for line in main_config_text.splitlines():
        if line.strip() == f'include "{SUB_CONFIG_PATH}/{static_file_config_data.id}_static_file.kdl"':
            has_include_statement = True
            break

    if not has_include_statement:
        new_main_config_text = (
            main_config_text + f'include "{SUB_CONFIG_PATH}/{static_file_config_data.id}_static_file.kdl"\n'
        )
        await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)


async def delete_static_file_config_from_file(static_file_id: int) -> None:
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    include_line = f'include "{SUB_CONFIG_PATH}/{static_file_id}_static_file.kdl"'

    lines = [line for line in main_config_text.splitlines() if line.strip() != include_line]
    new_main_config_text = "\n".join(lines) + ("\n" if lines else "")

    await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)

    await aiofiles_os.remove(f"{SUB_CONFIG_PATH}/{static_file_id}_static_file.kdl")


async def reload_ferron_service() -> None:
    docker = aiodocker.Docker()
    try:
        container = await docker.containers.get(settings.ferron_container_name)
        await container.kill(signal="SIGHUP")
    except aiodocker.exceptions.DockerError as e:
        if e.status == 404:
            raise FerronContainerNotFoundException(settings.ferron_container_name)
    finally:
        await docker.close()
