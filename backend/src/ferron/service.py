from pathlib import Path
from typing import Any

import ckdl

class FerronConfig:
    def __init__(self, config_file: Path):
        self.config_file = config_file

        with open(self.config_file, "r", encoding="utf-8") as f:
            text = f.read()


        self.parsed_config = ckdl.parse(text, version=2)

    def get_config_block(self, config_block_name: str, is_snippet: bool = False) -> ckdl.Node | None:
        config_blocks = self.parsed_config.nodes

        for config_block in config_blocks:
            if is_snippet:
                if config_block.name != "snippet":
                    continue

                if config_block.args:
                    first_arg = config_block.args[0]
                    if first_arg == config_block_name:
                        return config_block

            else:
                if config_block.name == config_block_name:
                    return config_block

        return None

    def get_config_block_directive(self, config_block_name: str, directive_name: str, is_snippet: bool = False) -> list[ckdl.Node]:
        result: list[ckdl.Node] = []

        node = self.get_config_block(config_block_name, is_snippet=is_snippet)
        if node is None:
            return result

        for child in node.children:
            if child.name == directive_name:
                result.append(child)

        return result

    def get_directive_arguments(self, node_name: str, directive_name: str, is_snippet: bool = False) -> list[list[Any]]:
        result: list[list[Any]] = []
        directive_nodes = self.get_config_block_directive(node_name, directive_name, is_snippet=is_snippet)

        for directive_node in directive_nodes:
            result.append(directive_node.args)

        return result

    def get_directive_properties(self, node_name: str, directive_name: str, is_snippet: bool = False) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        directive_nodes = self.get_config_block_directive(node_name, directive_name, is_snippet=is_snippet)

        for directive_node in directive_nodes:
            result.append(directive_node.properties)

        return result
