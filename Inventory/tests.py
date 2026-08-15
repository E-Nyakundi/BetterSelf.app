from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Item


@override_settings(ALLOWED_HOSTS=['testserver', '127.0.0.1', 'localhost'])
class InventoryViewsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='inventory_user', password='pass12345')
        self.other_user = User.objects.create_user(username='other_inventory_user', password='pass12345')
        self.client.force_login(self.user)

    def test_create_category_assigns_current_user(self):
        response = self.client.post(reverse('category-create'), {'name': 'Tools', 'parent': ''})

        self.assertRedirects(response, reverse('category-list'))
        self.assertTrue(Category.objects.filter(user=self.user, name='Tools').exists())

    def test_create_item_assigns_current_user(self):
        category = Category.objects.create(user=self.user, name='Tools')

        response = self.client.post(reverse('item-create'), {
            'name': 'Hammer',
            'category': category.id,
            'date_acquired': '2026-05-17',
            'condition': 'used_good',
            'purpose': 'Repairs',
            'item_type': 'Hand tool',
        })

        self.assertRedirects(response, reverse('item-list'))
        self.assertTrue(Item.objects.filter(user=self.user, name='Hammer', category=category).exists())

    def test_create_item_rejects_another_users_category(self):
        other_category = Category.objects.create(user=self.other_user, name='Private')

        response = self.client.post(reverse('item-create'), {
            'name': 'Borrowed',
            'category': other_category.id,
            'condition': 'new',
            'item_type': 'Tool',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(user=self.user, name='Borrowed').exists())
        self.assertContains(response, 'Select a valid choice', status_code=200)

    def test_item_list_only_shows_current_users_items(self):
        own_category = Category.objects.create(user=self.user, name='Office')
        other_category = Category.objects.create(user=self.other_user, name='Office')
        own_item = Item.objects.create(user=self.user, category=own_category, name='Notebook')
        other_item = Item.objects.create(user=self.other_user, category=other_category, name='Private Notebook')

        response = self.client.get(reverse('item-list'))

        self.assertContains(response, own_item.name)
        self.assertNotContains(response, other_item.name)

    def test_item_search_filters_by_type(self):
        category = Category.objects.create(user=self.user, name='Tools')
        Item.objects.create(user=self.user, category=category, name='Hammer', item_type='Hand tool')
        Item.objects.create(user=self.user, category=category, name='Laptop', item_type='Device')

        response = self.client.get(reverse('item-list'), {'item_type': 'Device'})

        self.assertContains(response, 'Laptop')
        self.assertNotContains(response, 'Hammer')

    def test_cannot_edit_another_users_item(self):
        other_category = Category.objects.create(user=self.other_user, name='Tools')
        other_item = Item.objects.create(user=self.other_user, category=other_category, name='Private Hammer')

        response = self.client.get(reverse('item-edit', args=[other_item.pk]))

        self.assertEqual(response.status_code, 404)

    def test_dispose_item_removes_owned_item(self):
        category = Category.objects.create(user=self.user, name='Tools')
        item = Item.objects.create(user=self.user, category=category, name='Old Hammer')

        response = self.client.post(reverse('item-dispose', args=[item.pk]))

        self.assertRedirects(response, reverse('item-list'))
        self.assertFalse(Item.objects.filter(pk=item.pk).exists())
