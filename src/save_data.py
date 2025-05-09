from pathlib import Path
import os


def save_data(branch, code_type, code_name, code_id, content_type, data):
    folder = Path.cwd()
    folder = os.path.join(folder, "data", branch, code_type, code_name + "_" + str(code_id))
    if not os.path.exists(folder):
        os.makedirs(folder)
    new_filename = os.path.join(folder, content_type)
    new_filename += ".txt"
    with open(new_filename, mode="w") as f:
        f.write(data)
