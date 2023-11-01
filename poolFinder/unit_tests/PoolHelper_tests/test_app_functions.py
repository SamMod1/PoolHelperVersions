from re import M
from typing_extensions import assert_type
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from poolFinder.models import AnalysedPlate, ArayaThresholds, Batch, PoolFinderConfig
from datetime import datetime
from poolFinder.functions.config_parse import config_parse
import poolFinder.functions.app_functions as func
from django.urls import reverse
from django.contrib.auth.models import User


class AppFunctionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        PoolFinderConfig.objects.create(
            option = 'test',
            value = 'thisisatest'
        )
        ArayaThresholds.objects.create(
            araya = 'ARAYA_01',
            positive = 9,
            negative = 4,
            nvic = 1,
            low_rox = 1600,
            high_rox = 4000,
            lj_mean_accu = 13.14,
            lj_mean_qneg = 1.22,
            lj_mean_qpos = 12.73,
            lj_sd_accu = 1.3,
            lj_sd_qneg = 0.3,
            lj_sd_qpos = 1.28
        )
        ArayaThresholds.objects.create(
            araya = 'ARAYA_02',
            positive = 9.5,
            negative = 5,
            nvic = 1.2,
            low_rox = 1000,
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
            escalations = '',
            plates = '000001'
        )
        AnalysedPlate.objects.create(
            array_code = '000001',
            batch = Batch.objects.all().first(),
            date_in = datetime.now(),
            uploaded_by = User.objects.all().first(),
            araya = 'ARAYA_01'
        )
    
    def test_func_get_thresholds(self):
        self.assertEqual(func.get_thresholds('ARAYA_01'), dict(
            POSITIVE = 9,
            NEGATIVE = 4,
            nVIC = 1,
            LOW_ROX = 1600,
            HIGH_ROX = 4000
        ))
        self.assertEqual(func.get_thresholds('ARAYA_02'), dict(
            POSITIVE = 9.5,
            NEGATIVE = 5,
            nVIC = 1.2,
            LOW_ROX = 1000,
            HIGH_ROX = 4000
        ))
    
    def test_func_create_batchnav(self):
        batch = Batch.objects.filter(batch='000001 - 000001').first()
        plate = AnalysedPlate.objects.filter(array_code='000001').first()

        self.assertEqual(type(func.create_batchnav(batch, plate)), str)

    def test_func_remove_text_in_brackets(self):
        self.assertEqual(func.remove_text_in_brackets('Hello (foo bar) World'), 'Hello World')

    def test_func_create_araya_choices(self):
        self.assertEqual(type(func.create_araya_choices()), str)

    def test_func_daily_contams(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        araya_file = open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').read().encode()
        araya_files = [SimpleUploadedFile('20220906090154_00890018002017-00620201218-000100.csv', araya_file, content_type="text/plain")]
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': araya_files, 'araya_choice': 'ARAYA_01'}, follow=True
        )
        expected = [('000100', 77, 45, 'Buffer'), (':', 'Total: 77', 'Total: 45', '')]

        self.assertEqual(func._daily_contams(AnalysedPlate.objects.all()), expected)

    def test_func_daily_summary(self):
        self.client.login(username='SYSTEM', password='_TestUserPassword_')
        araya_file = open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').read().encode()
        araya_files = [SimpleUploadedFile('20220906090154_00890018002017-00620201218-000100.csv', araya_file, content_type="text/plain")]
        response = self.client.post(
            reverse('Pool Helper-Batches Awaiting Release'), {'array_search': '', 'upload': araya_files, 'araya_choice': 'ARAYA_01'}, follow=True
        )
        expected = ((('Number of plates released: ', 0), ('Number of samples released: ', 0)), ())

        self.assertEqual(func.daily_summary(), expected)

    def test_func_find_test_channels_from_comments(self):
        plate = AnalysedPlate.objects.first()
        plate.is_prio = False
        plate.is_vip = True
        comments = """<br>POOL00078853:<br><span style = "color:red;">INC0085187</span><br><span style = "color:red;">
        Restamp from: 673875</span><br><br>INACT00152138 (Q1):<br><span style = "color:red;">OLT</span><br><br>ELUTE00316051 
        (Q1):<br>None<br><br>INACT00152137 (Q2):<br><span style = "color:red;">OLT</span><br><br>ELUTE00316047 
        (Q2):<br>None<br><br>INACT00152132 (Q3):<br><span style = "color:red;">OLT</span><br><br>ELUTE00316046 
        (Q3):<br>None<br><br>INACT00152131 (Q4):<br><span style = "color:red;">HTK</span><br><br>ELUTE00316045 
        (Q4):<br>None<br><br>"""
        plate.formatted_info = {'comments': comments}

        channels = func.find_test_channels_from_comments(plate)

        self.assertTrue('HTK' in channels and 'OLT' in channels and 'VIP' in channels)

    def test_func_format_escalations(self):
        escalations = """High number of PLODs - Comment: Also a mastermix only signal in A3$$"""

        expected = """Reason: High number of PLODs<br>Comment: Also a mastermix only signal in A3"""

        self.assertEqual(func._format_escalations(escalations), expected)

    def test_func_escalation_summary(self):
        batch = Batch.objects.filter(batch='000001 - 000001').first()
        self.assertEqual(func.escalation_summary(batch), [['No Escalations', '', '', '', '', 'user', '', '', '', '']])
        plate = AnalysedPlate.objects.filter(array_code='000001').first()
        plate.escalated = True
        plate.escalation_reason = '''High number of PLODs - Comment: Also a mastermix only signal in A3$$'''
        plate.save()
        batch.escalations = '000001'
        batch.save()

        reason = '''Reason: High number of PLODs<br>Comment: Also a mastermix only signal in A3'''
        expected = [['000001', '', reason, '', '', 'user', '', '', '', '']]

        self.assertTrue(func.escalation_summary(batch), expected)

    def test_func_add_lj_plot_lines(self):
        expected = [{'type': 'line', 'yref': 'y', 'y0': 13.14, 'y1': 13.14, 'xref': 'paper', 'x0': 0, 'x1': 1, 'line': 
        {'color': 'grey', 'width': 3, 'dash': 'dot'}}, {'type': 'line', 'yref': 'y', 'y0': 14.440000000000001, 
        'y1': 14.440000000000001, 'xref': 'paper', 'x0': 0, 'x1': 1, 'line': {'color': 'green', 'width': 3, 'dash': 'dot'}}, 
        {'type': 'line', 'yref': 'y', 'y0': 11.84, 'y1': 11.84, 'xref': 'paper', 'x0': 0, 'x1': 1, 'line': 
        {'color': 'green', 'width': 3, 'dash': 'dot'}}, {'type': 'line', 'yref': 'y', 'y0': 15.74, 'y1': 15.74, 'xref': 
        'paper', 'x0': 0, 'x1': 1, 'line': {'color': 'orange', 'width': 3, 'dash': 'dot'}}, {'type': 'line', 'yref': 'y', 
        'y0': 10.540000000000001, 'y1': 10.540000000000001, 'xref': 'paper', 'x0': 0, 'x1': 1, 'line': {'color': 'orange', 
        'width': 3, 'dash': 'dot'}}, {'type': 'line', 'yref': 'y', 'y0': 17.04, 'y1': 17.04, 'xref': 'paper', 'x0': 0, 'x1': 1, 
        'line': {'color': 'red', 'width': 3, 'dash': 'dot'}}, {'type': 'line', 'yref': 'y', 'y0': 9.24, 'y1': 9.24, 'xref': 
        'paper', 'x0': 0, 'x1': 1, 'line': {'color': 'red', 'width': 3, 'dash': 'dot'}}]
        result = func._add_lj_plot_lines('ARAYA_01', 'accu', 3)

        print('RESULT = ' + str(result))

        self.assertEqual(result, expected)

    def test_func_levy_jennings_plot(self):
        plot = func.levy_jennings_plot('ARAYA_01', 1)
        self.assertFalse(plot)

    def test_func_config_parse(self):
        expected = {'test': 'thisisatest'}

        self.assertEqual(config_parse(), expected)
