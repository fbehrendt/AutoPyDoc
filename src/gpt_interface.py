def send_batch(batch, callback):
    # TODO parallelize
    # flag developer comments
    # if only_comments_changed:
        # continue
    # generate description
    # inferr missing arg/return types
    # generate parameter descriptions
    # generate exception descriptions (?)
    change_necessary = False
    for item in batch:
        change_necessary = not change_necessary
        if change_necessary:
            # option 1
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
        else:
            # option two
            mocked_result = {
                "id": item["id"],
                "no_change_necessary": True,
            }
        callback(mocked_result)