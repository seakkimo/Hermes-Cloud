from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: dict  # JSON Schema


# Tool registry
_registry: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    _registry[tool.name] = tool


def get_tool(name: str) -> Tool | None:
    return _registry.get(name)


def list_tools() -> list[dict]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "inputSchema": {
                "type": "object",
                "properties": t.parameters,
                "required": list(t.parameters.keys()),
            },
        }
        for t in _registry.values()
    ]


async def call_tool(name: str, arguments: dict) -> Any:
    tool = get_tool(name)
    if not tool:
        raise ValueError(f"Tool '{name}' not found")
    return await tool.func(**arguments)
