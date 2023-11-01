from django.test import TestCase
from poolFinder.models import AnalysedPlate, Batch
import BackgroundTasks.PlateAnalysis.new_plates_management_functions as func
from unittest.mock import patch
from datetime import datetime
from django.contrib.auth.models import User
from poolFinder.unit_test_resources.helper_functions_and_classes import SpoofBytesIO, MockFileUpload


class PlateManagementTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create(
            username = 'SYSTEM',
            is_staff = True,
            is_active = True,
            date_joined = datetime.now()
        )
        Batch.objects.create(
            batch = '000200 - 000202',
            batch_time = datetime.now(),
            uploaded_by = User.objects.all().first(),
            escalations = 'NONE',
            in_ff = True
        )
        for x in range(3):
            AnalysedPlate.objects.create(
                array_code = '00020' + str(x),
                batch = Batch.objects.all().first(),
                date_in = datetime.now(),
                uploaded_by = User.objects.all().first(),
                in_ff = True
            )

    def test_func_update_previous_plates_and_batches(self):
        plates_in_ff = ['000100', '000101']
        func.update_previous_plates_and_batches(plates_in_ff)

        for x in range(3):
            self.assertFalse(AnalysedPlate.objects.filter(array_code='00020' + str(x)).first().in_ff)
        
        self.assertFalse(Batch.objects.filter(batch='000200 - 000202').first().in_ff)

    @patch('io.BytesIO')
    def test_func_decode_file(self, MockBytesIO):
        MockBytesIO.return_value = SpoofBytesIO()
        self.assertTrue(len(func.decode_file(SpoofBytesIO())) == 64)
        self.assertTrue(func.decode_file(SpoofBytesIO())[0] == 'Douglas Scientific\r')

    @patch('poolFinder.functions.app_functions.lims_query')
    def test_func_array_pools_from_array_code(self, mock_lims_query):
        mock_lims_query.return_value = [('000100', 'POOL00000001')]
        self.assertTrue(func.array_pools_from_array_code('000100', 'SAM_MODERN') == [('000100', 'POOL00000001')])

    @patch('poolFinder.functions.app_functions.lims_query')
    @patch('BackgroundTasks.PlateAnalysis.new_plates_management_functions.decode_file')
    def test_func_array_pools_from_files(self, mock_decode_file, mock_lims_query):
        mock_decode_file.return_value = SpoofBytesIO()
        mock_lims_query.return_value = [('000100', 'POOL00000001'), ('000101', 'POOL00000002')]
        files = [
            MockFileUpload('20220906085838_00890018002017-00620201218-000100.csv'),
            MockFileUpload('20220906085838_00890018002017-00620201218-000101.csv'),
            MockFileUpload('20220906085838_00890018002017-00620201218-000102.csv')
        ]
        result = func.array_pools_from_files(files, 'SAM_MODERN')

        self.assertTrue(result[0] == [('000100', 'POOL00000001'), ('000101', 'POOL00000002')])
        self.assertTrue(result[1]['000100'].read() == 'test')
