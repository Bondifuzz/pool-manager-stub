from copy import deepcopy
from typing import Any, Optional

from ..base.errors import SpecLoadError, SpecParseError
from ..base.spec import spec_get_item, spec_load, spec_set_item
from .errors import PoolSpecLoadError, PoolSpecParseError
from .spec import PoolSpec


class PoolSpecTemplate:

    _root: dict
    _container: dict

    def _spec_get(self, key: str, root: Optional[dict] = None) -> Any:
        return spec_get_item(root or self._root, key)

    def _spec_set(self, key: str, value: Any, root: Optional[dict] = None) -> Any:
        return spec_set_item(root or self._root, key, value)

    def _spec_init_node_group_name(self):
        self._spec_get("name")

    def _spec_init_node_resources(self):
        self._spec_get(".nodeTemplate.resourcesSpec.cores")
        self._spec_get(".nodeTemplate.resourcesSpec.memory")

    def _spec_init_node_group_size(self):
        self._spec_get(".scalePolicy.fixedScale.size")

    def _spec_init_node_taints(self):

        key = "nodeTaints"
        taints = self._spec_get(key)

        if taints is not None:
            if not isinstance(taints, list):
                msg = "Item 'taints' must be list"
                raise SpecParseError(key, msg)
        else:
            self._spec_set(key, list())

    def _spec_init_node_labels(self):

        key = "nodeLabels"
        labels = self._spec_get(key)

        if labels is not None:
            if not isinstance(labels, dict):
                msg = "Item 'labels' must be dict"
                raise SpecParseError(key, msg)
        else:
            self._spec_set(key, dict())

    def _spec_init(self):
        self._spec_init_node_group_name()
        self._spec_init_node_group_size()
        self._spec_init_node_resources()
        self._spec_init_node_labels()
        self._spec_init_node_taints()

    def __init__(self, template_file: str):

        try:
            self._root = spec_load(template_file)
            self._spec_init()

        except SpecLoadError as e:
            raise PoolSpecLoadError(str(e)) from e

        except SpecParseError as e:
            raise PoolSpecParseError(str(e)) from e

    def copy(self) -> PoolSpec:
        return PoolSpec(deepcopy(self._root))
