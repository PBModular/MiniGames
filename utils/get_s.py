import random

def get_s(s_map, key_path, **kwargs):
    keys = key_path.split('.')
    val = s_map
    try:
        for k in keys:
            val = val[k]
    except KeyError:
        return f"<{key_path} string not found>"
    except TypeError:
        return f"<{key_path} structure error>"

    if isinstance(val, list):
        chosen_string = random.choice(val)
    elif isinstance(val, str):
        chosen_string = val
    else:
        return str(val)

    try:
        return chosen_string.format(**kwargs)
    except KeyError:
        return chosen_string
