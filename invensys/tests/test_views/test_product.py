from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ...models import Category, Product, ProductPrice, ProductUnit, Unit


class ProductViewSetTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user_a = User.objects.create_user(username='usera', password='password123')
        self.user_b = User.objects.create_user(username='userb', password='password123')

        self.category = Category.objects.create(name='Elektronik', created_by=self.user_a)
        self.unit = Unit.objects.create(name='pcs')
        self.unit2 = Unit.objects.create(name='pcs2')
        self.product = Product.objects.create(
            name='Mouse',
            category=self.category,
            created_by=self.user_a,
            updated_by=self.user_a,
        )
        self.pu1 = ProductUnit.objects.create(
            product=self.product,
            unit=self.unit,
            multiplier=1,
            is_base_unit=True,
        )
        self.pu2 = ProductUnit.objects.create(
            product=self.product,
            unit=self.unit2,
            multiplier=2,
            is_base_unit=False,
        )
        self.pp1 = ProductPrice.objects.create(
            product=self.product,
            unit=self.unit,
            price=Decimal('25.00'),
            minimum_quantity=1,
        )
        self.pp2 = ProductPrice.objects.create(
            product=self.product,
            unit=self.unit,
            price=Decimal('30.00'),
            minimum_quantity=2,
        )

        self.list_url = reverse('product-list')
        self.detail_url = reverse('product-detail', kwargs={'pk': self.product.pk})

    def test_unauthenticated_access_denied(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_products_list(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row['name'], 'Mouse')
        self.assertIn('sku_number', row)
        self.assertEqual(row['category']['name'], 'Elektronik')
        self.assertEqual(row['unit'], 'pcs')
        self.assertEqual(Decimal(str(row['price'])), Decimal('25.00'))

    def test_get_product_detail(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Mouse')
        self.assertIn('prices', response.data)
        self.assertIn('units', response.data)
        self.assertEqual(len(response.data['prices']), 2)
        self.assertEqual(len(response.data['units']), 2)
        self.assertEqual(response.data['prices'][0]['unit']['name'], 'pcs')
        self.assertEqual(response.data['units'][0]['unit']['name'], 'pcs')

    def test_create_product(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'name': 'Keyboard',
            'category_id': self.category.pk,
            'prices': [
                {'price': '150.00', 'minimum_quantity': 1, 'unit_id': self.unit.pk},
            ],
            'units': [
                {'unit_id': self.unit.pk, 'multiplier': 1, 'is_base_unit': True},
            ],
        }
        response = self.client.post(self.list_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Product.objects.get(pk=response.data['id'])
        self.assertEqual(created.category, self.category)
        self.assertEqual(created.prices.count(), 1)
        self.assertEqual(created.productunit_set.count(), 1)

    def test_update_product(self):
        self.client.force_authenticate(user=self.user_b)
        payload = {
            'name': 'Mouse Wireless',
            'category_id': self.category.pk,
            'prices': [
                {
                    'id': self.pp1.pk,
                    'price': '50.00',
                    'minimum_quantity': 1,
                    'unit_id': self.unit.pk,
                },
                {
                    'price': '60.00',
                    'minimum_quantity': 2,
                    'unit_id': self.unit.pk,
                },
            ],
            'units': [
                {
                    'id': self.pu1.pk,
                    'unit_id': self.unit.pk,
                    'is_base_unit': True,
                },
                {
                    'unit_id': self.unit2.pk,
                    'multiplier': 4,
                    'is_base_unit': False,
                },
            ],
        }
        response = self.client.put(self.detail_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Mouse Wireless')

        self.assertFalse(ProductPrice.objects.filter(pk=self.pp2.pk).exists())
        self.assertFalse(ProductUnit.objects.filter(pk=self.pu2.pk).exists())

        self.assertEqual(self.product.prices.count(), 2)
        self.assertEqual(self.product.productunit_set.count(), 2)

        new_pp = self.product.prices.filter(unit=self.unit, minimum_quantity=2).first()
        self.assertEqual(self.product.prices.get(pk=self.pp1.pk).price, Decimal('50.00'))
        self.assertEqual(self.product.prices.get(pk=new_pp.pk).price, Decimal('60.00'))

        new_pu = self.product.productunit_set.filter(unit=self.unit2, multiplier=4).first()
        self.assertTrue(self.product.productunit_set.filter(pk=self.pu1.pk).exists())
        self.assertTrue(self.product.productunit_set.filter(pk=new_pu.pk).exists())

    def test_partial_update_product(self):
        self.client.force_authenticate(user=self.user_b)
        payload = {
            'name': 'Mouse Wireless',
        }
        response = self.client.patch(self.detail_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Mouse Wireless')
        self.assertEqual(self.product.prices.count(), 2)
        self.assertEqual(self.product.productunit_set.count(), 2)

    def test_delete_product(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_invalid_create_product(self):
        self.client.force_authenticate(user=self.user_a)
        payload = {
            'name': 'Invalid Product',
            'category_id': 9999,
            'prices': [
                {'price': '150.00', 'minimum_quantity': 1, 'unit_id': self.unit.pk},
            ],
            'units': []
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category_id', response.data)
        self.assertNotIn('units', response.data)
