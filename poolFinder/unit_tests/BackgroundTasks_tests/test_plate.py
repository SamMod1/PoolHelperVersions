from BackgroundTasks.PlateAnalysis.classes.sample import Sample
from BackgroundTasks.PlateAnalysis.classes.plate import Plate
from poolFinder.models import Sample as db_Sample
from poolFinder.models import ArayaThresholds, AnalysedPlate, Batch
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from django.test import TestCase
from datetime import datetime
import pandas as pd
import numpy as np


LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
NUMBERS = ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17',
           '18', '19', '20', '21', '22', '23', '24')


class PlateTest(TestCase):
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
            batch = '000001 - 000016',
            batch_time = datetime.now(),
            uploaded_by = User.objects.all().first(),
            escalations = 'NONE'
        )
        AnalysedPlate.objects.create(
            array_code = '000001',
            batch = Batch.objects.all().first(),
            date_in = datetime.now(),
            uploaded_by = User.objects.all().first()
        )

    def setUp(self):
        self.plate = Plate('000001', None)

    def test_plate_get_set_item(self):
    
        self.assertTrue(self.plate['A01'] == None)
        self.plate['A01'] = Sample(1,1,1)
        self.assertTrue(self.plate['A01'].all_data() == {'FAM' : 1, 'VIC' : 1, 'ROX' : 1, 'nFAM' : 1.0, 'nVIC' : 1.0, 'barcode' : ''})


    def test_plate_data_as_df(self):
    
        self.plate.sample_matrix = np.array([[Sample(1,1,1) for _ in range(24)] for _ in range(16)])
        self.plate.data_as_df()
        self.assertFalse((self.plate.df['FAM'] != 1).any())
        self.assertFalse((self.plate.df['VIC'] != 1).any())
        self.assertFalse((self.plate.df['ROX'] != 1).any())
        self.assertFalse((self.plate.df['nFAM'] != 1.0).any())
        self.assertFalse((self.plate.df['nVIC'] != 1.0).any())
        self.assertFalse((self.plate.df['barcode'] != '').any())
        self.assertFalse(self.plate.df['well'].equals(pd.Series([x + y for x in LETTERS for y in NUMBERS])))


    def test_plate_set_barcodes(self):
    
        self.plate.sample_matrix = np.array([[Sample(1,1,1) for _ in range(24)] for _ in range(16)])
        wells = [x + y for x in LETTERS for y in NUMBERS]
        self.plate.set_barcodes([(None, 'AAA', x) for x in wells])
        self.plate.data_as_df()
        self.assertFalse((self.plate.df['barcode'] != 'AAA').any())


    def test_plate_barcodes_from_matrix(self):
    
        self.plate.sample_matrix = np.array([[Sample(1,1,1) for _ in range(24)] for _ in range(16)])
        self.plate.barcodes_from_matrix(np.array([['AAA' for _ in range(24)] for _ in range(16)]))
        self.assertFalse((self.plate.df['barcode'] != 'AAA').any())


    def test_plate_get_lysis_and_elute_plates(self):
        mock_lims_response = [('INACT00000001', 'ELUTE00000001', 'A01'), ('INACT00000001', 'ELUTE00000001', 'E05'),
                                        ('INACT00000002', 'ELUTE00000002', 'K12'), ('INACT00000002', 'ELUTE00000002', 'G08'),
                                        ('INACT00000003', 'ELUTE00000003', 'F05'), ('INACT00000004', 'ELUTE00000004', 'L12')]
        self.plate = Plate('000001', 'POOL00000001')
        expected = {'Pool plate' : 'POOL00000001', 'Nexar' : '', 'Araya' : '', 'Hydrocycler' : '', 'Hamilton' : '', 
                'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'),
                'INACT00000001' : None, 'ELUTE00000001' : {}, 'INACT00000002' : None, 'ELUTE00000002' : {},
                'INACT00000003' : None, 'ELUTE00000003' : {}, 'INACT00000004' : None, 'ELUTE00000004' : {}}
        
        self.assertTrue(self.plate.get_lysis_and_elute_plates(mock_lims_response) == expected)


    def test_plate_find_instruments(self):
        mock_lysis_elute = {'Pool plate' : 'POOL00000001', 'Nexar' : '', 'Araya' : '', 'Hydrocycler' : '', 'Hamilton' : '', 
                'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'),
                'INACT00000001' : None, 'ELUTE00000001' : {}, 'INACT00000002' : None, 'ELUTE00000002' : {},
                'INACT00000003' : None, 'ELUTE00000003' : {}, 'INACT00000004' : None, 'ELUTE00000004' : {}}
        mock_lims_response = [('TEST123', 'POOL00000001'), ('TEST321', 'INACT00000001'), ('HAM_DWP_01', 'INACT00000001'),
                                        ('KF_01', 'ELUTE00000001'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000002'),
                                        ('DRAGONFLY_01', 'ELUTE00000001'), ('HAM_DWP_02', 'INACT00000002'), ('KF_02', 'ELUTE00000002'),
                                        ('HAM_DWP_03', 'INACT00000003'), ('KF_03', 'ELUTE00000003'), ('DRAGONFLY_03', 'ELUTE00000003'),
                                        ('HAM_DWP_04', 'INACT00000004'), ('KF_04', 'ELUTE00000004'), ('DRAGONFLY_04', 'ELUTE00000004'),
                                        ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001')]
        self.plate = Plate('000001', 'POOL00000001')
        expected = {'Pool plate' : 'POOL00000001', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_01', 'Hydrocycler' : 'HYDROCYCL_01', 
                    'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                    'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                    'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                    'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                    'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                    'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}
        self.plate.find_instruments(mock_lims_response, mock_lysis_elute)
        self.assertTrue(self.plate.instruments == expected)


    def test_plate_set_thresholds(self):
        plate1 = Plate('000001', 'POOL00000001')
        plate1.instruments = {'Pool self.plate' : 'POOL00000001', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_01', 'Hydrocycler' : 'HYDROCYCL_01', 
                    'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                    'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                    'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                    'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                    'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                    'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}
        plate1.set_thresholds()

        plate2 = Plate('000002', 'POOL00000002')
        plate2.instruments = {'Pool self.plate' : 'POOL00000002', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_02', 'Hydrocycler' : 'HYDROCYCL_01', 
                    'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                    'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                    'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                    'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                    'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                    'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}
        plate2.set_thresholds()

        self.assertTrue(plate1.thresholds == {
            'POSITIVE' : 9,
            'NEGATIVE' : 4,
            'nVIC' : 1,
            'LOW_ROX' : 1600,
            'HIGH_ROX' : 4000
        })

        self.assertTrue(plate2.thresholds == {
            'POSITIVE' : 9.5,
            'NEGATIVE' : 5,
            'nVIC' : 1.2,
            'LOW_ROX' : 1000,
            'HIGH_ROX' : 4000
        })


    def test_plate_set_araya_data(self):
        thresholds = {'POSITIVE' : 9, 'NEGATIVE' : 4, 'nVIC' : 1, 'LOW_ROX' : 1600, 'HIGH_ROX' : 5000}
        self.plate = Plate('000001', 'POOL00000001')
        self.plate.thresholds = thresholds
        araya_file = open('.//poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').readlines()
        self.plate.set_araya_data(araya_file)
        barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        barcodes[14:16, 18:24] = 'Con'
        self.plate.barcodes_from_matrix(barcodes)
        self.plate.data_as_df()
        self.plate.df.to_csv('temp.csv')
        self.assertTrue(self.plate.df.equals(pd.read_csv('.//poolFinder//unit_test_resources//expected_data//expected df1.csv')))


    def test_plate_create_matrices(self):
        thresholds = {'POSITIVE' : 9, 'NEGATIVE' : 4, 'nVIC' : 1, 'LOW_ROX' : 1600, 'HIGH_ROX' : 5000}
        self.plate = Plate('000001', 'POOL00000001')
        self.plate.thresholds = thresholds
        araya_file = open('.//poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').readlines()
        self.plate.set_araya_data(araya_file)
        barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        barcodes[14:16, 18:24] = 'Con'
        for row in range(8):
            for col in range(12):
                barcodes[row * 2 + 1, col * 2 + 1] = ''
        self.plate.barcodes_from_matrix(barcodes)
        self.plate.data_as_df()
        output = self.plate._create_matrices()
        wells = np.array([[LETTERS[y] + NUMBERS[x] for x in range(24)] for y in range(16)])
        barcodes = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//barcode_expected.csv', dtype = str, delimiter = ',')
        flags = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//flags_expected.csv', dtype = str, delimiter = ',')
        result = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//result_expected.csv', dtype = int, delimiter = ',')
        fam = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//fam_expected.csv', dtype = int, delimiter = ',')
        vic = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//vic_expected.csv', dtype = int, delimiter = ',')
        rox = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//rox_expected.csv', dtype = int, delimiter = ',')
        nfam = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//nfam_expected.csv', dtype = float, delimiter = ',')
        nvic = np.genfromtxt('.//poolFinder//unit_test_resources//expected_data//nvic_expected.csv', dtype = float, delimiter = ',')
        list_of_samples = []
        for row in range(16):
            for col in range(24):
                if wells[row,col][1] == '0':
                    wells[row,col] = wells[row,col][0] + wells[row,col][2]  # Removes the leading zeros is present
                list_of_samples.append(db_Sample(
                    plate = None,
                    x384_well = wells[row,col],
                    fam = fam[row,col],
                    vic = vic[row,col],
                    rox = rox[row,col],
                    nfam = nfam[row,col],
                    nvic = nvic[row,col],
                    flag = flags[row,col],
                    barcode = barcodes[row,col]
                ))
        self.assertEqual((output[1]['barcode_matrix'], barcodes).all())
        self.assertEqual((output[1]['result_matrix'], result).all())
        self.assertEqual((output[1]['flag_matrix'], flags).all())
        self.assertEqual([model_to_dict(x) for x in output[0]], [model_to_dict(x) for x in list_of_samples])


    def test_plate_plate_info(self):
        thresholds = {'POSITIVE' : 9, 'NEGATIVE' : 4, 'nVIC' : 1, 'LOW_ROX' : 1600, 'HIGH_ROX' : 5000}
        self.plate = Plate('000001', 'POOL00000001')
        self.plate.thresholds = thresholds
        araya_file = open('.//poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').readlines()
        self.plate.set_araya_data(araya_file)
        barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        barcodes[14:16, 18:24] = 'Con'
        for row in range(8):
            for col in range(12):
                barcodes[row * 2 + 1, col * 2 + 1] = ''
        self.plate.barcodes_from_matrix(barcodes)
        self.plate.data_as_df()
        self.plate._create_matrices()
        
        self.plate.instruments = {'Pool self.plate' : 'POOL00000001', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_01', 'Hydrocycler' : 'HYDROCYCL_01', 
                    'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                    'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                    'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                    'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                    'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                    'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}

        expected = {'plate_location': ('384', 'Q1', 'Q2', 'Q3', 'Q4'), 
                    'positives': [56, 19, 19, 18, 0], 'plods': [31, 10, 10, 11, 0], 'negatives': [126, 42, 42, 42, 0], 
                    'vic_fails': [42, 14, 14, 14, 0], 'total_samples': [279, 93, 93, 93, 0], 
                    'inact_plate': ['', 'INACT00000001', 'INACT00000002', 'INACT00000003', 'INACT00000004'], 
                    'nexar_or_dwp_ham': ['NEXAR_01', 'HAM_DWP_01', 'HAM_DWP_02', 'HAM_DWP_03', 'HAM_DWP_04'], 
                    'araya_or_elute': ['ARAYA_01', 'ELUTE00000001', 'ELUTE00000002', 'ELUTE00000003', 'ELUTE00000004'], 
                    'hydrocycler_or_kf': ['HYDROCYCL_01', 'KF_01', 'KF_02', 'KF_03', 'KF_04'], 
                    'df_or_384_ham': ['HAM_384_01', 'DRAGONFLY_01', 'DRAGONFLY_02', 'DRAGONFLY_03', 'DRAGONFLY_04']}

        self.plate.plate_info()
        self.assertTrue(self.plate.info == expected)


    def test_plate_rox_box(self):
        thresholds = {'POSITIVE' : 9, 'NEGATIVE' : 4, 'nVIC' : 1, 'LOW_ROX' : 1600, 'HIGH_ROX' : 5000}
        self.plate = Plate('000001', 'POOL00000001')
        self.plate.thresholds = thresholds
        araya_file = open('.//poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').readlines()
        self.plate.set_araya_data(araya_file)
        barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        barcodes[14:16, 18:24] = 'Con'
        for row in range(8):
            for col in range(12):
                barcodes[row * 2 + 1, col * 2 + 1] = ''
        self.plate.barcodes_from_matrix(barcodes)
        self.plate.data_as_df()
        expected = {'Average ROX' : 3635, 'Standard Deviation' : 1052, 'Total ROX < Threshold' : 35, 
        'Patient ROX < Threshold' : 24, 'ROX >= Threshold' : 4}
        self.plate.rox_box()
        self.assertTrue(self.plate.roxbox == expected)


    def test_plate_quadrant_statistics(self):
        self.plate = Plate('000001', 'POOL00000001')
        quadrant_matrices = {
            'barcode_matrix': np.array([['AAA', 'AAA', ''], ['', 'AAA', ''], ['Con', '', 'Con']]),
            'result_matrix': np.array([[2, 2, 0], [0, 1, 1], [2, 0, 1]]),
            'total': 0,
            'pos': 0
        }
        quadrant_matrices = self.plate._quadrant_statistics(quadrant_matrices)
        self.assertTrue(quadrant_matrices['total'] == 3)
        self.assertTrue(quadrant_matrices['pos'] == 2)


    def test_plate_find_esclations_and_stripes(self):
        thresholds = {'POSITIVE' : 9, 'NEGATIVE' : 4, 'nVIC' : 1, 'LOW_ROX' : 1600, 'HIGH_ROX' : 5000}
        self.plate = Plate('000001', 'POOL00000001')
        self.plate.thresholds = thresholds
        araya_file = open('.//poolFinder//unit_test_resources//test_data//test-araya_000001.csv', 'r').readlines()
        self.plate.set_araya_data(araya_file)

        barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        barcodes[14:16, 18:24] = 'Con'
        for row in range(8):
            for col in range(12):
                barcodes[row * 2 + 1, col * 2 + 1] = ''
        self.plate.barcodes_from_matrix(barcodes)
        self.plate.data_as_df()

        flags_post_stripe_analysis = open('.//poolFinder//unit_test_resources//expected_data//flags_post_stripe_expected.csv', 'r').read()
        flags_post_stripe_analysis = flags_post_stripe_analysis.replace('\n', ',').replace('\r', '').split(',')[:-1]

        #plate.find_instruments()
        list_of_samples, matrices = self.plate._create_matrices()
        self.plate._find_esclations_and_stripes(matrices, list_of_samples)

        self.assertTrue([x.flag for x in list_of_samples] == flags_post_stripe_analysis)

        self.assertTrue('21 or more RNaseP failures' in self.plate.escalations)
        self.assertTrue('3 or more ROX fails' in self.plate.escalations)
        self.assertTrue('Both positive controls on Q1 have failed' in self.plate.escalations)
        self.assertTrue('Both positive controls on Q2 have failed' in self.plate.escalations)
        self.assertTrue('The qnostic has failed on Q3, and the accuplex in the same quadrant contains RNaseP' in self.plate.escalations)
        self.assertTrue('Negcon fail on Q1 has invalidated samples' in self.plate.escalations)
        self.assertTrue('Negcon fail on Q2 has invalidated samples' in self.plate.escalations)
        self.assertTrue('Negcon fail on Q3 has invalidated samples' in self.plate.escalations)
        self.assertTrue('21 or more RNaseP failures' in self.plate.escalations)
        self.assertTrue('3 or more ROX fails' in self.plate.escalations)


    def test_plate_get_comments(self):
        mock_lims_response = [('Pool plate comment', 'POOL00000001'), 
                                        ('Elute 1 comment', 'ELUTE00000001'), ('Inact 1 comment', 'INACT00000001'),
                                        ('Elute 2 comment', 'ELUTE00000002'), ('Inact 2 comment', 'INACT00000002'),
                                        ('Elute 3 comment', 'ELUTE00000003'), ('Inact 3 comment', 'INACT00000003'),
                                        ('Elute 4 comment', 'ELUTE00000004'), ('Inact 4 comment', 'INACT00000004'),
                                        ('Elute 1 comment 2', 'ELUTE00000001')]
        
        self.plate = Plate('000001', 'POOL00000001')
        self.plate.sample_matrix = np.array([[Sample(1,1,1) for _ in range(24)] for _ in range(16)])
        
        self.plate.instruments = {'Pool plate' : 'POOL00000001', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_01', 'Hydrocycler' : 'HYDROCYCL_01', 
                    'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                    'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                    'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                    'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                    'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                    'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}
        
        self.plate.get_comments(pd.DataFrame(mock_lims_response, columns = ('comment', 'plate')))
        self.assertTrue(self.plate.comments == {
            'Q1': {'INACT00000001': ['Inact 1 comment'], 'ELUTE00000001': ['Elute 1 comment', 'Elute 1 comment 2']}, 
            'Q2': {'INACT00000002': ['Inact 2 comment'], 'ELUTE00000002': ['Elute 2 comment']}, 
            'Q3': {'INACT00000003': ['Inact 3 comment'], 'ELUTE00000003': ['Elute 3 comment']}, 
            'Q4': {'INACT00000004': ['Inact 4 comment'], 'ELUTE00000004': ['Elute 4 comment']}, 
            'Pool': ['Pool plate comment']
        })


    def test_plate_check_if_prio(self):
        plate1 = Plate('000001', 'POOL00000001')
        plate1.sample_matrix = np.array([[Sample(1,1,1, 'AVA') for _ in range(24)] for _ in range(16)])
        plate1.formatted_info['comments'] = ''
        plate1.data_as_df()
        
        plate2 = Plate('000001', 'POOL00000001')
        plate2.sample_matrix = np.array([[Sample(1,1,1, 'AAA') for _ in range(24)] for _ in range(16)])
        plate2.formatted_info['comments'] = 'priority'
        plate2.data_as_df()

        plate3 = Plate('000001', 'POOL00000001')
        plate3.sample_matrix = np.array([[Sample(1,1,1, 'AAA') for _ in range(24)] for _ in range(16)])
        plate3.formatted_info['comments'] = ''
        plate3.data_as_df()

        self.assertTrue(plate1.check_if_prio())
        self.assertTrue(plate2.check_if_prio())
        self.assertFalse(plate3.check_if_prio())


    def test_plate_check_if_vip(self):
        plate1 = Plate('000001', 'POOL00000001')
        plate1.sample_matrix = np.array([[Sample(1,1,1, 'AVA') for _ in range(24)] for _ in range(16)])
        plate1.formatted_info['comments'] = 'this self.plate is VIP'
        plate1.data_as_df()
        
        plate2 = Plate('000001', 'POOL00000001')
        plate2.sample_matrix = np.array([[Sample(1,1,1, 'AAA') for _ in range(24)] for _ in range(16)])
        plate2.formatted_info['comments'] = '(VIP)'
        plate2.data_as_df()

        plate3 = Plate('000001', 'POOL00000001')
        plate3.sample_matrix = np.array([[Sample(1,1,1, 'AAA') for _ in range(24)] for _ in range(16)])
        plate3.formatted_info['comments'] = 'priority'
        plate3.data_as_df()

        self.assertTrue(plate1.check_if_vip())
        self.assertTrue(plate2.check_if_vip())
        self.assertFalse(plate3.check_if_vip())

    def test_plate_create_unique_platename(self):
        self.plate.set_unique_platename()
        self.assertTrue(self.plate.unique_platename == '000001 1')

    def test_plate_save_samples_to_db(self):
        self.plate.sample_db_objects = [db_Sample(
            plate = None,
            x384_well = str(x),
            fam = 0,
            vic = 0,
            rox = 0,
            nfam = 0,
            nvic = 0,
            flag = 'warning',
            barcode = 'AAA'
        ) for x in range(10)]
        self.plate._save_samples_to_db(AnalysedPlate.objects.all().first(), '000001 - 000016')

        self.assertTrue(len(db_Sample.objects.all()) == 10)
