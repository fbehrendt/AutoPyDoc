import logging
from typing import Callable

from gpt_input import (
    GptInputCodeObject,
    GptOutput,
)
from models import ModelStrategyFactory


class GptInterface:
    def __init__(self, model_name: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = ModelStrategyFactory.create_strategy(
            model_name, device="cuda", context_size=2**13
        )

    def estimate(self, full_input: list[GptInputCodeObject]):
        pass  # TODO fill this method

    def process_batch(self, batch: list[GptInputCodeObject], callback: Callable[[GptOutput], None]):
        """Method to process batches of code using the gpt for which docstrings are to be generated/updated

        :param batch: list of dictionaries containing all information necessary for docstring generation
        :type batch: list[GptInputCodeObject]
        :param callback: the method that should be called with the result of one item of the batch. Has to be called once for every item in the batch
        :type callback: (GptOutput) -> None
        """
        self.logger.debug("Now working on:" + " ".join([str(item.id) for item in batch]))
        # TODO parallelize
        # flag developer comments
        # inferr missing arg/return types
        # generate exception descriptions (?)

        for current_code_object in batch:
            try:
                try:
                    # Only check docstring using gpt if a docstring is present
                    change_necessary = (
                        current_code_object.docstring is None
                        or len(current_code_object.docstring.strip()) == 0
                        or self.model.check_outdated(current_code_object)
                    )
                except Exception as e:
                    self.logger.fatal("Error while determining if change is necessary", exc_info=e)
                    raise e

                if not change_necessary:
                    output = GptOutput(
                        current_code_object.id,
                        no_change_necessary=True,
                        description=False,
                    )
                    callback(output)
                else:
                    try:
                        output = self.model.generate_docstring(current_code_object)
                    except Exception as e:
                        self.logger.fatal("Error while processing batch", exc_info=e)
                        raise e

                    callback(output)
            except KeyboardInterrupt as e:
                raise e
