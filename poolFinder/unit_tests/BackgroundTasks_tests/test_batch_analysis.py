from BackgroundTasks.PlateAnalysis.classes.batch_analysis import BatchAnalysis
from BackgroundTasks.PlateAnalysis.classes.plate import Plate
from django.test import TestCase
from poolFinder.models import ArayaThresholds, Batch
import BackgroundTasks.PlateAnalysis.classes.analysis_functions as func
from unittest.mock import patch, MagicMock
from datetime import datetime
from django.contrib.auth.models import User
import numpy as np
import pandas as pd
from poolFinder.unit_test_resources.helper_functions_and_classes import SpoofBytesIO, CallableGenerator


class BatchAnalysisTest(TestCase):
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
        ArayaThresholds.objects.create(
            araya = 'ARAYA_02',
            positive = 9.5,
            negative = 5,
            nvic = 1.2,
            low_rox = 1000,
            high_rox = 4000
        )
        User.objects.create(
            username = 'SYSTEM',
            is_staff = True,
            is_active = True,
            date_joined = datetime.now()
        )
        Batch.objects.create(
            batch = '000100 - 000101',
            batch_time = datetime.now(),
            uploaded_by = User.objects.all().first(),
            escalations = 'NONE'
        )


    def setUp(self):
        self.batch = BatchAnalysis([('000100', 'POOL00000001'), ('000201', 'POOL00000002')])

    def test_batch_get_files_query(self):
        expected_query = """select substr(SWEEPER_LOG.ORIGINAL_FILENAME, 43),BLOB_VALUES.BLOB_FIELD from SWEEPER_LOG inner join BLOB_VALUES on 
SWEEPER_LOG.ARCHIVED_FILE_BLOB = BLOB_VALUES.BLOB_ID where SWEEPER_LOG.ORIGINAL_FILENAME like '%000085.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000086.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000087.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000088.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000089.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000090.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000091.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000092.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000093.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000094.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000095.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000096.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000097.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000098.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000099.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000100.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000101.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000102.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000103.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000104.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000105.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000106.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000107.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000108.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000109.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000110.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000111.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000112.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000113.csv' or 
SWEEPER_LOG.ORIGINAL_FILENAME like '%000114.csv' or SWEEPER_LOG.ORIGINAL_FILENAME like '%000115.csv'""".replace('\n', '')
        self.assertTrue(str(self.batch._get_files_query()) == str(expected_query))


    def test_batch_remaining_pools_query(self):
        expected_single_array = """select ARRAY_CODE, JOB_NAME from JOB_HEADER where ARRAY_CODE = '000100'"""
        self.assertTrue(self.batch._remaining_pools_query(['000100']) == expected_single_array)

        expected_multi_array = """select ARRAY_CODE, JOB_NAME from JOB_HEADER where ARRAY_CODE in ('000100', '000201')"""
        self.assertTrue(self.batch._remaining_pools_query(['000100', '000201']) == expected_multi_array)

    
    @patch("poolFinder.functions.app_functions.lims_query", MagicMock(return_value = [('000100', 'POOL00000001'), ('000201', 'POOL00000002')]))
    def test_batch_get_remaining_pools(self):
        expected = {
            '000100' : 'POOL00000001',
            '000201' : 'POOL00000002'
        }
        #mock_lims_query.return_value = [('000100', 'POOL00000001'), ('000201', 'POOL00000002')]
        self.assertTrue(self.batch._get_remaining_pools(['000100', '000201']) == expected)

    
    def test_batch_set_araya_data_from_files(self):
        array_file = {'000001': open('poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').readlines()}
        batch = BatchAnalysis([('000001', 'POOL00000001')], files = array_file, araya = 'ARAYA_01')
        batch._set_araya_data_from_files()
        self.assertTrue(batch.plates_dict['000001']['A01'].all_data() == {
            'FAM': 60000, 'VIC': 120, 'ROX': 4000, 'nFAM': 15.0, 'nVIC': 0.03, 'barcode': ''
        })

    
    @patch('io.BytesIO')
    @patch("poolFinder.functions.app_functions.lims_query")
    def test_batch_set_araya_data_from_lims(self, mock_lims_query, MockBytesIO):
        MockBytesIO.return_value = SpoofBytesIO()
        mock_lims_query.return_value = [('000100.csv', SpoofBytesIO(),),]
        self.batch._set_araya_data_from_lims()
        self.assertTrue(self.batch.plates_dict['000100']['A01'].all_data() == {
            'FAM': 4022, 'VIC': 9617, 'ROX': 4125, 'nFAM': 0.975030303030303, 'nVIC': 2.3313939393939394, 'barcode': ''
        })

    @patch('io.BytesIO')
    @patch("poolFinder.functions.app_functions.lims_query", CallableGenerator((x for x in [
        [('000100.csv', SpoofBytesIO()), ('000101.csv', SpoofBytesIO())],
        [],
        [('POOL00000001', 'AAA', 'A01')]
    ])))
    def test_batch_set_plate_data(self, MockBytesIO):
        MockBytesIO.return_value = SpoofBytesIO()
        self.batch.set_plate_data()
        self.assertTrue(self.batch.plates_dict['000100']['A01'].all_data() == {
            'FAM': 4022, 'VIC': 9617, 'ROX': 4125, 'nFAM': 0.975030303030303, 'nVIC': 2.3313939393939394, 'barcode': 'AAA'
        })
        self.assertTrue(self.batch.plates_dict['000101']['A01'].all_data() == {
            'FAM': 4022, 'VIC': 9617, 'ROX': 4125, 'nFAM': 0.975030303030303, 'nVIC': 2.3313939393939394, 'barcode': ''
        })

    def test_batch_lysis_elute_plates_query(self):
        expected = """select JOB_NAME, LYSIS_PLATE, ELUTION_PLATE, PLATE_COORDINATE from SAMPLE where JOB_NAME in ('POOL00000001', 'POOL00000002') and 
PLATE_COORDINATE in ('A01', 'C03', 'E05', 'G07', 'I09', 'K11', 'M13', 'O15', 'A02', 'C04', 'E06', 'G08', 'I10', 'K12', 'M14', 'O16', 
'B01', 'D03', 'F05', 'H07', 'J09', 'L11', 'N13', 'P15', 'B02', 'D04', 'F06', 'H08', 'J10', 'L12', 'N14', 'P16')""".replace('\n', '')
        self.assertTrue(self.batch._lysis_elute_plates_query() == expected)
    
    def test_batch_instruments_query(self):
        expected = """select VALUE, JOB from JOB_PARAMETER where JOB in ('POOL00000001', 'POOL00000002')"""
        self.assertTrue(self.batch._instruments_query(['POOL00000001', 'POOL00000002']) == expected)

        expected = """select VALUE, JOB from JOB_PARAMETER where JOB in ('POOL00000001')"""
        self.assertTrue(self.batch._instruments_query(['POOL00000001']) == expected)

    @patch("poolFinder.functions.app_functions.lims_query", CallableGenerator((x for x in [
        [('POOL00000001', 'INACT00000011', 'ELUTE00000011', 'A01'), ('POOL00000001', 'INACT00000012', 'ELUTE00000012', 'A02'),
        ('POOL00000001', 'INACT00000013', 'ELUTE00000013', 'B01'), ('POOL00000002', 'INACT00000021', 'ELUTE00000021', 'A01')],
        [('HAM_DWP_01', 'INACT00000011'), ('KF_01', 'ELUTE00000011'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000012'),
        ('DRAGONFLY_01', 'ELUTE00000011'), ('HAM_DWP_02', 'INACT00000012'), ('KF_02', 'ELUTE00000012'),
        ('HAM_DWP_03', 'INACT00000013'), ('KF_03', 'ELUTE00000013'), ('DRAGONFLY_03', 'ELUTE00000013'),
        ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001'),
        ('HAM_DWP_21', 'INACT00000021'), ('KF_21', 'ELUTE00000021'), ('ARAYA_02', 'POOL00000002'), ('DRAGONFLY_21', 'ELUTE00000021'),
        ('NEXAR_02', 'POOL00000002'), ('HYDROCYCL_02', 'POOL00000002'), ('HAM_384_02', 'POOL00000002')]
    ])))
    def test_batch_set_plate_instruments(self):
        new_plate = Plate('000102', None)
        self.batch.plates.append(new_plate)
        self.batch.plates_dict['000102'] = new_plate
        self.batch.array_codes.append('000102')
        self.batch.set_plate_instruments()
        self.assertTrue(self.batch.araya == 'ARAYA_01')
        self.assertTrue(self.batch.thresholds == {
            'POSITIVE' : 9,
            'NEGATIVE' : 4,
            'nVIC' : 1,
            'LOW_ROX' : 1600,
            'HIGH_ROX' : 4000
        })
        self.assertTrue(self.batch.plates[0].instruments == {'Pool plate': 'POOL00000001', 'Nexar': 'NEXAR_01', 'Araya': 'ARAYA_01', 
                    'Hydrocycler': 'HYDROCYCL_01', 'Hamilton': 'HAM_384_01', 'Q1': ('INACT00000011','ELUTE00000011'), 
                    'Q2': ('INACT00000012','ELUTE00000012'), 'Q3': ('INACT00000013','ELUTE00000013'), 'Q4': ['', ''],  
                    'INACT00000011': 'HAM_DWP_01', 'ELUTE00000011': {0: 'KF_01', 1: 'DRAGONFLY_01'}, 'INACT00000012': 'HAM_DWP_02', 
                    'ELUTE00000012': {0: 'KF_02', 1: 'DRAGONFLY_02'}, 'INACT00000013': 'HAM_DWP_03', 
                    'ELUTE00000013': {0: 'KF_03', 1: 'DRAGONFLY_03'}, '': '  '})
        self.assertTrue(self.batch.plates[1].instruments == {'Pool plate' : 'POOL00000002', 'Nexar' : 'NEXAR_02', 'Araya' : 'ARAYA_02', 
                    'Hydrocycler' : 'HYDROCYCL_02', 'Hamilton' : 'HAM_384_02', 'Q1' : ('INACT00000021','ELUTE00000021'), 
                    'Q2': ['', ''], 'Q3': ['', ''], 'Q4': ['', ''], 'INACT00000021' : 'HAM_DWP_21', 
                    'ELUTE00000021' : {0 : 'KF_21', 1 : 'DRAGONFLY_21'}, '': '  '})
        self.assertTrue(self.batch.plates[2].araya == 'ARAYA_01')

        batch2 = BatchAnalysis([('000001', None), ('000002', None)], files = {'1': 1}, araya = 'ARAYA_02')
        batch2.any_in_lims = False
        batch2.set_plate_instruments()
        self.assertTrue(batch2.plates[0].araya == 'ARAYA_02')
        self.assertTrue(batch2.thresholds == {
            'POSITIVE' : 9.5,
            'NEGATIVE' : 5,
            'nVIC' : 1.2,
            'LOW_ROX' : 1000,
            'HIGH_ROX' : 4000
        })

    @patch("poolFinder.functions.app_functions.lims_query", CallableGenerator((x for x in [
        [('POOL00000001', 'INACT00000011', 'ELUTE00000011', 'A01'), ('POOL00000001', 'INACT00000012', 'ELUTE00000012', 'A02'),
        ('POOL00000001', 'INACT00000013', 'ELUTE00000013', 'B01'), ('POOL00000002', 'INACT00000021', 'ELUTE00000021', 'A01')],
        [('HAM_DWP_01', 'INACT00000011'), ('KF_01', 'ELUTE00000011'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000012'),
        ('DRAGONFLY_01', 'ELUTE00000011'), ('HAM_DWP_02', 'INACT00000012'), ('KF_02', 'ELUTE00000012'),
        ('HAM_DWP_03', 'INACT00000013'), ('KF_03', 'ELUTE00000013'), ('DRAGONFLY_03', 'ELUTE00000013'),
        ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001'),
        ('HAM_DWP_21', 'INACT00000021'), ('KF_21', 'ELUTE00000021'), ('ARAYA_02', 'POOL00000002'), ('DRAGONFLY_21', 'ELUTE00000021'),
        ('NEXAR_02', 'POOL00000002'), ('HYDROCYCL_02', 'POOL00000002'), ('HAM_384_02', 'POOL00000002')]
    ])))
    def test_batch_comments_query(self):
        new_plate = Plate('000102', None)
        self.batch.plates.append(new_plate)
        self.batch.plates_dict['000102'] = new_plate
        self.batch.array_codes.append('000102')
        self.batch.set_plate_instruments()
        
        expected = """select COMMENTS, JOB_HEADER from C19_JOB_COMMENTS where JOB_HEADER in ('ELUTE00000011', 'INACT00000011', 'ELUTE00000012', 
'INACT00000012', 'ELUTE00000013', 'INACT00000013', 'POOL00000001', 'ELUTE00000021', 'INACT00000021', 'POOL00000002')""".replace('\n', '')

        self.assertTrue(self.batch._comments_query() == expected)

    @patch("poolFinder.functions.app_functions.lims_query", CallableGenerator((x for x in [
        [('POOL00000001', 'INACT00000011', 'ELUTE00000011', 'A01'), ('POOL00000001', 'INACT00000012', 'ELUTE00000012', 'A02'),
        ('POOL00000001', 'INACT00000013', 'ELUTE00000013', 'B01'), ('POOL00000002', 'INACT00000021', 'ELUTE00000021', 'A01')],
        [('HAM_DWP_01', 'INACT00000011'), ('KF_01', 'ELUTE00000011'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000012'),
        ('DRAGONFLY_01', 'ELUTE00000011'), ('HAM_DWP_02', 'INACT00000012'), ('KF_02', 'ELUTE00000012'),
        ('HAM_DWP_03', 'INACT00000013'), ('KF_03', 'ELUTE00000013'), ('DRAGONFLY_03', 'ELUTE00000013'),
        ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001'),
        ('HAM_DWP_21', 'INACT00000021'), ('KF_21', 'ELUTE00000021'), ('ARAYA_02', 'POOL00000002'), ('DRAGONFLY_21', 'ELUTE00000021'),
        ('NEXAR_02', 'POOL00000002'), ('HYDROCYCL_02', 'POOL00000002'), ('HAM_384_02', 'POOL00000002')],
        [('Pool plate comment', 'POOL00000001'), ('Elute 11 comment', 'ELUTE00000011'), ('Inact 11 comment', 'INACT00000011'),
        ('Elute 12 comment', 'ELUTE00000012'), ('Inact 12 comment', 'INACT00000012'), ('Elute 13 comment', 'ELUTE00000013'), 
        ('Inact 13 comment', 'INACT00000013'), ('Elute 21 comment', 'ELUTE00000021'), ('Inact 21 comment', 'INACT00000021'),
        ('Elute 11 comment 2', 'ELUTE00000011')],
    ])))
    def test_batch_set_plate_comments(self):
        self.batch.set_plate_instruments()
        self.batch.set_plate_comments()
        plate_1_expected = {
            'Q1': {'INACT00000011': ['Inact 11 comment'], 'ELUTE00000011': ['Elute 11 comment', 'Elute 11 comment 2']}, 
            'Q2': {'INACT00000012': ['Inact 12 comment'], 'ELUTE00000012': ['Elute 12 comment']}, 
            'Q3': {'INACT00000013': ['Inact 13 comment'], 'ELUTE00000013': ['Elute 13 comment']}, 'Q4': {'': []},
            'Pool': ['Pool plate comment']
        }
        plate_2_expected = {
            'Q1': {'INACT00000021': ['Inact 21 comment'], 'ELUTE00000021': ['Elute 21 comment']}, 'Q2': {'': []}, 'Q3': {'': []}, 'Q4': {'': []},
            'Pool': []
        }
        self.assertTrue(self.batch.plates[0].comments == plate_1_expected)
        self.assertTrue(self.batch.plates[1].comments == plate_2_expected)

    @patch('io.BytesIO')
    @patch("poolFinder.functions.app_functions.lims_query", CallableGenerator((x for x in [
        [('000100.csv', SpoofBytesIO()), ('000101.csv', SpoofBytesIO())],
        [],
        [('POOL00000001', 'AAA', 'A01')],
        [('POOL00000001', 'INACT00000011', 'ELUTE00000011', 'A01'), ('POOL00000001', 'INACT00000012', 'ELUTE00000012', 'A02'),
        ('POOL00000001', 'INACT00000013', 'ELUTE00000013', 'B01'), ('POOL00000002', 'INACT00000021', 'ELUTE00000021', 'A01')],
        [('HAM_DWP_01', 'INACT00000011'), ('KF_01', 'ELUTE00000011'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000012'),
        ('DRAGONFLY_01', 'ELUTE00000011'), ('HAM_DWP_02', 'INACT00000012'), ('KF_02', 'ELUTE00000012'),
        ('HAM_DWP_03', 'INACT00000013'), ('KF_03', 'ELUTE00000013'), ('DRAGONFLY_03', 'ELUTE00000013'),
        ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001'),
        ('HAM_DWP_21', 'INACT00000021'), ('KF_21', 'ELUTE00000021'), ('ARAYA_02', 'POOL00000002'), ('DRAGONFLY_21', 'ELUTE00000021'),
        ('NEXAR_02', 'POOL00000002'), ('HYDROCYCL_02', 'POOL00000002'), ('HAM_384_02', 'POOL00000002')]
    ])))
    def test_batch_analyse_plates(self, MockBytesIO):
        MockBytesIO.return_value = SpoofBytesIO()
        self.batch.set_plate_data()
        self.batch.set_plate_instruments()
        self.batch.analyse_plates()

        self.assertTrue(len(self.batch.plates[0].df) == 384)
        self.assertTrue(list(self.batch.plates[0].df.iloc[0]) == [4022, 9617, 4125, 0.975030303030303, 2.3313939393939394, 'AAA', 'A1', 'None', 'Q1'])
        self.assertTrue(len(self.batch.plates[0].sample_db_objects) == 384)

        self.assertTrue(len(self.batch.plates[1].df) == 384)
        self.assertTrue(list(self.batch.plates[1].df.iloc[0]) == [4022, 9617, 4125, 0.975030303030303, 2.3313939393939394, '', 'A1', 'None', 'Q1'])
        self.assertTrue(len(self.batch.plates[1].sample_db_objects) == 384)

    def test_batch_summary_buffer(self):
        df = dict(plates = [],
            plate_type = [],
            read_date = [],
            test_channel = [],
            patient_samples = [],
            positives = [],
            plods = [],
            vic_fails = [],
            rox_failures = [],
            accu_fails = [],
            negcon_fails = [],
            poscon_fails = [],
            pos_rate = [],
            pos_punch = [],
            plod_punch = [],
            vic_punch = []) # df, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic
        result = self.batch._summary_buffer(df, ['A1', 'A2'], ['A15', 'A16'], ['A5', 'A6'], ['A1', 'A5', 'A03'], ['A15', 'A3'])
        expected = {'plates': [], 'plate_type': ['Possible Buffer'], 'read_date': [], 'test_channel': ['-'], 
                    'patient_samples': [0], 'positives': [2], 'plods': [2], 'vic_fails': ['-'], 'rox_failures': [], 
                    'accu_fails': ['-'], 'negcon_fails': ['-'], 'poscon_fails': ['-'], 'pos_rate': ['-'], 
                    'pos_punch': ['A1'], 'plod_punch': ['A5'], 'vic_punch': ['A15']}
        self.assertTrue(result == expected)

    @patch('io.BytesIO')
    @patch("poolFinder.functions.app_functions.lims_query", CallableGenerator((x for x in [
        [('000100.csv', SpoofBytesIO()), ('000101.csv', SpoofBytesIO())],
        [],
        [('POOL00000001', 'AAA', 'A01')],
        [('POOL00000001', 'INACT00000011', 'ELUTE00000011', 'A01'), ('POOL00000001', 'INACT00000012', 'ELUTE00000012', 'A02'),
        ('POOL00000001', 'INACT00000013', 'ELUTE00000013', 'B01'), ('POOL00000002', 'INACT00000021', 'ELUTE00000021', 'A01')],
        [('HAM_DWP_01', 'INACT00000011'), ('KF_01', 'ELUTE00000011'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000012'),
        ('DRAGONFLY_01', 'ELUTE00000011'), ('HAM_DWP_02', 'INACT00000012'), ('KF_02', 'ELUTE00000012'),
        ('HAM_DWP_03', 'INACT00000013'), ('KF_03', 'ELUTE00000013'), ('DRAGONFLY_03', 'ELUTE00000013'),
        ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001'),
        ('HAM_DWP_21', 'INACT00000021'), ('KF_21', 'ELUTE00000021'), ('ARAYA_02', 'POOL00000002'), ('DRAGONFLY_21', 'ELUTE00000021'),
        ('NEXAR_02', 'POOL00000002'), ('HYDROCYCL_02', 'POOL00000002'), ('HAM_384_02', 'POOL00000002')]
    ])))
    def test_batch_summary_patient(self, MockBytesIO):
        MockBytesIO.return_value = SpoofBytesIO()
        self.batch.set_plate_data()
        self.batch.set_plate_instruments()
        self.batch.analyse_plates()
        plate = self.batch.plates[0]
        self.batch.plates = [plate]
        self.batch.plates_dict = {'000100': plate}
        self.batch.array_codes = [plate.array_code]
        barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        barcodes[14:16, 18:24] = 'Con'
        for row in range(8):
            for col in range(12):
                barcodes[row * 2 + 1, col * 2 + 1] = ''
        plate.barcodes_from_matrix(barcodes)
        plate.data_as_df()
        plate._create_matrices()
        plate.plate_info()
        
        df = dict(plates = [],
            plate_type = [],
            read_date = [],
            test_channel = [],
            patient_samples = [],
            positives = [],
            plods = [],
            vic_fails = [],
            rox_failures = [],
            accu_fails = [],
            negcon_fails = [],
            poscon_fails = [],
            pos_rate = [],
            pos_punch = [],
            plod_punch = [],
            vic_punch = []) # df, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic
        plate.formatted_info['comments'] = 'OLT,    Priority  HTK'
        plate.is_prio = plate.check_if_prio()
        result = self.batch._summary_patient(df, plate, ['A1', 'A2'], ['A15', 'A16'], ['A5', 'A6'], 
            ['A1', 'A5', 'A03'], ['A15', 'A3'], True)
        
        expected = {'plates': [], 'plate_type': ['Patient'], 'read_date': [], 'test_channel': ['OLT, HTK, PRIO'], 
                    'patient_samples': [279], 'positives': [88], 'plods': [0], 'vic_fails': [4], 'rox_failures': [], 
                    'accu_fails': [0], 'negcon_fails': [0], 'poscon_fails': [1], 'pos_rate': ['31.54%'], 
                    'pos_punch': ['A1'], 'plod_punch': ['A5'], 'vic_punch': ['A15']}

        self.assertEqual(result, expected)

    @patch('io.BytesIO')
    @patch("poolFinder.functions.app_functions.lims_query", CallableGenerator((x for x in [
        [('000100.csv', SpoofBytesIO()), ('000101.csv', SpoofBytesIO())],
        [],
        [('POOL00000001', 'AAA', 'A01')],
        [('POOL00000001', 'INACT00000011', 'ELUTE00000011', 'A01'), ('POOL00000001', 'INACT00000012', 'ELUTE00000012', 'A02'),
        ('POOL00000001', 'INACT00000013', 'ELUTE00000013', 'B01'), ('POOL00000002', 'INACT00000021', 'ELUTE00000021', 'A01')],
        [('HAM_DWP_01', 'INACT00000011'), ('KF_01', 'ELUTE00000011'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000012'),
        ('DRAGONFLY_01', 'ELUTE00000011'), ('HAM_DWP_02', 'INACT00000012'), ('KF_02', 'ELUTE00000012'),
        ('HAM_DWP_03', 'INACT00000013'), ('KF_03', 'ELUTE00000013'), ('DRAGONFLY_03', 'ELUTE00000013'),
        ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001'),
        ('HAM_DWP_21', 'INACT00000021'), ('KF_21', 'ELUTE00000021'), ('ARAYA_02', 'POOL00000002'), ('DRAGONFLY_21', 'ELUTE00000021'),
        ('NEXAR_02', 'POOL00000002'), ('HYDROCYCL_02', 'POOL00000002'), ('HAM_384_02', 'POOL00000002')]
    ])))
    def test_batch_buffer_summary(self, MockBytesIO):
        MockBytesIO.return_value = SpoofBytesIO()
        self.batch.set_plate_data()
        self.batch.set_plate_instruments()
        self.batch.analyse_plates()
        plate = self.batch.plates[0]
        barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        barcodes[14:16, 18:24] = 'Con'
        for row in range(8):
            for col in range(12):
                barcodes[row * 2 + 1, col * 2 + 1] = ''
        plate.barcodes_from_matrix(barcodes)
        plate.data_as_df()
        plate._create_matrices()
        plate.plate_info()

        plate_2 = Plate('000101', None)
        plate_2.thresholds = plate.thresholds
        plate_2.read_date = plate.read_date
        plate_2.df = pd.read_csv('.//poolFinder//unit_test_resources//test_data//buffer_plate_df.csv')

        self.batch.plates = [plate, plate_2]
        self.batch.plates_dict = {'000100': plate, '000101': plate_2}
        self.batch.array_codes = [plate.array_code, '000101']
        
        plate.formatted_info['comments'] = 'OLT,    Priority  HTK'
        plate.is_prio = plate.check_if_prio()
        self.batch.buffer_summary()
        expected = {'Plate': ['000100', '000101'], 'Type': ['Patient', 'Possible Buffer'], 
        'Read Date': ['2022/06/01 04:11', '2022/06/01 04:11'], 'Channel': ['OLT, HTK, PRIO', '-'], 
        'Num Samples': [279, 0], 'Positives': [88, 0], 'PLODs': [2, 1], 'VIC Fails': [4, '-'], 
        'Low ROX': [0, 0], 'Accuplex Fails': [0, '-'], 'Negcon Fails': [0, '-'], 'Qnos Fails': [1, '-'], 
        'Patient Positivity': ['31.54%', '-'], 'Pos Punch': ['-', ''], 'Pos to PLOD': ['-', 'E22'], 
        'VIC Punch': ['-', 'A20']}

        self.assertTrue(self.batch.summary.to_dict(orient = 'list') == expected)

    def test_batch_create_unique_batchname(self):
        plate_2 = Plate('000101', None)
        self.batch.plates = [self.batch.plates[0], plate_2]
        self.batch.plates_dict = {'000100': self.batch.plates[0]}
        self.batch.array_codes = [self.batch.plates[0].array_code, plate_2.array_code]

        self.batch.create_unique_batchname()

        self.assertTrue(self.batch.unique_batchname == '000100 - 000101 1')

    def test_func_add_leading_zeros(self):
        string = '123'
        self.assertTrue(func.add_leading_zeros(string, 6) == '000123')

    def test_func_find_arrays_in_current_batch(self):
        first_array = int('000100')
        lower_files = [
            ('000090.csv', None), ('000091.csv', None), ('000092.csv', None), ('000093.csv', None), ('000094.csv', None), 
            ('000095.csv', None), ('000098.csv', None), ('000099.csv', None)
        ]
        lower_files.reverse()
        upper_files = [
            ('000101.csv', None), ('000102.csv', None), ('000103.csv', None), ('000104.csv', None), ('000105.csv', None), 
            ('000106.csv', None), ('000107.csv', None), ('000108.csv', None), ('000109.csv', None), ('000110.csv', None), 
            ('000111.csv', None), ('000112.csv', None), ('000113.csv', None)
        ]
        expected = [
            '000098.csv', '000099.csv', '000100.csv', '000101.csv', '000102.csv', '000103.csv', '000104.csv', '000105.csv',
            '000106.csv', '000107.csv', '000108.csv', '000109.csv', '000110.csv', '000111.csv', '000112.csv', '000113.csv'
        ]

        self.assertTrue(set(func.find_arrays_in_current_batch(first_array, upper_files, lower_files)) == set(expected))

    def test_func_detect_carryover(self):
        pos = ['A1', 'A2']
        vic = ['A15', 'A16']
        plods = ['A5', 'A6']
        previous_fam = ['A1', 'A5', 'A03']
        previous_vic = ['A15', 'A3']
        self.assertTrue(func.detect_carryover(pos, vic, plods, previous_fam, previous_vic) == ('A1', 'A15', 'A5'))

    def test_func_find_stripes(self):
        glob = {'x96_CONTROL_WELLS': [(7, 11), (7, 10), (7, 9)], 'STRIPE_LIMIT': (4.0, 5.0)}

        flag_matrix = np.array([[None for _ in range(12)] for _ in range(8)])
        nfam_matrix = np.array([[1 for _ in range(12)] for _ in range(8)])
        for row in range(8):
            for col in range(12):
                flag_matrix[row, col] = 'None'
        self.assertFalse('Stripe' in func.find_stripes(nfam_matrix, flag_matrix, glob))
        nfam_matrix[3:8, 3] = 10
        self.assertTrue((func.find_stripes(nfam_matrix, flag_matrix, glob)[3:8, 3] == 'Stripe').all())
        nfam_matrix = np.array([[1 for _ in range(12)] for _ in range(8)])
        nfam_matrix[3, 3:8] = 10
        flag_matrix = np.array([[None for _ in range(12)] for _ in range(8)])
        for row in range(8):
            for col in range(12):
                flag_matrix[row, col] = 'None'
        self.assertTrue((func.find_stripes(nfam_matrix, flag_matrix, glob)[3, 3:8] == 'Stripe').all())

    def test_func_format_escalations(self):
        escalations = ['3 or more ROX fails', '6 or more PLODs',
                    'Negcon fail on Q1 has invalidated samples', '10 or more RNaseP failures',
                    'Both positive controls on Q2 have failed', 
                    'The qnostic has failed on Q3, and the accuplex in the same quadrant contains RNaseP',
                    '6 or more PLODs']
        expected = """3 or more ROX fails$$6 or more PLODs$$Negcon fail on Q1 has invalidated samples$$10 or more RNaseP failures$$
Both positive controls on Q2 have failed$$The qnostic has failed on Q3, and the accuplex in the same quadrant contains RNaseP$$6 or
 more PLODs$$""".replace('\n', '')
        self.assertTrue(func.format_escalations(escalations) == expected)
        escalations = []
        expected = """NONE"""
        self.assertTrue(func.format_escalations(escalations) == expected)

    def test_func_format_comments(self):
        comments = {'Q1': {'INACT00000001': ['Lysis Q1'], 'ELUTE00000001': []}, 'Q2': {'INACT00000002': ['Lysis Q2'], 'ELUTE00000002': []}, 
                    'Q3': {'INACT00000003': ['Lysis Q3'], 'ELUTE00000003': []}, 'Q4': {'INACT00000004': ['Lysis Q4'], 'ELUTE00000004': []}, 
                    'Pool': ['Pool Comment']}
        expected = """<br>Pool plate:<br><span style = "color:red;">Pool Comment</span><br><br>INACT00000001 (Q1):<br>
<span style = "color:red;">Lysis Q1</span><br><br>ELUTE00000001 (Q1):<br>None<br><br>INACT00000002 (Q2):<br><span style = 
"color:red;">Lysis Q2</span><br><br>ELUTE00000002 (Q2):<br>None<br><br>INACT00000003 (Q3):<br><span style = "color:red;">
Lysis Q3</span><br><br>ELUTE00000003 (Q3):<br>None<br><br>INACT00000004 (Q4):<br><span style = "color:red;">Lysis Q4</span>
<br><br>ELUTE00000004 (Q4):<br>None<br><br>""".replace('\n', '')

        self.assertTrue(func.format_comments(comments, 'Pool plate') == expected)
