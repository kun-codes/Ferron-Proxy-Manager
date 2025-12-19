import os

import jinja2
import aiofiles
import asyncio
from aiofiles import os as aiofiles_os

from src.ferron.schemas import GlobalTemplateConfig, TemplateConfig, CreateReverseProxyConfig, UpdateReverseProxyConfig
from src.ferron.constants import TemplateType
from src.ferron.exceptions import TemplateConfigAndTemplateTypeMismatch, FileNotFound

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATES_DIR = os.path.join(_CURRENT_DIR, "templates")

environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATES_DIR),
    enable_async=True
)

async def render_template(template_type: TemplateType, template_config: TemplateConfig)-> str:
    template = environment.get_template(template_type.value)

    if template_type == TemplateType.GLOBAL_CONFIG:
        if not isinstance(template_config, GlobalTemplateConfig):
            raise TemplateConfigAndTemplateTypeMismatch(template_type, template_config)

        protocol_fields = {
            "is_h1_protocol_enabled",
            "is_h2_protocol_enabled",
            "is_h3_protocol_enabled"
        }

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


async def write_config(path: str, text: str) -> None:
    """
    atomically writes `text` to file at `path` with 644 permissions
    """
    target_dir = os.path.dirname(path)
    
    await aiofiles_os.makedirs(target_dir, exist_ok=True)


    # atomic write by writing to a temp file and then atomically replacing the target file
    ## have to temp file in the same directory as target to avoid cross-device link errors
    async with aiofiles.tempfile.NamedTemporaryFile(
        mode="w+", 
        delete=False, 
        dir=target_dir
    ) as temp_file:
        await temp_file.write(text)
        temp_file_name = temp_file.name

    ## permissions are being set to 644 so that ferron can read the config files
    asyncio.to_thread(os.chmod, temp_file_name, 0o644)

    ## replace atomically
    await aiofiles_os.replace(temp_file_name, path)


async def read_config(path: str) -> str:
    try:
        async with aiofiles.open(path, "r") as f:
            return await f.read()
    except FileNotFoundError:
        raise FileNotFound(path)