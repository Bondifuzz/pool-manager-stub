from typing import Dict

C_K8S_LABEL_PFX = "bondifuzz"


def bondifuzz_key(s: str):
    return f"{C_K8S_LABEL_PFX}/{s}".replace("_", "-")


def parse_bondifuzz_labels(data: Dict[str, str]):

    result: Dict[str, str] = dict()
    prefix = f"{C_K8S_LABEL_PFX}/"
    prefix_len = len(prefix)

    for key, val in data.items():
        if key.startswith(prefix):
            new_key = key[prefix_len:].replace("-", "_")
            result.update({new_key: val})

    return result
