from typing import Dict, Any

def get_str_value(data: Dict[str, Any], key: str) -> str:
    try:
        value = data.pop(key)
        if not isinstance(value, str):
            raise ValueError(f'{key} must be a string')

        return value
    except KeyError:
        raise ValueError(f'{key} is required')
