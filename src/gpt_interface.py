from collections.abc import Callable
from functools import reduce

from models import ModelStrategyFactory


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
        print("Now working on:\n", "\n".join([item["id"] for item in batch]))
        # TODO parallelize
        # flag developer comments
        # if only_comments_changed:
        # continue
        # generate description
        # inferr missing arg/return types
        # generate parameter descriptions
        # generate exception descriptions (?)

        for item in batch:
            try:
                if "docstring" in item:
                    change_necessary = self.model.check_outdated(
                        item["code"], item["docstring"]
                    )
                else:
                    change_necessary = True

                if change_necessary:
                    # option 1
                    if item["type"] == "method":
                        generated_result = self.model.generate_docstring(item["code"])

                        parameter_types = reduce(
                            lambda r, dic: r.update(dic) or r,
                            map(
                                lambda r: {r["name"]: r["type"]},
                                generated_result["parameters"],
                            ),
                            {},
                        )
                        parameter_descriptions = reduce(
                            lambda r, dic: r.update(dic) or r,
                            map(
                                lambda r: {r["name"]: r["descriptions"]},
                                generated_result["parameters"],
                            ),
                            {},
                        )

                        return_description = generated_result["returns"]

                        mocked_result = {
                            "id": item["id"],
                            "no_change_necessary": False,
                            "description": generated_result["description"],
                            "parameter_types": {
                                name: parameter_types[name]
                                for name in item["missing_parameters"]
                            },
                            "parameter_descriptions": {
                                param["name"]: parameter_descriptions[param["name"]]
                                for param in item["parameters"]
                            },
                            "exception_descriptions": {
                                exception: "MOCK exception description"
                                for exception in item["exceptions"]
                            },
                            "return_description": return_description,
                        }
                        if item["return_missing"]:
                            mocked_result["return_type"] = "MOCK return type"
                    elif item["type"] == "class":
                        # TODO: change prompt to accomodate classes
                        mocked_result = {
                            "id": item["id"],
                            "no_change_necessary": False,
                            "description": "MOCK This is a docstring description.",
                        }
                    else:
                        raise NotImplementedError
                else:
                    # option two
                    mocked_result = {
                        "id": item["id"],
                        "no_change_necessary": True,
                    }

                callback(mocked_result)
            except Exception as e:
                print("Error in batch processing", e)
