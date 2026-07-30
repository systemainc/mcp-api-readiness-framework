from .anthropic_provider import AnthropicProvider

PROVIDER_REGISTRY = {
    "anthropic": AnthropicProvider,
}


def build_provider(provider_type: str, options: dict):
    cls = PROVIDER_REGISTRY.get(provider_type)
    if cls is None:
        raise ValueError(
            f"Unknown legibility provider '{provider_type}'. Known: {sorted(PROVIDER_REGISTRY)}"
        )
    return cls(options)
