def get_action_type(existing_item):
    if existing_item is not None:
        return "UPDATED"
    return 'NEW'


def get_item_changes(item, existing_item):
    diff_dictionary = {}

    all_keys = set(existing_item.keys()) | set(item.keys())

    for key in all_keys:
        existing_value = existing_item[key] if key in existing_item else None
        value = item[key] if key in item else None
        if value != existing_value:
            diff_dictionary[key] = {
                "old": existing_value,
                "new": value
            }

    return diff_dictionary
