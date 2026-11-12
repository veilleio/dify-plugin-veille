import ast
import importlib
from pathlib import Path

import pytest
import requests
import yaml
from conftest import ROOT
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from provider.veille import VeilleProvider

KEY = "test-key-not-real"
BASE = "https://api.veille.io"
TOOLS = {
    "check_email": "VeilleCheckEmailTool",
    "qualify_email": "VeilleQualifyEmailTool",
    "check_domain": "VeilleCheckDomainTool",
    "check_ip": "VeilleCheckIpTool",
    "check_phone": "VeilleCheckPhoneTool",
    "check_vat": "VeilleCheckVatTool",
    "check_iban": "VeilleCheckIbanTool",
    "exchange_rates": "VeilleExchangeRatesTool",
}


def run(tool_cls, params):
    return list(tool_cls.from_credentials({"api_key": KEY}).invoke(params))


def texts(messages):
    return [m.message.text for m in messages if m.type.value == "text"]


def jsons(messages):
    return [m.message.json_object for m in messages if m.type.value == "json"]


def test_credentials_check_calls_the_free_endpoint(http):
    http.reply(200, {"credits": 100})
    VeilleProvider()._validate_credentials({"api_key": f" {KEY} "})
    call = http.calls[0]
    assert (call["method"], call["url"]) == ("GET", BASE + "/v1/usage")
    assert call["headers"]["x-api-key"] == KEY
    assert call["timeout"] == 30


def test_credentials_check_rejects_a_bad_key_without_showing_it(http):
    http.reply(401, {"error": f"Invalid API key {KEY}"})
    with pytest.raises(ToolProviderCredentialValidationError) as error:
        VeilleProvider()._validate_credentials({"api_key": KEY})
    assert "401" in str(error.value) and "not valid" in str(error.value)
    assert KEY not in str(error.value)


def test_credentials_check_needs_a_key(http):
    with pytest.raises(ToolProviderCredentialValidationError):
        VeilleProvider()._validate_credentials({"api_key": "  "})
    assert http.calls == []


def test_network_error_has_a_clear_message(http):
    http.raise_error(requests.ConnectionError(f"failed with {KEY}"))
    with pytest.raises(ToolProviderCredentialValidationError) as error:
        VeilleProvider()._validate_credentials({"api_key": KEY})
    assert "api.veille.io" in str(error.value) and KEY not in str(error.value)


def test_plugin_registers_provider_and_tools():
    from dify_plugin import DifyPluginEnv
    from dify_plugin.core.plugin_registration import PluginRegistration

    registration = PluginRegistration(DifyPluginEnv())
    assert registration.get_tool_provider_cls("veille").__name__ == "VeilleProvider"
    for tool, class_name in TOOLS.items():
        assert registration.get_tool_cls("veille", tool).__name__ == class_name


def test_each_tool_file_has_one_tool_class():
    for path in Path(ROOT, "tools").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert len([n for n in tree.body if isinstance(n, ast.ClassDef)]) == 1, path.name


def test_manifest_and_tool_files_agree():
    manifest = yaml.safe_load(Path(ROOT, "manifest.yaml").read_text(encoding="utf-8"))
    provider = yaml.safe_load(Path(ROOT, "provider/veille.yaml").read_text(encoding="utf-8"))
    assert manifest["version"] == manifest["meta"]["version"]
    assert manifest["author"] == provider["identity"]["author"] == "veilleio"
    assert manifest["network"]["domains"] == ["api.veille.io"]
    assert Path(ROOT, "_assets", manifest["icon"]).is_file()
    assert Path(ROOT, manifest["privacy"]).is_file()
    assert sorted(Path(f).stem for f in provider["tools"]) == sorted(TOOLS)
    for tool_file in provider["tools"]:
        tool = yaml.safe_load(Path(ROOT, tool_file).read_text(encoding="utf-8"))
        assert tool["identity"]["author"] == "veilleio"
        assert Path(ROOT, tool["extra"]["python"]["source"]).is_file()
        for param in tool["parameters"]:
            assert param["form"] in ("llm", "form")
            assert param["form"] == "form" or param.get("llm_description")


CASES = [
    (
        "check_email",
        "VeilleCheckEmailTool",
        {"email": " john@example.com "},
        "GET",
        "/v1/intelligence/email",
        {"query": "john@example.com"},
    ),
    (
        "qualify_email",
        "VeilleQualifyEmailTool",
        {"email": " john@example.com "},
        "GET",
        "/v1/intelligence/emailq",
        {"query": "john@example.com"},
    ),
    (
        "check_domain",
        "VeilleCheckDomainTool",
        {"domain": " example.com "},
        "GET",
        "/v1/intelligence/domain",
        {"query": "example.com"},
    ),
    ("check_ip", "VeilleCheckIpTool", {"ip": " 8.8.8.8 "}, "GET", "/v1/intelligence/ip", {"query": "8.8.8.8"}),
    (
        "check_phone",
        "VeilleCheckPhoneTool",
        {"phone": " +33612345678 "},
        "GET",
        "/v1/intelligence/phone",
        {"query": "+33612345678"},
    ),
    (
        "check_vat",
        "VeilleCheckVatTool",
        {"vat_number": " FR40303265045 "},
        "GET",
        "/v1/vat",
        {"query": "FR40303265045"},
    ),
    (
        "check_iban",
        "VeilleCheckIbanTool",
        {"iban": " FR7630006000011234567890189 "},
        "GET",
        "/v1/vat/iban",
        {"query": "FR7630006000011234567890189"},
    ),
    (
        "exchange_rates",
        "VeilleExchangeRatesTool",
        {"base": "USD", "symbols": "EUR,GBP"},
        "GET",
        "/v1/vat/rates",
        {"base": "USD", "symbols": "EUR,GBP"},
    ),
]


@pytest.mark.parametrize("tool, cls_name, sample, method, url, values", CASES)
def test_tool_request(http, tool, cls_name, sample, method, url, values):
    http.reply(200, {"ok": True, "items": [1, 2]})
    cls = getattr(importlib.import_module(f"tools.{tool}"), cls_name)
    messages = run(cls, sample)
    call = http.calls[0]
    assert (call["method"], call["url"]) == (method, BASE + url)
    sent = call["params"] if method in ("GET", "DELETE") else call["json"]
    assert sent == values
    assert call["headers"]["x-api-key"] == KEY
    assert '"ok": true' in texts(messages)[0]
    assert jsons(messages) == [{"ok": True, "items": [1, 2]}]


@pytest.mark.parametrize("tool, cls_name, sample, method, url, values", CASES)
def test_required_inputs_are_checked_before_any_request(http, tool, cls_name, sample, method, url, values):
    cls = getattr(importlib.import_module(f"tools.{tool}"), cls_name)
    tool_yaml = yaml.safe_load(Path(ROOT, f"tools/{tool}.yaml").read_text(encoding="utf-8"))
    if not any(p["required"] for p in tool_yaml["parameters"]):
        pytest.skip("no required input")
    messages = run(cls, {})
    assert "is required" in texts(messages)[0] and jsons(messages) == []
    assert http.calls == []


def test_errors_are_returned_as_text(http):
    tool, cls_name, sample = CASES[0][:3]
    cls = getattr(importlib.import_module(f"tools.{tool}"), cls_name)
    http.reply(402, {"error": "No credits"})
    assert texts(run(cls, sample)) == ["Veille error 402: Not enough credits. (No credits)"]


def test_timeout(http):
    tool, cls_name, sample = CASES[0][:3]
    cls = getattr(importlib.import_module(f"tools.{tool}"), cls_name)
    http.raise_error(requests.Timeout("slow"))
    assert texts(run(cls, sample)) == ["Veille did not answer in time. Try again."]
