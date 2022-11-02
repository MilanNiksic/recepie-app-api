import decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core import models


def create_user(email='test@example.com', password='testpassword123'):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_sucessful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@EXAMPLE.COM', 'test4@example.com'],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_super_user(self):
        user = get_user_model().objects.create_superuser(
            'test@examile.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recepie(self):
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )
        recepie = models.Recepie.objects.create(
            user=user,
            title='Sambple recepie',
            time_minutes=5,
            price=decimal.Decimal('5.50'),
            description='Sample recepie description'
        )
        self.assertEqual(str(recepie), recepie.title)

    def test_create_tag(self):
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)

    def test_create_ingridient(self):
        user = create_user()
        ingridient = models.Ingridient.objects.create(user=user, name='Peper')

        self.assertEqual(str(ingridient), ingridient.name)

    @patch('core.models.uuid.uuid4')
    def test_recepie_file_name_uuid(self, mock_uuid):
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recepie_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recepie/{uuid}.jpg')
