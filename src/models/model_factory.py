import logging

from .model_strategy import DocstringModelStrategy


class ModelStrategyFactory:
    logger = logging.getLogger("ModelStrategyFactory")

    @staticmethod
    def create_strategy(model_type: str, **kwargs) -> DocstringModelStrategy:
        ModelStrategyFactory.logger.debug("Creating model strategy [%s]", model_type)

        if model_type == "local_deepseek":
            from .strategy_deepseek_r1_local import LocalDeepseekR1Strategy

            return LocalDeepseekR1Strategy(**kwargs)
        if model_type == "ollama":
            from .strategy_deepseek_olama import OllamaDeepseekR1Strategy

            return OllamaDeepseekR1Strategy(**kwargs)
        if model_type == "gemini":
            from models.strategy_google_gemini import GoogleGeminiStrategy

            return GoogleGeminiStrategy(**kwargs)
        if model_type == "mock":
            from .strategy_mock import MockStrategy

            return MockStrategy()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
