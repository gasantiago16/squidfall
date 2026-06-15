"""Flexible LLM provider factory for the inference agent.

The agent code never names a provider — it calls build_llm(), which selects and
constructs a chat model from environment config. The same agent runs against:

  LLM_PROVIDER=ollama         -> local Ollama            (dev default)
  LLM_PROVIDER=openai         -> any OpenAI-compatible endpoint (gateway/vLLM/LiteLLM)
  LLM_PROVIDER=azure_openai   -> Azure OpenAI (API key, or Entra ID incl. Gov cloud)

Switching providers is deploy-time config only — no code change. All three
return a tool-capable BaseChatModel, so create_react_agent works unchanged.
"""

from os import getenv


def _temperature() -> float:
    return float(getenv("LLM_TEMPERATURE", "0"))


def _require(provider: str, *names: str) -> None:
    missing = [n for n in names if not getenv(n)]
    if missing:
        raise RuntimeError(
            f"LLM_PROVIDER={provider} requires these env vars: {', '.join(missing)}"
        )


def _build_ollama():
    """Local Ollama via the NATIVE API (not /v1 — tools+streaming break there)."""
    from langchain.chat_models import init_chat_model

    return init_chat_model(
        getenv("LLM_MODEL", "qwen2.5"),
        model_provider="ollama",
        base_url=getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
        temperature=_temperature(),
        num_ctx=int(getenv("OLLAMA_NUM_CTX", "8192")),
    )


def _build_openai():
    """Any OpenAI-compatible endpoint (internal gateway, vLLM, LiteLLM, ...)."""
    from langchain.chat_models import init_chat_model

    _require("openai", "OPENAI_BASE_URL", "LLM_MODEL")
    return init_chat_model(
        getenv("LLM_MODEL"),
        model_provider="openai",
        base_url=getenv("OPENAI_BASE_URL"),
        api_key=getenv("OPENAI_API_KEY", "not-needed"),
        temperature=_temperature(),
    )


def _build_azure_openai():
    """Azure OpenAI. API-key auth if AZURE_OPENAI_API_KEY is set; otherwise
    Entra ID (service principal) — supports the Gov cloud via AZURE_AUTHORITY_HOST
    + AZURE_TOKEN_SCOPE."""
    from langchain_openai import AzureChatOpenAI

    _require("azure_openai", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT")
    kwargs = dict(
        azure_endpoint=getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version=getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        temperature=_temperature(),
    )

    api_key = getenv("AZURE_OPENAI_API_KEY")
    if api_key:
        return AzureChatOpenAI(api_key=api_key, **kwargs)

    # No key -> Entra ID (AAD) service-principal auth.
    _require("azure_openai", "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")
    from azure.identity import ClientSecretCredential, get_bearer_token_provider

    cred_kwargs = dict(
        tenant_id=getenv("AZURE_TENANT_ID"),
        client_id=getenv("AZURE_CLIENT_ID"),
        client_secret=getenv("AZURE_CLIENT_SECRET"),
    )
    authority = getenv("AZURE_AUTHORITY_HOST")  # e.g. https://login.microsoftonline.us (Gov)
    if authority:
        cred_kwargs["authority"] = authority

    credential = ClientSecretCredential(**cred_kwargs)
    scope = getenv("AZURE_TOKEN_SCOPE", "https://cognitiveservices.azure.com/.default")
    token_provider = get_bearer_token_provider(credential, scope)
    return AzureChatOpenAI(azure_ad_token_provider=token_provider, **kwargs)


_PROVIDERS = {
    "ollama": _build_ollama,
    "openai": _build_openai,
    "azure_openai": _build_azure_openai,
}


def build_llm():
    """Build the chat model selected by LLM_PROVIDER (default: ollama)."""
    provider = getenv("LLM_PROVIDER", "ollama").strip().lower()
    builder = _PROVIDERS.get(provider)
    if builder is None:
        raise RuntimeError(
            f"unknown LLM_PROVIDER={provider!r}; expected one of {sorted(_PROVIDERS)}"
        )
    return builder()
