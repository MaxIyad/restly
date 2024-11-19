from django.test import TestCase, RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages, constants as message_constants
from django.urls import reverse
from inventory.views import ingredient_list

class IngredientListViewTest(TestCase):
    def test_single_message_display(self):
        # Create a request using RequestFactory
        factory = RequestFactory()
        request = factory.get(reverse('inventory'))

        # Attach a session and messages storage to the request
        request.session = self.client.session
        messages_storage = FallbackStorage(request)
        setattr(request, '_messages', messages_storage)

        # Add multiple messages manually using FallbackStorage
        request._messages.add(message_constants.INFO, "First Message")
        request._messages.add(message_constants.INFO, "Second Message")

        # Simulate the view response
        response = ingredient_list(request)

        # Retrieve messages directly from the request
        messages = list(get_messages(request))

        # Assert that only the first message is displayed
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, "First Message")
