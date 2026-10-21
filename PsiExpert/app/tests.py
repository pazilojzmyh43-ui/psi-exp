from django.contrib.auth.models import User
from django.test import TestCase

from .forms import CategoryForm
from .models import Category, Profile


class CategoryValidationTests(TestCase):
    def test_duplicate_name_rejected_case_insensitive(self):
        Category.objects.create(name='Индивидуальная терапия', slug='individual', description='Первая')
        form = CategoryForm(data={
            'name': '  индивидуальная терапия  ',
            'description': 'Ещё раз',
            'position': 1,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('уже существует', form.errors['name'][0])

    def test_same_record_can_keep_name(self):
        category = Category.objects.create(name='Специальные методы', slug='methods', position=2)
        form = CategoryForm(
            data={'name': 'Специальные методы', 'description': 'КПТ и EMDR', 'position': 2},
            instance=category,
        )
        self.assertTrue(form.is_valid())

    def test_new_name_is_saved_with_slug(self):
        form = CategoryForm(data={'name': 'Форматы консультаций', 'description': 'Очно и онлайн', 'position': 3})
        self.assertTrue(form.is_valid())
        category = form.save()
        self.assertEqual(category.slug, 'formaty-konsultatsiy')


class AccessTests(TestCase):
    def test_guest_can_open_public_pages(self):
        for url in ('/', '/about/', '/catalog/', '/news/', '/contacts/', '/materials/', '/login/', '/register/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_guest_cart_asks_for_login(self):
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_manager_does_not_open_client_cart(self):
        user = User.objects.create_user('m', password='PsiManager!26')
        user.profile.role = Profile.ROLE_MANAGER
        user.profile.save()
        self.client.login(username='m', password='PsiManager!26')
        response = self.client.get('/cart/')
        self.assertRedirects(response, '/')

    def test_client_opens_cart(self):
        User.objects.create_user('c', password='PsiClient!26')
        self.client.login(username='c', password='PsiClient!26')
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)
