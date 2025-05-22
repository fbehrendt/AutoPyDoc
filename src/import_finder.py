import ast
import os
from pathlib import Path


class ImportFinder:
    def __init__(self, working_dir, debug=False):
        self.debug = debug
        self.import_lines = {}
        self.imports = {}
        self.aliases = {}
        self.working_dir = working_dir

    def add_file(self, filename):
        current_file_imports = []
        current_file_aliases = {}
        for node in ast.walk(ast.parse(open(file=filename, mode="r").read())):
            if isinstance(node, ast.Import):
                for item in node.names:  # TODO ast.alias
                    current_file_imports.append(item.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                for item in node.names:
                    if hasattr(item, "asname") and item.asname is not None:
                        if module is None:
                            current_file_aliases[item.asname] = item.name
                        else:
                            current_file_aliases[item.asname] = module + "." + item.name
                        current_file_imports.append(item.asname)
                    else:
                        if module is None:
                            current_file_imports.append(item.name)
                        else:
                            current_file_imports.append(module + "." + item.name)
        self.imports[filename] = current_file_imports
        self.aliases[filename] = current_file_aliases

    def resolve_external_call(self, call, filename, code_representer):
        # TODO resolve calls like class_obj_variable.class_method_call => get type of class_obj_variable
        # TODO resolve calls like self.class_obj.method, where class_obj was imported
        # TODO not working properly
        relevant_imports = self.imports[filename]
        matches = [
            current_import
            for current_import in relevant_imports
            # if call.split(".")[0] in current_import
            if current_import.endswith(call.split(".")[0])
        ]
        potential_code_objects = []
        for match in matches:
            for alias in self.aliases[filename].keys():
                if call.endswith(alias):
                    call = call.replace(alias, self.aliases[filename][alias])
                if match.endswith(alias):
                    match = match.replace(alias, self.aliases[filename][alias])
            potential_code_objects.extend(
                self.resolve_import_to_file(
                    import_statement=match,
                    source_file=filename,
                    code_representer=code_representer,
                )
            )
        matching_code_objects = [
            potential_code_object
            for potential_code_object in potential_code_objects
            if potential_code_object.name == call.split(".")[-1]
        ]
        if matching_code_objects is None or len(matching_code_objects) == 0:
            return None
        else:
            return matching_code_objects

    def resolve_import_to_file(self, import_statement, source_file, code_representer):
        import_statement = import_statement.split(".")
        repo_files = [
            os.path.join(dirpath, f)
            for (dirpath, dirnames, filenames) in os.walk(self.working_dir)
            for f in filenames
        ]
        repo_files = [file.split(".py")[0] for file in repo_files if file.endswith(".py")]
        repo_files = [file.split(self.working_dir)[1] for file in repo_files]
        repo_files = [
            [dir_part for dir_part in Path(file).parts if len(dir_part) > 0 and dir_part != "\\"]
            for file in repo_files
        ]
        source_file = source_file.split(self.working_dir)[1]
        source_file = [
            dir_part
            for dir_part in Path(source_file).parts
            if len(dir_part) > 0 and dir_part != "\\"
        ]

        potential_matches = []

        for split_path in repo_files:
            # go to same depth in repo
            i = 0
            while i < min(len(source_file), len(split_path)) and source_file[i] == split_path[i]:
                i += 1
            if i == len(source_file):
                raise CircularImportError("Import from the file that is importing")
            # match file part of import
            j = 0
            while (
                j < min(len(split_path) - i, len(import_statement))
                and split_path[i + j] == import_statement[j]
            ):
                j += 1
            if j > 0:
                filename = os.path.join(self.working_dir, *split_path)
                filename = filename + ".py"
                potential_matches.extend(code_representer.get_by_filename(filename))
        if len(potential_matches) > 0:
            return potential_matches
        else:
            return []


class CircularImportError(Exception):
    """
    Exception raised when circular imports are detected.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


if __name__ == "__main__":
    pass
