from django.test import SimpleTestCase
from django.urls import reverse, resolve
from inventory.views import ingredient_list

class TestUrls(SimpleTestCase):

    def test_inventory_url_is_resolved(self):
        url = reverse('inventory')
        self.assertEqual(resolve(url).func, ingredient_list)
    