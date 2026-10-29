"""Structured tool registry for COSKA agent tool calling."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolInput(BaseModel):
    """Base class for tool input validation."""
    pass


class ToolOutput(BaseModel):
    """Base class for tool output."""
    pass


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    name: str = ""
    description: str = ""
    input_model: Type[ToolInput] = ToolInput
    output_model: Type[ToolOutput] = ToolOutput
    
    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolResult:
        """Execute the tool with validated input."""
        pass
    
    def validate_input(self, data: Dict[str, Any]) -> ToolInput:
        """Validate input data against the input model."""
        return self.input_model(**data)
    
    def get_schema(self) -> Dict[str, Any]:
        """Get OpenAI-compatible function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema()
            }
        }


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool=tool.name)
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with their schemas."""
        return [tool.get_schema() for tool in self._tools.values()]
    
    async def execute(self, name: str, input_data: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name with validated input."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
                metadata={"available_tools": list(self._tools.keys())}
            )
        
        try:
            validated_input = tool.validate_input(input_data)
            result = await tool.execute(validated_input)
            logger.info("tool_executed", tool=name, success=result.success)
            return result
        except Exception as e:
            logger.error("tool_execution_failed", tool=name, error=str(e))
            return ToolResult(success=False, error=str(e))


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry