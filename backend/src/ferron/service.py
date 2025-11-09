from pathlib import Path

import ckdl

class FerronConfig:
    def __init__(self, config_file: Path):
        self.config_file = config_file

        with open(self.config_file, "r", encoding="utf-8") as f:
            text = f.read()


        self.parsed_config = ckdl.parse(text, version=2)

    def find_node(self, node_name: str, is_snippet: bool = False) -> ckdl.Node | None:
        nodes = self.parsed_config.nodes

        for node in nodes:
            if is_snippet:
                if node.name != "snippet":
                    continue

                if node.args:
                    first_arg = node.args[0]
                    if first_arg == node_name:
                        return node

            else:
                if node.name == node_name:
                    return node

        return None

    def get_node_directive(self, node_name: str, directive_name: str, is_snippet: bool = False) -> list[ckdl.Node]:
        result: list[ckdl.Node] = []

        node = self.find_node(node_name, is_snippet=is_snippet)
        if node is None:
            return result

        for child in node.children:
            if child.name == directive_name:
                result.append(child)

        return result
