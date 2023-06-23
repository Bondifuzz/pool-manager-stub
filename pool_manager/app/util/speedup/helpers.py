from importlib import import_module


def try_import_module(name: str) -> bool:
    try:
        import_module(name)
        return True
    except ImportError:
        return False


def try_import_class(mod_name: str, cls_name: str) -> bool:
    try:
        mod = import_module(mod_name)
        getattr(mod, cls_name)
        return True
    except (ImportError, AttributeError):
        return False
