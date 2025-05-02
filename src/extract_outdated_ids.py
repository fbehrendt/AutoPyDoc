import copy


def extract_code_affected_by_change(code_parser_old, code_parser_new):
    outdated_ids = set()
    # create ast from latest_commit state and current state
    # create code representation from latest_commit state and current state
    # while loop look for methods and classes that have no children in current state ast
    object_copy = copy.deepcopy(
        code_parser_new.code_representer.objects
    )  # prevent mutating objects in code_prepresenter
    next_code_objects = [
        code_object
        for code_object in object_copy.values()
        if (not hasattr(code_object, "class_ids") or len(code_object.class_ids) == 0)
        and (not hasattr(code_object, "method_ids") or len(code_object.method_ids) == 0)
    ]
    while len(next_code_objects) > 0:
        for new_code_object in next_code_objects:
            # look for those methods/classes in latest_commit state
            old_code_object = [
                code_object
                for code_object in code_parser_old.code_representer.objects.values()
                if code_object.name == new_code_object.name
                and code_parser_old.code_representer.get(code_object.parent_id).name
                == code_parser_new.code_representer.get(new_code_object.parent_id).name
            ]
            if len(old_code_object) > 1:
                raise NotImplementedError
            else:
                if len(old_code_object) == 1:
                    # compare them
                    if new_code_object.code == old_code_object[0].code:
                        continue
                # if they are different, or new, mark as outdated
                outdated_ids.add(new_code_object.id)
                new_code_object.outdated = True
                for code_object in object_copy.values():
                    if (
                        hasattr(code_object, "class_ids")
                        and new_code_object.id in code_object.class_ids
                    ):
                        print("class id")
                    if (
                        hasattr(code_object, "method_ids")
                        and new_code_object.id in code_object.method_ids
                    ):
                        print("method id")
                for parent_object in [
                    code_object
                    for code_object in object_copy.values()
                    if (
                        hasattr(code_object, "class_ids")
                        and new_code_object.id in code_object.class_ids
                    )
                    or (
                        hasattr(code_object, "method_ids")
                        and new_code_object.id in code_object.method_ids
                    )
                ]:
                    # remove those methods/classes from list of children of other objects
                    if new_code_object.id in parent_object.class_ids:
                        parent_object.class_ids.remove(new_code_object.id)
                    if new_code_object.id in parent_object.method_ids:
                        parent_object.method_ids.remove(new_code_object.id)
                    # remove those methods/classes code from code of objects that have them as children, unless it's a new method/class
                    if len(old_code_object) == 1:
                        parent_object.code = parent_object.code.replace(new_code_object.code, "")
                object_copy.pop(new_code_object.id)
                if len(old_code_object) == 1:
                    for parent_object in [
                        code_object
                        for code_object in code_parser_old.code_representer.objects.values()
                        if (
                            hasattr(code_object, "class_ids")
                            and old_code_object[0].id in code_object.class_ids
                        )
                        or (
                            hasattr(code_object, "method_ids")
                            and old_code_object[0].id in code_object.method_ids
                        )
                    ]:
                        # remove those methods/classes from list of children of other objects
                        if old_code_object[0].id in parent_object.class_ids:
                            parent_object.class_ids.remove(old_code_object[0].id)
                        if old_code_object[0].id in parent_object.method_ids:
                            parent_object.method_ids.remove(old_code_object[0].id)
                        # remove those methods/classes code from code of objects that have them as children
                        parent_object.code = parent_object.code.replace(old_code_object[0].code, "")
                        code_parser_old.code_representer.objects.pop(old_code_object[0].id)
        # update next code objects
        next_code_objects = [
            code_object
            for code_object in object_copy.values()
            if (not hasattr(code_object, "class_ids") or len(code_object.class_ids) == 0)
            and (not hasattr(code_object, "method_ids") or len(code_object.method_ids) == 0)
        ]
    return outdated_ids


if __name__ == "__main__":
    outdated_ids, code_representer_new = extract_code_affected_by_change(
        filename_old="C:\\Users\\Fabian\\Github\\AutoPyDoc\\src\\test_file_old.py",
        filename_new="C:\\Users\\Fabian\\Github\\AutoPyDoc\\src\\test_file_new.py",
    )
    print(outdated_ids)
    print()
