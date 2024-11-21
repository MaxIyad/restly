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