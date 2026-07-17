from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: dict  # JSON Schema properties
    required: list[str] = field(default_factory=list)  # required param names


# Tool registry
_registry: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    _registry[tool.name] = tool


def get_tool(name: str) -> Tool | None:
    return _registry.get(name)


def list_tools() -> list[dict]:
    """MCP format (inputSchema)."""
    return [
        {
            "name": t.name,
            "description": t.description,
            "inputSchema": {
                "type": "object",
                "properties": t.parameters,
                "required": t.required or list(t.parameters.keys()),
            },
        }
        for t in _registry.values()
    ]


def to_openai_schema() -> list[dict]:
    """OpenAI function calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": {
                    "type": "object",
                    "properties": t.parameters,
                    "required": t.required or list(t.parameters.keys()),
                },
            },
        }
        for t in _registry.values()
    ]


async def call_tool(name: str, arguments: dict) -> Any:
    tool = get_tool(name)
    if not tool:
        raise ValueError(f"Tool '{name}' not found")
    return await tool.func(**arguments)
