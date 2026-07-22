"""memory_unified — unified structured memory provider for Hermes.

Loader contract (plugins/memory/__init__.py): this file must textually
mention register_memory_provider or MemoryProvider, and may expose
register(ctx). Sibling top-level .py files are pre-registered as submodules.
"""
try:
    from .provider import UnifiedMemoryProvider
except ImportError:
    from provider import UnifiedMemoryProvider

__all__ = ["UnifiedMemoryProvider", "register"]


def register(ctx):
    ctx.register_memory_provider(UnifiedMemoryProvider())
