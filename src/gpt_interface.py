from collections.abc import Callable

def send_batch(batch: list[dict[str, list|dict|str|bool]], callback: Callable):
    """Mock method to send batches of code to the gpt for which docstrings are to be generated/updated
    
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
    change_necessary = True
    for item in batch:
        # change_necessary = not change_necessary
        if change_necessary:
            # option 1
            if item["type"] == "method":
                mocked_result = {
                    "id": item["id"],
                    "no_change_necessary": False,
                    "description": "MOCK This is a docstring description.",
                    "parameter_types": {name: "MOCK type" for name in item["missing_parameters"]},
                    "parameter_descriptions": {param["name"]: "MOCK description for this parameter" for param in item["parameters"]},
                    "exception_descriptions": {exception: "MOCK exception description" for exception in item["exceptions"]},
                    "return_description": "MOCK return type description"
                }
                if item["return_missing"]:
                    mocked_result["return_type"] = "MOCK return type"
            elif item["type"] == "class":
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