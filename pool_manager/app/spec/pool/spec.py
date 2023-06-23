from ..base.errors import SpecValidationError
from ..base.spec import spec_validate
from .errors import PoolSpecValidationError


class PoolSpec:

    _root: dict
    _taints: list
    _update_mode: bool

    def validate(self):
        try:
            spec_validate(self._root, "$pool")
        except SpecValidationError as e:
            raise PoolSpecValidationError(str(e)) from e

    def __init__(self, pool_body: dict):
        self._update_mode = False
        self._resources = pool_body["nodeTemplate"]["resourcesSpec"]
        self._taints = pool_body["nodeTaints"]
        self._root = pool_body

    def set_node_taint(self, key: str, value: str, effect: str):

        taint = {
            "key": key,
            "value": value,
            "effect": effect,
        }

        try:

            def name_exists(taint: str):
                return taint["key"] == key

            res: dict = next(filter(name_exists, self._taints))
            res.update(taint)

        except StopIteration:
            self._taints.append(taint)

    def set_node_group_name(self, name: str):
        self._root["name"] = name

    def set_node_group_size(self, cnt: int):
        self._root["scalePolicy"]["fixedScale"]["size"] = cnt

    def set_node_cpu(self, cores: int):
        self._resources["cores"] = str(cores)

    def set_node_ram(self, gb: int):
        self._resources["memory"] = str(gb * 2**30)

    def set_node_label(self, key: str, value: str):
        self._root["nodeLabels"][key] = value

    def set_update_mode(self):

        fields = [
            "nodeTemplate.resourcesSpec.cores",
            "nodeTemplate.resourcesSpec.memory",
            "scalePolicy.fixedScale.size",
        ]

        self._root["updateMask"] = ",".join(fields)
        self._root["version"] = None
        self._root["name"] = None
        self._update_mode = True

    def as_dict(self) -> dict:

        if __debug__:
            if not self._update_mode:
                self.validate()

        return self._root
