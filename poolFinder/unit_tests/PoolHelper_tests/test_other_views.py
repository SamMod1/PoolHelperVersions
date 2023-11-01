from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from poolFinder.models import AnalysedPlate, ArayaThresholds, Batch
from datetime import datetime
from django.urls import reverse
from django.contrib.auth.models import User


class OtherViewsTest(TestCase):
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
        Batch.objects.create(
            batch = '000001 - 000001',
            batch_time = datetime.now(),
            uploaded_by = User.objects.all().first(),
            escalations = 'NONE'
        )
        AnalysedPlate.objects.create(
            array_code = '000001',
            batch = Batch.objects.all().first(),
            date_in = datetime.now(),
            uploaded_by = User.objects.all().first(),
            araya = 'ARAYA_01'
        )

    # Home view:
    def test_view_home_render(self):
        """Test view is rendered if user is logged in"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.get(reverse('Pool Helper-Home'), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/other_views/home.html')

    def test_view_home_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Home'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Home"))
        response = self.client.post(reverse('Pool Helper-Home'), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Home"))

    # Modify plate view:
    def test_view_modify_plate_render(self):
        """Test view is rendered if user is logged in"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.get(reverse('Pool Helper-Modify Plate', args={'choice': 'pk'}), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/other_views/modify_plate.html')

    def test_view_modify_plate_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Modify Plate', args={'choice': 'pk'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Modify Plate", args={'choice': 'pk'}))
        response = self.client.post(reverse('Pool Helper-Modify Plate', args={'choice': 'pk'}), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Modify Plate", args={'choice': 'pk'}))

    def test_view_modify_plate_blank_form(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.post(
            reverse('Pool Helper-Modify Plate', args={'choice-000001': 'pk'}), {'escalation': 0, 'comments': ''}, follow=True
        )
        self.assertRedirects(response, reverse('Pool Helper-Plates in FF'))
        self.assertFalse(AnalysedPlate.objects.filter(array_code='000001').first().escalated)
    
    def test_view_modify_plate_form_submit(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.post(
            reverse('Pool Helper-Modify Plate', args={'choice-000001': 'pk'}), {'escalation': 1, 'comments': 'Test'}, follow=True
        )
        self.assertRedirects(response, reverse('Pool Helper-Plates in FF'))
        self.assertTrue(AnalysedPlate.objects.filter(array_code='000001').first().escalated)
        self.assertEqual(AnalysedPlate.objects.filter(array_code='000001').first().escalation_reason, 'Suspicious pattern or stripe - Comment: Test$$')

    # Plate view:
    def test_view_plate_render(self):
        """Test view is rendered if user is logged in"""
        # Need to upload a plate which has actual data otherwise the rendering will error:
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        araya_file = open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').read().encode()
        araya_files = [SimpleUploadedFile('20220906090154_00890018002017-00620201218-000001.csv', araya_file, content_type="text/plain")]
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': araya_files, 'araya_choice': 'ARAYA_01'}, follow=True
        )

        response = self.client.get(reverse('Pool Helper-Plate', args={'000001 1': 'pk'}), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/other_views/plate.html')

    def test_view_plate_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Plate', args={'000001': 'pk'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Plate", args={'000001': 'pk'}))
        response = self.client.post(reverse('Pool Helper-Plate', args={'000001': 'pk'}), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse("Pool Helper-Plate", args={'000001': 'pk'}))

    def test_view_plate_blank_form(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        araya_file = open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').read().encode()
        araya_files = [SimpleUploadedFile('20220906090154_00890018002017-00620201218-000001.csv', araya_file, content_type="text/plain")]
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': araya_files, 'araya_choice': 'ARAYA_01'}, follow=True
        )

        response = self.client.post(reverse('Pool Helper-Plate', args={'000001 1': 'pk'}), {'escalation': 0, 'comments': ''}, follow=True)
        self.assertRedirects(response, reverse('Pool Helper-Plates in FF'))
        self.assertFalse(AnalysedPlate.objects.filter(array_code='000001 1').first().escalated)
    
    def test_view_plate_form_submit(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        araya_file = open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').read().encode()
        araya_files = [SimpleUploadedFile('20220906090154_00890018002017-00620201218-000001.csv', araya_file, content_type="text/plain")]
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': araya_files, 'araya_choice': 'ARAYA_01'}, follow=True
        )

        response = self.client.post(reverse('Pool Helper-Plate', args={'000001 1': 'pk'}), {'escalation': 1, 'comments': 'Test'}, follow=True)
        self.assertRedirects(response, reverse('Pool Helper-Plates in FF'))
        self.assertTrue(AnalysedPlate.objects.filter(array_code='000001 1').first().escalated)
        self.assertEqual(AnalysedPlate.objects.filter(array_code='000001 1').first().escalation_reason, 'Suspicious pattern or stripe - Comment: Test$$')

    # Batch overview view:
    def test_view_batch_overview_render(self):
        """Test view is rendered if user is logged in"""
        # Need to upload a plate which has actual data otherwise the rendering will error:
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        araya_file = open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').read().encode()
        araya_files = [SimpleUploadedFile('20220906090154_00890018002017-00620201218-000001.csv', araya_file, content_type="text/plain")]
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': araya_files, 'araya_choice': 'ARAYA_01'}, follow=True
        )

        response = self.client.get(reverse('Pool Helper-Batch Overview', args={'000001 - 000001 1': 'pk'}), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/other_views/batch_overview.html')

    def test_view_batch_overview_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Batch Overview', args={'000001 - 000001': 'pk'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Batch Overview', args={'000001%20-%20000001': 'pk'}))
        response = self.client.post(reverse('Pool Helper-Batch Overview', args={'000001 - 000001': 'pk'}), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Batch Overview', args={'000001%20-%20000001': 'pk'}))

    # Search view:
    def test_view_search_render(self):
        """Test view is rendered if user is logged in"""
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.get(reverse('Pool Helper-Search'), follow=True)
        self.assertTemplateUsed(response, 'poolFinder/other_views/search.html')

    def test_view_search_deny_anonymous(self):
        """Test non-logged in users get redirected to login page"""
        response = self.client.get(reverse('Pool Helper-Search'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Search'))
        response = self.client.post(reverse('Pool Helper-Search'), follow=True)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('Pool Helper-Search'))

    def test_view_search_form(self):
        """
        Checks that without form data no new batch is uploaded and no redirect occurrs (actual form errors and validation were not used in this code
        due to the simplicity of the form)
        """
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        response = self.client.post(
            reverse('Pool Helper-Search'), {'psearch': 'thisisnotanarraycode'}, follow=True
        )
        self.assertRedirects(response, reverse('Pool Helper-Search Results', args={'thisisnotanarraycode': 'pk'}))
