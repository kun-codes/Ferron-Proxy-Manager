import os
import tempfile

import jinja2
import aiofiles
from aiofiles import os as aiofiles_os

from src.ferron.schemas import GlobalTemplateConfig, TemplateConfig
from src.ferron.constants import TemplateType
from src.ferron.exceptions import TemplateConfigAndTemplateTypeMismatch

environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    enable_async=True
)

async def render_template(template_type: TemplateType, template_config: TemplateConfig)-> str:
    template = environment.get_template(template_type.value)

    text = ""

    if template_type == TemplateType.GLOBAL_CONFIG:
        if not isinstance(template_config, GlobalTemplateConfig):
            raise TemplateConfigAndTemplateTypeMismatch(template_type, template_config)

        global_config = template_config.model_dump(
            exclude={
                GlobalTemplateConfig.is_h1_protocol_enabled,
                GlobalTemplateConfig.is_h2_protocol_enabled,
                GlobalTemplateConfig.is_h3_protocol_enabled
            }
        )

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

        text = await template.render_async(global_config=global_config)

        return text

    return text


async def write_config(path: str, text: str) -> None:
    """
    atomically writes `text` to file at `path`
    """
    async with aiofiles.tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
        await temp_file.write(text)

        aiofiles_os.replace(temp_file.name, path)
