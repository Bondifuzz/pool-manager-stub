from typing import Any, List, Optional

import yaml

from .errors import *


def _spec_parse_key(key: str) -> List[str]:

    if key.startswith("."):
        key = key[1:]

    key_list = key.split(".")
    if "" in key_list:
        raise UsageError("Invalid key. Please, use '.a.b.c' format")

    assert len(key_list) > 0
    return key_list


def _spec_lookup(
    keys: List[str],
    root: Optional[dict],
):
    def assume_dict_lookup(dict_data: Any, key: str):

        if not isinstance(dict_data, dict):
            msg = f"Item '{key}' is not a dict"
            raise SpecParseError(".".join(keys), msg)

        try:
            res = dict_data[key]
        except KeyError:
            msg = f"Item '{key}' was not found"
            raise SpecParseError(".".join(keys), msg)

        return res

    res = root
    for key in keys:
        res = assume_dict_lookup(res, key)

    return res


def spec_get_item(root: dict, key: str) -> Any:
    return _spec_lookup(_spec_parse_key(key), root)


def spec_set_item(root: dict, key: str, value: Any) -> Any:

    key_list = _spec_parse_key(key)
    last_key = key_list[-1]
    key_list = key_list[:-1]

    res = _spec_lookup(key_list, root)
    res[last_key] = value


def spec_load(template_file: str):

    try:
        with open(template_file) as f:
            res = yaml.safe_load(f)

    except FileNotFoundError as e:
        raise SpecLoadError(template_file) from e

    if not isinstance(res, dict):
        msg = "Root node must be dict"
        raise SpecParseError("<root>", msg)

    return res


def spec_validate(item: Any, item_name: str):

    if isinstance(item, list):
        _list: list = item
        for i, val in enumerate(_list):
            spec_validate(val, f"{item_name}[{i}]")

    elif isinstance(item, dict):
        _dict: dict = item
        for name, val in _dict.items():
            spec_validate(val, f"{item_name}.{name}")

    else:
        if item is None:
            raise SpecValidationError(item_name)
