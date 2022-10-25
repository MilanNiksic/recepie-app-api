from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recepie

from recepie.serializers import RecepieSerializer


RECEPIE_URL = reverse('recepie:recepie-list')


def create_recepie(user, **params):
    defaults = {
        'title': 'Sample recepie title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample Description',
        'link': 'http://example.com/recepie.pdf',
    }
    defaults.update(params)

    recepie = Recepie.objects.create(user=user, **defaults)
    return recepie


class PiblicRecepieAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECEPIE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecepieAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@example.com',
            'testPassword123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recepies(self):
        create_recepie(user=self.user)
        create_recepie(user=self.user)

        res = self.client.get(RECEPIE_URL)

        recepies = Recepie.objects.all().order_by('-id')
        serializer = RecepieSerializer(recepies, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recepie_list_limited_to_user(self):
        local_user = get_user_model().objects.create_user(
            'testTwo@example.com',
            'testTwoPassword123'
        )
        create_recepie(user=local_user)
        create_recepie(user=local_user)
        create_recepie(user=self.user)

        res = self.client.get(RECEPIE_URL)

        recepies = Recepie.objects.filter(user=self.user)
        serializer = RecepieSerializer(recepies, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
