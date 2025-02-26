import ast
import os
from pathlib import Path

class ImportFinder():
    def __init__(self, working_dir):
        self.import_lines = {}
        self.imports = {}
        self.working_dir = working_dir
    
    def add_file(self, filename):
        current_file_imports = []
        for node in ast.walk(ast.parse(open(file=filename, mode='r').read())):
            if isinstance(node, ast.Import):
                for item in node.names:
                    current_file_imports.append(item.name)
            elif isinstance(node, ast.ImportFrom):          
                module = node.module
                if not self.debug: # TODO
                    if module is None:
                        continue
                for item in node.names:
                    current_file_imports.append(module + '.' + item.name)
        self.imports[filename] = current_file_imports

    def resolve_external_call(self, call, filename, code_representer):
        # TODO does ast resolve external calls as module.method, or as method with module stored separately?
        # TODO resolve calls like class_obj_variable.class_method_call => get type of class_obj_variable
        # TODO resolve calls like self.class_obj.method, where class_obj was imported
        relevant_imports = self.imports[filename]
        matches = [current_import for current_import in relevant_imports if call.split('.')[0] in current_import]
        matching_code_objects = []
        for match in matches:
            matching_code_objects = self.resolve_import_to_file(import_statement=match, source_file=filename, code_representer=code_representer)
        if matching_code_objects is None or len(matching_code_objects) == 0:
            return None
        else:
            return matching_code_objects

    def resolve_import_to_file(self, import_statement, source_file, code_representer):
        import_statement = import_statement.split('.')
        repo_files = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(self.working_dir) for f in filenames]
        repo_files = [file.split('.py')[0] for file in repo_files if file.endswith(".py")]
        repo_files = [file.split(self.working_dir)[1] for file in repo_files]
        repo_files = [[dir_part for dir_part in Path(file).parts if len(dir_part) > 0] for file in repo_files]
        source_file = source_file.split(self.working_dir)[1]
        source_file = [dir_part for dir_part in Path(source_file).parts if len(dir_part) > 0]
        
        potential_matches = []

        for split_path in repo_files:
            # go to same depth in repo
            i = 0
            while i < min(len(source_file), len(split_path)) and source_file[i] == split_path[i]:
                i += 1
            if i == len(source_file):
                raise Exception("Import from the file that is importing")
            # match file part of import
            j = 0
            while j < min(len(split_path)-i, len(import_statement)) and split_path[i+j] == import_statement[j]:
                j+=1
            if j > 0:
                filename = os.path.join(self.working_dir, *split_path)
                potential_matches.extend(code_representer.get_by_filename(filename)) # TODO
        if len(potential_matches) > 0:
            return potential_matches
        else:
            return None


if __name__ == "__main__":
    pass
