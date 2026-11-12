from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from veille_api import call


class VeilleQualifyEmailTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from call(
            self, tool_parameters, "GET", "/v1/intelligence/emailq", {"email": "query"}, required=("email",)
        )
