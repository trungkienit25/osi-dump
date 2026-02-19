from typing import Type, List, Dict
from osi_dump.core.interfaces import IBatchHandler
from osi_dump.core.config import AppConfig

class HandlerRegistry:
    """
    Registry for resource batch handlers.
    Allows decoupling of handler registration from execution logic.
    """
    _handlers: List[Type[IBatchHandler]] = []

    @classmethod
    def register(cls, handler_class: Type[IBatchHandler]) -> Type[IBatchHandler]:
        """
        Decorator to register a class as a batch handler.
        """
        cls._handlers.append(handler_class)
        return handler_class

    @classmethod
    def get_active_handlers(cls, config: AppConfig) -> List[IBatchHandler]:
        """
        Instantiates and returns a list of handlers that are enabled in the provided config.
        """
        active_handlers = []
        for handler_cls in cls._handlers:
            # Instantiate the handler (assuming default no-arg constructor or we'd need a factory)
            # Since handlers might need dependencies later, we might move to a factory pattern.
            # For now, strict requirement says just instantiate.
            try:
                handler = handler_cls()
                if handler.is_enabled(config):
                    active_handlers.append(handler)
            except Exception:
                # If instantiation fails, we skip safe logic or log it?
                # For strictness, let's assume handlers must be instantiable.
                continue
                
        return active_handlers
