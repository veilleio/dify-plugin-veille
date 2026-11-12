from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from veille_api import call


class VeilleCheckIbanTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from call(self, tool_parameters, "GET", "/v1/vat/iban", {"iban": "query"}, required=("iban",))
