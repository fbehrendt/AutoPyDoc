import ast
import os
import pathlib

from code_representation import Code_obj, Class_obj, Method_obj, CodeRepresenter

code = CodeRepresenter()

class CodeParser():
    def __init__(self, code_representer):
        self.code_representer = code_representer

    def add_file(self, filename="src\experiments\\ast_tests.py"):
        dir = pathlib.Path().resolve()
        self.full_path = os.path.join(dir, filename)
        self.tree = ast.parse(open(self.full_path).read())
        self.parse_tree(tree=self.tree)

    def parse_tree(self, tree, parent = None):
        for node in ast.walk(tree):
            # ast.get_docstring(node, clean=True)
            # ast.get_source_segment(source, node.body[0])
            if isinstance(node, ast.Call):
                if hasattr(node.func, "id"):
                    called_func_name = node.func.id
                else:
                    called_func_name = node.func.attr
                print()
                print("Function call:", called_func_name)
                print("Called by:", parent)
                print()
            if isinstance(node, ast.FunctionDef):
                func_def_name = node.name
                print("Function def:", func_def_name)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body)
                self.code_representer.add_code_obj(method_obj)
                print("###Begin subtree of", func_def_name, "###")
                for sub_tree in node.body:
                    self.parse_tree(tree=sub_tree, parent=parent)
                print("###END subtree of", func_def_name, "###")
            if isinstance(node, ast.AsyncFunctionDef):
                func_def_name = node.name
                print("Async function def:", func_def_name)
                method_obj = Method_obj(name=func_def_name, filename=self.full_path, signature="signature mock", body=node.body)
                self.code_representer.add_code_obj(method_obj)
                print("###Begin subtree of", func_def_name, "###")
                for sub_tree in node.body:
                    self.parse_tree(tree=sub_tree, parent=func_def_name)
                print("###END subtree of", func_def_name, "###")
            if isinstance(node, ast.Lambda):
                print("Lambda")
            if isinstance(node, ast.ClassDef):
                class_def_name = node.name
                print("Class def:", class_def_name)
                class_obj = Class_obj(name=class_def_name, filename=self.full_path, signature="signature mock", body=node.body)
                self.code_representer.add_code_obj(class_obj)
                print("###Begin subtree of", class_def_name, "###")
                for sub_tree in node.body:
                    self.parse_tree(tree=sub_tree, parent=class_def_name)
                print("###END subtree of", class_def_name, "###")
            if isinstance(node, ast.Module):
                print("Module")
                print("###Begin subtree of Module###")
                for sub_tree in node.body:
                    self.parse_tree(sub_tree, parent="Module")
                print("###END subtree of Module###")

code_parser = CodeParser(CodeRepresenter())
code_parser.add_file()
print("finished")