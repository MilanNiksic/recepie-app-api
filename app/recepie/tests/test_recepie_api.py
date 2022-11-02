from decimal import Decimal

import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingridient,
    Recepie,
    Tag,
)

from recepie.serializers import (
    RecepieSerializer,
    RecepieDetailSerializer,
)


RECEPIE_URL = reverse('recepie:recepie-list')


def detail_url(recepie_id):
    return reverse('recepie:recepie-detail', args=[recepie_id])


def image_upload_url(recipe_id):
    return reverse('recepie:recepie-upload-image', args=[recipe_id])


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

    def test_create_recepie_with_new_tags(self):
        payload = {
            'title': 'Curry',
            'link': 'https://example.com/curry.pdf',
            'time_minutes': 20,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }

        res = self.client.post(RECEPIE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepies = Recepie.objects.filter(user=self.user)
        self.assertEqual(recepies.count(), 1)
        recepie = recepies[0]
        self.assertEqual(recepie.tags.count(), 2)
        for tag in payload['tags']:
            exists = recepie.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recepie_with_existing_tags(self):
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Brakefast'}],
        }
        res = self.client.post(RECEPIE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepies = Recepie.objects.filter(user=self.user)
        self.assertEqual(recepies.count(), 1)
        recepie = recepies[0]
        self.assertEqual(recepie.tags.count(), 2)
        self.assertIn(tag_indian, recepie.tags.all())
        for tag in payload['tags']:
            exists = recepie.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recepie = create_recepie(user=self.user)
        payload = {
            'tags': [{'name': 'Indian'}, {'name': 'Brakefast'}],
        }
        url = detail_url(recepie.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.filter(user=self.user)
        self.assertEqual(new_tag[0], recepie.tags.first())

    def test_update_recepie_assign_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user, name='Brakefast')
        recepie = create_recepie(user=self.user)
        recepie.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recepie.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recepie.tags.all())
        self.assertNotIn(tag_breakfast, recepie.tags.all())

    def test_clear_recepie_tags(self):
        tag_breakfast = Tag.objects.create(user=self.user, name='Brakefast')
        recepie = create_recepie(user=self.user)
        recepie.tags.add(tag_breakfast)

        payload = {'tags': []}
        url = detail_url(recepie.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(tag_breakfast, recepie.tags.all())
        self.assertEqual(recepie.tags.count(), 0)

    def test_create_recepie_with_new_ingridients(self):
        payload = {
            'title': 'Curry',
            'link': 'https://example.com/curry.pdf',
            'time_minutes': 20,
            'price': Decimal('2.50'),
            'ingridients': [{'name': 'Salt'}, {'name': 'Pepper'}]
        }

        res = self.client.post(RECEPIE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepies = Recepie.objects.filter(user=self.user)
        self.assertEqual(recepies.count(), 1)
        recepie = recepies[0]
        self.assertEqual(recepie.ingridients.count(), 2)
        for ingridient in payload['ingridients']:
            exists = recepie.ingridients.filter(
                name=ingridient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recepie_with_existing_ingridients(self):
        ingridient_potatoe = Ingridient.objects.create(
            user=self.user,
            name='Potatoe'
        )
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'ingridients': [{'name': 'Potatoe'}, {'name': 'Pepper'}],
        }
        res = self.client.post(RECEPIE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recepies = Recepie.objects.filter(user=self.user)
        self.assertEqual(recepies.count(), 1)
        recepie = recepies[0]
        self.assertEqual(recepie.ingridients.count(), 2)
        self.assertIn(ingridient_potatoe, recepie.ingridients.all())
        for ingridient in payload['ingridients']:
            exists = recepie.ingridients.filter(
                name=ingridient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ingridient_on_update(self):
        recepie = create_recepie(user=self.user)
        payload = {
            'ingridients': [{'name': 'Salt'}, {'name': 'Pepper'}],
        }
        url = detail_url(recepie.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingridient = Ingridient.objects.filter(user=self.user)
        self.assertEqual(new_ingridient[0], recepie.ingridients.first())

    def test_update_recepie_assign_ingridient(self):
        ingridient_pepper = Ingridient.objects.create(
            user=self.user,
            name='Pepper'
        )
        recepie = create_recepie(user=self.user)
        recepie.ingridients.add(ingridient_pepper)

        ingridient_salt = Ingridient.objects.create(
            user=self.user,
            name='Salt'
        )
        payload = {'ingridients': [{'name': 'Salt'}]}
        url = detail_url(recepie.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingridient_salt, recepie.ingridients.all())
        self.assertNotIn(ingridient_pepper, recepie.ingridients.all())

    def test_clear_recepie_ingridients(self):
        ingridient_pepper = Ingridient.objects.create(
            user=self.user,
            name='Pepper'
        )
        recepie = create_recepie(user=self.user)
        recepie.ingridients.add(ingridient_pepper)

        payload = {'ingridients': []}
        url = detail_url(recepie.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(ingridient_pepper, recepie.ingridients.all())
        self.assertEqual(recepie.ingridients.count(), 0)


class ImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recepie(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
