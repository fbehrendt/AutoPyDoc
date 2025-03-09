def extract_methods_from_change_info(
    filename: str, change_start: int, change_length: int
) -> list[dict[str | int]]:
    """
    Extract start, end and content of methods affected by change information

    :param filename: filename
    :type filename: str
    :param change_start: line where the change begins
    :type change_start: int
    :param change_length: line length of the change
    :type change_length: int

    :return: list of method information as dict with keys type, filename, start, end, content
    :return type: list[dict[str|int]]
    """
    with open(filename, "r") as f:
        content = f.readlines()

    line = change_start
    method_locations = []
    # search for first affected method position
    while line >= 0:
        if content[line].lstrip().startswith("def "):
            break
        line -= 1
    if content[line].lstrip().startswith("def "):
        method_locations.append({"start": line})

    # search for additional affected method positions
    num_method = 0
    line = change_start + 1
    while line < len(content):
        if content[line].lstrip().startswith("def "):
            if len(method_locations) > 0:
                method_locations[-1]["end"] = line - 1
                # TODO detect and remove newlines before next method
                num_method += 1
            if line > change_length:
                break
            method_locations.append({"start": line})
            line += 2
            continue
        line += 1
    if len(method_locations) > 0 and "end" not in method_locations[-1].keys():
        method_locations[-1]["end"] = len(content)

    methods = []
    for method_location in method_locations:
        methods.append(
            {
                "type": "method",  # TODO only if applicable
                "filename": filename,
                "start": method_location["start"],
                "end": method_location["end"],
                "content": "".join(
                    content[method_location["start"] : method_location["end"]]
                ),
            }
        )

    return methods


def extract_classes_from_change_info(
    filename: str, change_start: int, change_length: int
) -> list[dict[str | int]]:
    """
    Extract start, end and content of classes affected by change information

    :param filename: filename
    :type filename: str
    :param change_start: line where the change begins
    :type change_start: int
    :param change_length: line length of the change
    :type change_length: int

    :return: list of class information as dict with keys type, filename, start, end, content
    :return type: list[dict[str|int]]
    """
    with open(filename, "r") as f:
        content = f.readlines()

    line = change_start
    class_locations = []
    # search for first affected method position
    while line >= 0:
        if content[line].lstrip().startswith("class "):
            break
        line -= 1
    if content[line].lstrip().startswith("class "):
        class_locations.append({"start": line})

    # search for additional affected method positions
    num_class = 0
    line = change_start + 1
    while line < len(content):
        if content[line].lstrip().startswith("class "):
            if len(class_locations) > 0:
                class_locations[-1]["end"] = line - 1
                # TODO detect and remove newlines before next method
                num_class += 1
            if line > change_length:
                break
            class_locations.append({"start": line})
            line += 2
            continue
        line += 1
    if len(class_locations) > 0 and "end" not in class_locations[-1].keys():
        class_locations[-1]["end"] = len(content)

    classes = []
    for class_location in class_locations:
        classes.append(
            {
                "type": "class",
                "filename": filename,
                "start": class_location["start"],
                "end": class_location["end"],
                "content": "".join(
                    content[class_location["start"] : class_location["end"]]
                ),
            }
        )

    return classes


def extract_module_from_change_info(
    filename: str, change_start: int, change_length: int
) -> list[dict[str | int]]:
    """
    Extract start, end and content of methods affected by change information

    :param filename: filename
    :type filename: str
    :param change_start: line where the change begins
    :type change_start: int
    :param change_length: line length of the change
    :type change_length: int

    :return: list of method information as dict with keys type, filename, start, end, content
    :return type: list[dict[str|int]]
    """
    with open(filename, "r") as f:
        content = f.readlines()
    return {
        "type": "method",  # TODO only if applicable
        "filename": filename,
        "start": 0,
        "end": len(content),
        "content": "".join(content),
    }
