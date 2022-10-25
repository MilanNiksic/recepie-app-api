from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recepie

from recepie.serializers import (
    RecepieSerializer,
    RecepieDetailSerializer,
)


RECEPIE_URL = reverse('recepie:recepie-list')


def detail_url(recepie_id):
    return reverse('recepie:recepie-detail', args=[recepie_id])


def create_recepie(user, **params):
    defaults = {
        'title': 'Sample recepie title',
        'time_minutes': '22',
        'price': Decimal('5.25'),
        'description': 'Sample Description',
        'link': 'http://example.com/recepie.pdf',
    }
    defaults.update(params)

    recepie = Recepie.objects.create(user=user, **defaults)
    return recepie


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PiblicRecepieAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECEPIE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecepieAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='test@example.com',
            password='testPassword123'
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
        local_user = create_user(
            email='testTwo@example.com',
            password='testTwoPassword123'
        )
        create_recepie(user=local_user)
        create_recepie(user=local_user)
        create_recepie(user=self.user)

        res = self.client.get(RECEPIE_URL)

        recepies = Recepie.objects.filter(user=self.user)
        serializer = RecepieSerializer(recepies, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recepie_detail(self):
        recepie = create_recepie(user=self.user)

        url = detail_url(recepie.id)
        res = self.client.get(url)

        serializer = RecepieDetailSerializer(recepie)
        self.assertEqual(res.data, serializer.data)

    def test_create_recepie(self):
        payload = {
            'title': 'Sample recepie title',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }
        res = self.client.post(RECEPIE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepie = Recepie.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recepie, k), v)
        self.assertEqual(recepie.user, self.user)

    def test_partial_update(self):
        original_link = 'https://example.com/recepie.pdf'
        recepie = create_recepie(
            user=self.user,
            title='sample recepie',
            link=original_link
        )

        payload = {
            'title': 'New recepie title'
        }
        url = detail_url(recepie.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recepie.refresh_from_db()
        self.assertEqual(recepie.title, payload['title'])
        self.assertEqual(recepie.link, original_link)
        self.assertEqual(recepie.user, self.user)

    def test_full_update(self):
        recepie = create_recepie(
            user=self.user,
            title='sample recepie',
            link='https://example.com/recepie.pdf',
            description='Sample recepie description'
        )

        payload = {
            'title': 'New title',
            'description': 'New description',
            'link': 'https://example.com/new-recepie.pdf',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }
        url = detail_url(recepie.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recepie.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recepie, k), v)
        self.assertEqual(recepie.user, self.user)

    def test_update_user_returns_error(self):
        new_user = create_user(email='user2@example.com', password='test123')
        recepie = create_recepie(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recepie.id)
        self.client.patch(url, payload)

        recepie.refresh_from_db()
        self.assertEqual(recepie.user, self.user)

    def test_delete_recepie(self):
        recepie = create_recepie(user=self.user)

        url = detail_url(recepie.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recepie.objects.filter(id=recepie.id).exists())

    def test_delete_other_users_recepie(self):
        new_user = create_user(email='user2@example.com', password='test123')
        recepie = create_recepie(user=new_user)

        url = detail_url(recepie.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recepie.objects.filter(id=recepie.id).exists())
