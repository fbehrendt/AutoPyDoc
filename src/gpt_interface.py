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
        self.model = ModelStrategyFactory.create_strategy(model_name, device="cuda")

        self.debug_abort = False

    def process_batch(
        self, batch: list[GptInputCodeObject], callback: Callable[[GptOutput], None]
    ):
        """Method to process batches of code using the gpt for which docstrings are to be generated/updated

        :param batch: list of dictionaries containing all information necessary for docstring generation
        :type batch: list[GptInputCodeObject]
        :param callback: the method that should be called with the result of one item of the batch. Has to be called once for every item in the batch
        :type callback: (GptOutput) -> None
        """
        self.logger.info(
            "Now working on:\n" + "\n".join([str(item.id) for item in batch])
        )
        # TODO parallelize
        # flag developer comments
        # if only_comments_changed:
        # continue
        # generate description
        # inferr missing arg/return types
        # generate parameter descriptions
        # generate exception descriptions (?)

        for current_code_object in batch:
            # if self.debug_abort:
            #     self.logger.info("Debugging, aborting!")
            #     break

            try:
                change_necessary = (
                    current_code_object.docstring is None
                    or self.model.check_outdated(current_code_object)
                )

                if not change_necessary:
                    no_change_necessary_output = GptOutput(
                        current_code_object.id, no_change_necessary=True, description=""
                    )
                    callback(no_change_necessary_output)
                else:
                    generated_output = self.model.generate_docstring(
                        current_code_object
                    )

                    callback(generated_output)

            except Exception as e:
                self.logger.exception("Error while processing batch", exc_info=e)
                self.debug_abort = True
