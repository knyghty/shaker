import ast
import importlib
import os

from .analyzer import Analyzer


seen_modules = set()
to_skip = {"importlib", "copy"}


def get_level(s):
    count = 0
    for char in s:
        if char != ".":
            return count
        count += 1


def recurse_modules(modules):
    for module in modules:
        print(module)
        if not hasattr(module, "__file__"):
            continue

        print(module.__file__)
        if module.__file__ not in seen_modules:
            with open(module.__file__, "r") as f:
                try:
                    tree = ast.parse(f.read())
                except UnicodeDecodeError as e:
                    print(f"{os.path.realpath(f.name)}: {e}")
                    continue

            seen_modules.add(module.__file__)
            analyzer = Analyzer()
            analyzer.visit(tree)
            imports = []
            for module_path in analyzer.imports:
                if module_path.startswith("."):
                    level = get_level(module_path)
                    package_name = module.__name__
                    package_name = ".".join(package_name.split(".")[:level])
                    try:
                        imports.append(importlib.import_module(module_path, package=package_name))
                    except ModuleNotFoundError:
                        # The last part might not be a module.
                        module_path = ".".join(module_path.split(".")[:-1])
                        try:
                            imports.append(importlib.import_module(module_path, package=package_name))
                        except ModuleNotFoundError:
                            print(f"Module not found: {package_name}.{module_path}")
                else:
                    try:
                        imports.append(importlib.import_module(module_path))
                    except ModuleNotFoundError:
                        try:
                            imports.append(importlib.import_module(".".join(module_path.split(".")[:-1])))
                        except ModuleNotFoundError:
                            print(f"Module not found: {module_path}")
                        except ValueError as e:
                            print(e)
                    except ImportError as e:
                        print(e)
            recurse_modules(imports)


def shake(entry_point):
    with open(entry_point, "r") as infile:
        tree = ast.parse(infile.read())
        seen_modules.add(os.path.realpath(infile.name))

    analyzer = Analyzer()
    analyzer.visit(tree)
    modules = [importlib.import_module(module) for module in analyzer.imports if module not in to_skip]
    recurse_modules(modules)
    return seen_modules
