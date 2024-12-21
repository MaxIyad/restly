from django import template
from menu.models import MenuItem, MenuItemVariation

register = template.Library()

@register.filter
def lookup_menu_item(menu_item_id):
    try:
        return MenuItem.objects.get(id=menu_item_id).name
    except MenuItem.DoesNotExist:
        return "Unknown Menu Item"

@register.filter
def lookup_variation(variation_id):
    try:
        return MenuItemVariation.objects.get(id=variation_id).name
    except MenuItemVariation.DoesNotExist:
        return "Unknown Variation"
    

@register.filter
def sum_cart_prices(cart):
    return sum(item['price'] * item['quantity'] for item in cart)
