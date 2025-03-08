from collections.abc import Callable

from models import ModelStrategyFactory
from gpt_input import GptOutput, GptOutputMethod


class GptInterface:
    def __init__(self, model_name: str):
        self.model = ModelStrategyFactory.create_strategy(model_name, device="cpu")

    def process_batch(
        self, batch: list[dict[str, list | dict | str | bool]], callback: Callable
    ):
        """Method to process batches of code using the gpt for which docstrings are to be generated/updated

        :param batch: list of dictionaries containing all information necessary for docstring generation
        :type batch: list[dict[str, list|dict|str|bool]]
        :param callback: the method that should be called with the result of one item of the batch. Has to be called once for every item in the batch
        :type callback: Callable
        """
        print("Now working on:\n", "\n".join([str(item.id) for item in batch]))
        # TODO parallelize
        # flag developer comments
        # if only_comments_changed:
        # continue
        # generate description
        # inferr missing arg/return types
        # generate parameter descriptions
        # generate exception descriptions (?)

        change_necessary = True
        for item in batch:
            # change_necessary = not change_necessary
            if change_necessary:
                # option 1
                if item.code_type == "method":
                    return_type = None
                    if item.return_missing:
                        return_type = "MOCK return type"
                    mocked_result = GptOutputMethod(
                        id=item.id,
                        no_change_necessary=False,
                        description="MOCK This is a docstring description.",
                        parameter_types={
                            name: "MOCK type" for name in item.missing_parameters
                        },
                        parameter_descriptions={
                            param["name"]: "MOCK description for this parameter"
                            for param in item.parameters
                        },
                        exception_descriptions={
                            exception: "MOCK exception description"
                            for exception in item.exceptions
                        },
                        return_description="MOCK return type description",
                        return_missing=item.return_missing,
                        return_type=return_type,
                    )
                elif item.code_type == "class":
                    mocked_result = GptOutput(
                        id=item.id,
                        no_change_necessary=False,
                        description="MOCK This is a docstring description.",
                    )
                else:
                    raise NotImplementedError
            else:
                # option two
                mocked_result = GptOutput(
                    item.id, no_change_necessary=True, description=""
                )

            callback(mocked_result)
