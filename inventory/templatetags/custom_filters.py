from django import template

register = template.Library()

@register.filter
def get_form(forms_dict, ingredient_id):
    """Retrieve the form for the given ingredient ID from the dictionary."""
    return forms_dict.get(ingredient_id)


@register.filter
def abs_value(value):
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value
    

@register.filter
def dict_get(dictionary, key):
    """Safely get a value from a dictionary."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, None)
    return None

@register.filter
def empty_cells(count):
    """Generates the number of empty cells needed for a table."""
    try:
        empty_count = max(3 - int(count), 0)
        return range(empty_count)
    except (ValueError, TypeError):
        return range(0)


@register.filter
def subtract(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value
    
@register.filter
def subtract_length(value, count):
    try:
        return max(count - len(value), 0)
    except TypeError:
        return 0


@register.filter
def times(number):
    """Generate a range for iteration in templates."""
    try:
        return range(int(number))
    except (ValueError, TypeError):
        return range(0)

@register.filter
def length(value, count):
    """Subtract a value from a fixed count."""
    try:
        return max(count - len(value), 0)
    except TypeError:
        return 0


@register.filter
def add_float(value, arg):
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value
    

@register.filter
def multi(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0