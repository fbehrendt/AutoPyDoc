def extract_methods_from_change_info(filename: str, change_start: int, change_length: int) -> list[dict[str|int]]:
    with open(filename, 'r') as f:
        content = f.readlines()

    line = change_start
    method_locations =  []
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
    if len(method_locations) > 0 and not "end" in method_locations[-1].keys():
        method_locations[-1]["end"] = len(content)-1

    methods = []
    for method_location in method_locations:
        methods.append({
            "type": "method", # TODO only if applicable
            "filename": filename,
            "start": method_location["start"],
            "end": method_location["end"],
            "content": "".join(content[method_location["start"]:method_location["end"]]),
            })

    return methods