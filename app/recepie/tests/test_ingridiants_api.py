from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingridient
from recepie.serializers import IngridientSerializer


INGRIDIENTS_URL = reverse('recepie:ingridient-list')


def detail_url(ingridient_id):
    return reverse('recepie:ingridient-detail', args=[ingridient_id])


def create_user(email='test@example.com', password='testpassword123'):
    return get_user_model().objects.create_user(email, password)


class PublicIngridientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGRIDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngridientsApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingridients(self):
        Ingridient.objects.create(user=self.user, name="Kale")
        Ingridient.objects.create(user=self.user, name="Vanilla")

        res = self.client.get(INGRIDIENTS_URL)

        ingridients = Ingridient.objects.all().order_by('-name')
        serializer = IngridientSerializer(ingridients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingridients_limited_to_user(self):
        user2 = create_user(email='test2@example.com')
        Ingridient.objects.create(name='Kale', user=user2)
        ingridient = Ingridient.objects.create(name='Vanilla', user=self.user)

        res = self.client.get(INGRIDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingridient.name)
        self.assertEqual(res.data[0]['id'], ingridient.id)

    def test_ingridient_update(self):
        ingridient = Ingridient.objects.create(name='Kale', user=self.user)
        payload = {
            'name': 'Vanilla'
        }
        url = detail_url(ingridient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingridient.refresh_from_db()
        self.assertEqual(ingridient.name, payload['name'])

    def test_delete_ingridient(self):
        ingridient = Ingridient.objects.create(name='Desert', user=self.user)

        url = detail_url(ingridient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingridients = Ingridient.objects.filter(user=self.user)
        self.assertFalse(ingridients.exists())
