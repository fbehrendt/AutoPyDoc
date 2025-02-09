import os
import pathlib
import re
import sys

file_path = os.path.dirname(os.path.realpath(__file__))
project_dir = str(pathlib.Path(file_path).parent.parent.absolute())
sys.path.append(project_dir) 

from src.get_context import CodeParser
from src.code_representation import CodeRepresenter

def resolve_variable_chain_by_file(code_representer, filename="src\experiments\\ast_tests.py", variable_chain="var_B.var_class_a", called_class_or_method="func_d"):
    dir = pathlib.Path().resolve()
    full_path = os.path.join(dir, filename)
    with open(full_path, 'r') as f:
        content = f.readlines()
        return resolve_variable_chain(code_representer=code_representer, content=content, variable_chain=variable_chain, called_class_or_method=called_class_or_method, full_path=full_path)

def resolve_variable_chain(code_representer, content, variable_chain, called_class_or_method, full_path):
        # currently fails to handle conditional assignments, as it returns when the first match is found
        for line in content:
            if line.lstrip().startswith(variable_chain + '.' + called_class_or_method):
                print("variable chain usage found in line", line)
            if line.lstrip().strip('self.').startswith(variable_chain.split('.')[0]):
                if line.lstrip().strip('self.').lstrip(variable_chain.split('.')[0]).lstrip().startswith('='):
                    print("variable chain assignment found in line", line)
                    identified_source = line.lstrip().strip('self.').lstrip(variable_chain.split('.')[0]).lstrip().lstrip('=').lstrip().split('#')[0].rstrip()
                    if '.' in identified_source.split('(')[0]: # case solve right side of assignment
                        # make sure the period is not part of a string
                        pattern = r'\w+'
                        string = identified_source.split('(')[0].split('.')
                        if re.fullmatch(pattern=pattern, string=string):
                            return resolve_variable_chain(code_representer=code_representer, content=content, variable_chain='.'.join(variable_chain.split('.')[1:], full_path=full_path), called_class_or_method=called_class_or_method)
                    elif '(' in identified_source: # case class or method call
                        identified_source = identified_source.split('(')[0]
                        # raise NotImplementedError
                        # TODO resolve method or class
                        # resolve import
                        # get code_obj
                        print("trying to get code_obj for", identified_source, "in line", line)
                        full_path = full_path # differs if imported
                        id_case_method = full_path + "_method_" + identified_source
                        id_case_class = full_path + "_class_" + identified_source
                        if id_case_method in code_representer.objects.keys():
                            code_obj = code_representer.objects[id_case_method]
                        elif id_case_class in code_representer.objects.keys():
                            code_obj = code_representer.objects[id_case_class]
                        else:
                            raise NotImplementedError
                        remaining_variable_chain = '.'.join(variable_chain.split('.')[1:])
                        if remaining_variable_chain != "":
                            result_id = resolve_variable_chain(code_representer=code_representer, content=code_obj.code.split('\n'), variable_chain='.'.join(variable_chain.split('.')[1:]), called_class_or_method=called_class_or_method, full_path=full_path)
                            return result_id
                        else:
                            return code_obj.id
                    else: # case assignment is not class or method call
                        raise NotImplementedError

if __name__ == "__main__":
    code_parser = CodeParser(CodeRepresenter(), debug=True)
    code_parser.add_file(filename="src\experiments\\ast_tests.py")
    code_parser.create_dependencies()
    result = resolve_variable_chain_by_file(code_representer=code_parser.code_representer)
    print(result)
    