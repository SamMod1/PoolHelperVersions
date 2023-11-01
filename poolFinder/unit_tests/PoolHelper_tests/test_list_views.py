from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from poolFinder.models import AnalysedPlate, ArayaThresholds
from datetime import datetime
from django.urls import reverse
from django.contrib.auth.models import User


class ListViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        ArayaThresholds.objects.create(
            araya = 'ARAYA_01',
            positive = 9,
            negative = 4,
            nvic = 1,
            low_rox = 1600,
            high_rox = 4000
        )
        user = User(
            username = 'SYSTEM',
            is_staff = True,
            is_active = True,
            date_joined = datetime.now(),
        )
        user.set_password('_TestUserPassword_')
        user.save()

    # Batches awaiting release view:
    def test_view_batches_awaiting_release_render(self):
        """Test view is rendered if user is logged in"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.get(reverse('Pool Helper-Batches Awaiting Release'), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/list_views/batches_awaiting_release.html')

    def test_view_batches_awaiting_release_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Batches Awaiting Release'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Batches Awaiting Release"))
        response = self.client.post(reverse('Pool Helper-Batches Awaiting Release'), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Batches Awaiting Release"))

    def test_view_batches_awaiting_release_blank_form(self):
        """
        Checks that without form data no new batch is uploaded and no redirect occurrs (actual form errors and validation were not used in this code
        due to the simplicity of the form)
        """
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': [], 'araya_choice': 'ARAYA_01'}, follow=True
        )
        self.assertTemplateUsed(response, 'poolFinder/list_views/batches_awaiting_release.html')

    def test_view_batches_awaiting_release_batch_upload(self):
        """Use the form to upload a test batch and check if that batch gets saved to database and the user gets redirected to the batch page"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        araya_file = open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').read().encode()
        araya_files = [SimpleUploadedFile('20220906090154_00890018002017-00620201218-000001.csv', araya_file, content_type="text/plain")]
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': araya_files, 'araya_choice': 'ARAYA_01'}, follow=True
        )
        self.assertTemplateUsed(response, 'poolFinder/other_views/batch_overview.html')
        self.assertTrue(AnalysedPlate.objects.filter(array_code='000001').exists())

    # Plates in FF view:
    def test_view_plates_in_ff_render(self):
        """Test view is rendered if user is logged in"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.get(reverse('Pool Helper-Plates in FF'), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/list_views/plates_in_ff.html')

    def test_view_plates_in_ff_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Plates in FF'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Plates in FF"))
        response = self.client.post(reverse('Pool Helper-Plates in FF'), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Plates in FF"))

    def test_view_plates_in_ff_form_hide(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.post(reverse('Pool Helper-Plates in FF'), {'choice': 'HIDE'}, follow = True)
        self.assertRedirects(response, reverse('Pool Helper-Plates in FF'))

    def test_view_plates_in_ff_form_escalate(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.post(reverse('Pool Helper-Plates in FF'), {'choice': 'ESCALATE'}, follow = True)
        self.assertRedirects(response, reverse('Pool Helper-Modify Plate', args={'choice': 'pk'}))

    # Archive view:
    def test_view_archive_render(self):
        """Test view is rendered if user is logged in"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.get(reverse('Pool Helper-Archive', args={'1': 'pk'}), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/list_views/archive.html')

    def test_view_archive_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Archive', args={'1': 'pk'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Archive', args={'1': 'pk'}))
        response = self.client.post(reverse('Pool Helper-Archive', args={'1': 'pk'}), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Archive', args={'1': 'pk'}))

    def test_view_archive_page_form(self):
        """
        Checks that without form data no new batch is uploaded and no redirect occurrs (actual form errors and validation were not used in this code
        due to the simplicity of the form)
        """
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.post(reverse('Pool Helper-Archive', args={'1': 'pk'}), {'page': '2'})
        self.assertRedirects(response, reverse('Pool Helper-Archive', args={'2': 'pk'}))

    # Search results view:
    def test_view_search_results_render(self):
        """Test view is rendered if user is logged in"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.get(reverse('Pool Helper-Search Results', args={'thisisnotanarraycode': 'pk'}), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/list_views/search_list.html')

    def test_view_search_results_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Search Results', args={'thisisnotanarraycode': 'pk'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Search Results', args={'thisisnotanarraycode': 'pk'}))
        response = self.client.post(reverse('Pool Helper-Search Results', args={'thisisnotanarraycode': 'pk'}), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Search Results', args={'thisisnotanarraycode': 'pk'}))
