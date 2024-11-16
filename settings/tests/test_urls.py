from django.test import SimpleTestCase
from django.urls import reverse, resolve
from settings.views import settings_view

class TestUrls(SimpleTestCase):

    def test_settings_url_is_resolved(self):
        url = reverse('settings')
        self.assertEqual(resolve(url).func, settings_view)
    