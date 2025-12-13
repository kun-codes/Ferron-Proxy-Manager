from pathlib import Path
from typing import Any

import ckdl

class FerronConfig:
    def __init__(self, config_file: Path):
        self.config_file = config_file

        self.load_from_file()

    def load_from_file(self) -> None:
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

    def get_directive_arguments(self, config_block_name: str, directive_name: str, is_snippet: bool = False) -> list[list[Any]]:
        result: list[list[Any]] = []
        directive_nodes = self.get_config_block_directive(config_block_name, directive_name, is_snippet=is_snippet)

        for directive_node in directive_nodes:
            result.append(directive_node.args)

        return result

    def get_directive_properties(self, config_block_name: str, directive_name: str, is_snippet: bool = False) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        directive_nodes = self.get_config_block_directive(config_block_name, directive_name, is_snippet=is_snippet)

        for directive_node in directive_nodes:
            result.append(directive_node.properties)

        return result

    def set_config_block(self, config_block_name: str, node: ckdl.Node, is_snippet: bool = False) -> None:
        """Set or replace a config block. If it exists, replace it; otherwise, add it."""
        config_blocks = self.parsed_config.nodes

        for i, config_block in enumerate(config_blocks):
            if is_snippet:
                if config_block.name == "snippet" and config_block.args and config_block.args[0] == config_block_name:
                    config_blocks[i] = node
                    return
            else:
                if config_block.name == config_block_name:
                    config_blocks[i] = node
                    return

        # If not found, append the new node
        config_blocks.append(node)

    def save(self, output_file: Path | None = None) -> None:
        """Save the current config to a file. If no output_file is specified, overwrite the original file."""
        target_file = output_file if output_file is not None else self.config_file

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(self.parsed_config.dump(ckdl.EmitterOptions(version=2, identifier_mode=ckdl.IdentifierMode.quote_all_identifiers)))