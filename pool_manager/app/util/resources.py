"""
## Resource strings conversion module
"""

import re

CPU_REGEX = re.compile(r"^(\d+|\d+.\d+)([mn])?$")
RAM_REGEX = re.compile(r"^(\d+|\d+.\d+)([KMGTPE]|Ki|Mi|Gi|Ti|Pi|Ei)?$")

RAM_UNITS = {
    None: 1,
    "K": 10**3,
    "M": 10**6,
    "G": 10**9,
    "T": 10**12,
    "P": 10**15,
    "E": 10**18,
    "Ki": 2**10,
    "Mi": 2**20,
    "Gi": 2**30,
    "Ti": 2**40,
    "Pi": 2**50,
    "Ei": 2**60,
}

CPU_UNITS = {
    None: 1,
    "m": 10**-3,
    "n": 10**-9,
}


class CpuResources:
    def from_string(value: str, dst_units="m") -> int:

        match = CPU_REGEX.match(value)
        if not match:
            raise ValueError(f"Invalid resource: {value}")

        value, src_units = match.groups()

        try:
            dst_unit = CPU_UNITS[dst_units]
            src_unit = CPU_UNITS[src_units]
        except KeyError as e:
            raise ValueError(f"Invalid CPU unit: {e}")

        if src_unit == dst_unit:
            return int(value)

        return int(round(float(value) * src_unit / dst_unit, 6))

    def to_string(value: int, src_units="m", dst_units="m") -> str:

        try:
            src_unit = CPU_UNITS[src_units]
            dst_unit = CPU_UNITS[dst_units]
        except KeyError as e:
            raise ValueError(f"Invalid CPU unit: {e}")

        if src_unit == dst_unit:
            return f"{value}{dst_units}"

        return f"{int(round(value * src_unit / dst_unit, 6))}{dst_units}"


class RamResources:
    def from_string(value: str, dst_units="Mi") -> int:

        match = RAM_REGEX.match(value)
        if not match:
            raise ValueError(f"Invalid resource: {value}")

        value, src_units = match.groups()

        try:
            dst_unit = RAM_UNITS[dst_units]
            src_unit = RAM_UNITS[src_units]
        except KeyError as e:
            raise ValueError(f"Invalid RAM unit: {e}")

        if src_unit == dst_unit:
            return int(value)

        return int(round(float(value) * src_unit / dst_unit, 6))

    def to_string(value: int, src_units="Mi", dst_units="Mi") -> str:

        try:
            src_unit = RAM_UNITS[src_units]
            dst_unit = RAM_UNITS[dst_units]
        except KeyError as e:
            raise ValueError(f"Invalid RAM unit: {e}")

        if src_unit == dst_unit:
            return f"{value}{dst_units}"

        return f"{int(round(value * src_unit / dst_unit, 6))}{dst_units}"
