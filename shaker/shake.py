import ast
import importlib
import logging
import os

from .analyzer import Analyzer


console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addHandler(console)

seen_modules = set()
to_skip = {"importlib"}


def _warn(module, package_name):
    if package_name:
        logger.warn("Module not found: %s.%s", package_name, module.path)
    else:
        logger.warn("Module not found: %s", module.path)


def _import_module(module, package_name=None):
    try:
        return importlib.import_module(module.path, package=package_name)
    except ModuleNotFoundError:
        # The last part might not be a module.
        module_path = ".".join(module.path.split(".")[:-1])
        if not module_path:
            _warn(module, package_name)
            return
        try:
            return importlib.import_module(module_path, package=package_name)
        except ModuleNotFoundError:
            _warn(module, package_name)
        except ImportError as e:
            logger.error(e)
    except ImportError as e:
        logger.error(e)


def recurse_modules(modules):
    for imported_module in modules:
        if not hasattr(imported_module, "__file__"):
            try:
                logger.warning("%s has no __file__", imported_module.__name__)
            except AttributeError:
                # Someties __name__ can be None?
                pass
            continue

        logger.info(imported_module.__file__)
        if imported_module.__file__ not in seen_modules:
            with open(imported_module.__file__, "r") as f:
                try:
                    tree = ast.parse(f.read())
                except UnicodeDecodeError:
                    # Probably a binary file, so just add it.
                    seen_modules.add(os.path.realpath(f.name))
                    continue

            seen_modules.add(imported_module.__file__)
            analyzer = Analyzer()
            analyzer.visit(tree)
            imports = []
            for module in analyzer.imports:
                if module.path.startswith("."):
                    try:
                        package_name = imported_module.__name__
                    except AttributeError:
                        logger.error("Cannot get name for %s, %s, %s", module, module.name, module.level)
                        continue
                    package_name = ".".join(package_name.split(".")[:module.level])
                    m = _import_module(module, package_name)
                    if m:
                        imports.append(m)
                else:
                    m = _import_module(module)
                    if m:
                        imports.append(m)
            recurse_modules(imports)


def shake(entry_point):
    with open(entry_point, "r") as infile:
        tree = ast.parse(infile.read())
        seen_modules.add(os.path.realpath(infile.name))

    analyzer = Analyzer()
    analyzer.visit(tree)
    modules = [_import_module(module) for module in analyzer.imports if module not in to_skip]
    recurse_modules(modules)
    return seen_modules
