import importlib.util
import os

_module_hook = None


def __getattr__(name, use_hook=True):
    from . import custom_operations_dir

    if use_hook and _module_hook:
        _module_hook(name)

    file = os.path.join(custom_operations_dir, name + ".py")
    if os.path.exists(file):
        try:
            spec = importlib.util.spec_from_file_location(name, file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Failed to load operation module {name}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f"Failed to load operation module {name}") from e
        return module
    raise AttributeError(f"module {__name__} has no attribute {name}")
