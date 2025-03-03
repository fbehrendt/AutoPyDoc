import logging

from .deepseek_r1_local import LocalDeepseekR1Strategy
from .model_strategy import DocstringModelStrategy


class ModelStrategyFactory:
    logger = logging.getLogger("ModelStrategyFactory")

    @staticmethod
    def create_strategy(model_type: str, **kwargs) -> DocstringModelStrategy:
        ModelStrategyFactory.logger.info("Creating model strategy [%s]", model_type)

        if model_type == "local_deepseek":
            return LocalDeepseekR1Strategy(**kwargs)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
