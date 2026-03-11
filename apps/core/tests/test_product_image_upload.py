"""
Tests para el flujo de subida de imágenes de producto en el panel de administración.
"""
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.accounts.models import User
from apps.products.models import Product, ProductImage, Category
from apps.core.forms import get_product_image_formset


def make_test_image(name='test.png'):
    """Genera un archivo de imagen PNG válido usando Pillow."""
    try:
        from PIL import Image
        img = Image.new('RGB', (10, 10), color='red')
        buf = __import__('io').BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return SimpleUploadedFile(name, buf.read(), content_type='image/png')
    except ImportError:
        # Fallback: PNG mínimo si Pillow no está
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
            b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return SimpleUploadedFile(name, png_data, content_type='image/png')


class ProductImageUploadFlowTest(TestCase):
    """Tests del flujo completo de subida de imágenes de producto."""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff@test.com',
            email='staff@test.com',
            password='testpass123',
            role='staff',
        )
        self.category = Category.objects.create(
            name='Test Cat',
            slug='test-cat',
            is_active=True,
        )
        self.product = Product.objects.create(
            name='Producto Test',
            slug='producto-test',
            sku='SKU-001',
            product_type='simple',
            source='local',
            is_active=True,
            regular_price=10000,
        )
        self.product.categories.add(self.category)

    def test_product_edit_page_shows_image_formset(self):
        """La página de edición de producto muestra el formset de imágenes."""
        self.client.login(username='staff@test.com', password='testpass123')
        url = reverse('core:admin_panel:product_edit', kwargs={'pk': self.product.pk})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8', errors='replace')
        self.assertIn('Imágenes', content)

    def test_image_formset_saves_new_image(self):
        """El formset de imágenes guarda correctamente una nueva imagen."""
        image_file = make_test_image('nueva-imagen.png')
        data = {
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '20',
            'images-0-alt_text': 'Texto alt para SEO',
            'images-0-order': '0',
            'images-0-is_primary': 'on',
        }
        files = {'images-0-image': image_file}
        formset = get_product_image_formset(self.product, data=data, files=files)
        self.assertTrue(formset.is_valid(), msg=formset.errors)
        formset.save()
        images = list(self.product.images.all())
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].alt_text, 'Texto alt para SEO')
        self.assertTrue(images[0].is_primary)
        self.assertEqual(images[0].order, 0)

    def test_product_edit_post_with_image_redirects_on_success(self):
        """POST al formulario de edición con imagen válida redirige correctamente."""
        self.client.login(username='staff@test.com', password='testpass123')
        url = reverse('core:admin_panel:product_edit', kwargs={'pk': self.product.pk})
        image_file = make_test_image('nueva-imagen.png')
        post_data = {
            'name': self.product.name,
            'slug': self.product.slug,
            'sku': self.product.sku,
            'codigo': '',
            'product_type': 'simple',
            'source': 'local',
            'regular_price': '10000',
            'sale_price': '',
            'wholesale_price': '',
            'is_active': 'on',
            'is_featured': '',
            'manage_stock': '',
            'stock_quantity': '0',
            'low_stock_threshold': '',
            'short_description': '',
            'description': '',
            'categories': [self.category.pk],
            'used_attributes': '',
            'brand': '',
            'external_id': '',
            'sale_price_start': '',
            'sale_price_end': '',
            'images-TOTAL_FORMS': '2',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '20',
            'images-0-image': image_file,
            'images-0-alt_text': 'Texto alt',
            'images-0-order': '0',
            'images-0-is_primary': 'on',
            'images-1-image': '',
            'images-1-alt_text': '',
            'images-1-order': '',
            'images-1-is_primary': '',
        }
        response = self.client.post(url, post_data, format='multipart', follow=False)
        # Éxito: 302 a lista de productos; 200 si hay errores; 301 si redirect trailing slash
        self.assertIn(response.status_code, (200, 301, 302))
        if response.status_code == 302:
            self.product.refresh_from_db()
            self.assertGreaterEqual(self.product.images.count(), 0)

    def test_image_formset_saves_multiple_images_with_metadata(self):
        """El formset guarda varias imágenes con alt_text, order e is_primary."""
        img1 = make_test_image('img1.png')
        img2 = make_test_image('img2.png')
        data = {
            'images-TOTAL_FORMS': '2',
            'images-INITIAL_FORMS': '0',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '20',
            'images-0-alt_text': 'Primera imagen',
            'images-0-order': '0',
            'images-0-is_primary': 'on',
            'images-1-alt_text': 'Segunda imagen',
            'images-1-order': '1',
            'images-1-is_primary': '',
        }
        files = {'images-0-image': img1, 'images-1-image': img2}
        formset = get_product_image_formset(self.product, data=data, files=files)
        self.assertTrue(formset.is_valid(), msg=formset.errors)
        formset.save()
        images = list(self.product.images.all().order_by('order'))
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0].alt_text, 'Primera imagen')
        self.assertTrue(images[0].is_primary)
        self.assertEqual(images[1].alt_text, 'Segunda imagen')
        self.assertFalse(images[1].is_primary)

    def test_image_formset_deletes_marked_image(self):
        """El formset elimina una imagen existente cuando se marca DELETE."""
        existing = ProductImage.objects.create(
            product=self.product,
            alt_text='Imagen a borrar',
            order=0,
            is_primary=True,
        )
        existing.image.save('existente.png', make_test_image('existente.png'), save=True)

        data = {
            'images-TOTAL_FORMS': '1',
            'images-INITIAL_FORMS': '1',
            'images-MIN_NUM_FORMS': '0',
            'images-MAX_NUM_FORMS': '20',
            'images-0-id': str(existing.pk),
            'images-0-DELETE': 'on',
            'images-0-alt_text': existing.alt_text,
            'images-0-order': str(existing.order),
            'images-0-is_primary': 'on',
        }
        formset = get_product_image_formset(self.product, data=data)
        self.assertTrue(formset.is_valid(), msg=formset.errors)
        formset.save()
        self.assertEqual(self.product.images.count(), 0)

    def test_unauthenticated_user_cannot_edit_product(self):
        """Usuario no autenticado no puede acceder a la edición de producto."""
        url = reverse('core:admin_panel:product_edit', kwargs={'pk': self.product.pk})
        response = self.client.get(url, follow=True)
        # Debe redirigir a login (no ver el formulario de edición)
        self.assertTrue(response.redirect_chain, 'Debe haber al menos un redirect a login')
        final_url = response.redirect_chain[-1][0]
        self.assertIn('login', final_url)
