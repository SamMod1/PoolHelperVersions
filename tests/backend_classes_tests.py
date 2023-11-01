"python -m pytest tests/backend_classes_tests.py"


import jinja2
import numpy as np
import pandas as pd
import src.functions as f
import src.backend_classes as bc 
from unittest.mock import patch, MagicMock
from Pool_Helper_Config_Encryptor.poolHelperConfig import GLOBALS, THRESHOLDS


LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
NUMBERS = ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17',
           '18', '19', '20', '21', '22', '23', '24')


class MockPlate:
    def __init__(self):
        self.date = "2022:05:27"
        
        
class MockAnalysis(bc.Analysis):
    def __init__(self, first_araya, cur, admin = False, from_files = False, mirrorless = False, filepath = './/Araya Files//'):
        self.plates = {first_araya : MockPlate}
        self.globals = GLOBALS
        self.thresholds = THRESHOLDS
        self.html = self.globals['HTML_FIRST_TAB']
        self.cur = cur
        self.admin = False
        #bc.Analysis.get_araya()


def test_sample_all_data():
    samp = bc.Sample(1,1,1)
    assert samp.all_data() == {'FAM' : 1, 'VIC' : 1, 'ROX' : 1, 'nFAM' : 1.0, 'nVIC' : 1.0, 'barcode' : ''}

def test_sample_set_barcode():
    samp = bc.Sample(1,1,1)
    samp.set_barcode('AAA')
    assert samp.barcode == 'AAA'
    
def test_plate_get_set_item():
    cur = MagicMock()
    plate = bc.Plate(None, '000001', {'HTML_PLATE_TAB' : ''}, {}, cur, 'date')
    assert plate['A01'] == None
    plate['A01'] = bc.Sample(1,1,1)
    assert plate['A01'].all_data() == {'FAM' : 1, 'VIC' : 1, 'ROX' : 1, 'nFAM' : 1.0, 'nVIC' : 1.0, 'barcode' : ''}

def test_plate_data_as_df():
    cur = MagicMock()
    plate = bc.Plate(None, '000001', {'HTML_PLATE_TAB' : ''}, {}, cur, 'date')
    plate.sample_matrix = np.array([[bc.Sample(1,1,1) for _ in range(24)] for _ in range(16)])
    plate.data_as_df()
    assert not (plate.df['FAM'] != 1).any()
    assert not (plate.df['VIC'] != 1).any()
    assert not (plate.df['ROX'] != 1).any()
    assert not (plate.df['nFAM'] != 1.0).any()
    assert not (plate.df['nVIC'] != 1.0).any()
    assert not (plate.df['barcode'] != '').any()
    assert not plate.df['well'].equals(pd.Series([x + y for x in LETTERS for y in NUMBERS]))

def test_plate_set_barcodes():
    cur = MagicMock()
    plate = bc.Plate(None, '000001', {'HTML_PLATE_TAB' : ''}, {}, cur, 'date')
    plate.sample_matrix = np.array([[bc.Sample(1,1,1) for _ in range(24)] for _ in range(16)])
    wells = [x + y for x in LETTERS for y in NUMBERS]
    plate.set_barcodes([(None, 'AAA', x) for x in wells])
    assert not (plate.df['barcode'] != 'AAA').any()
    
def test_plate_barcodes_from_matrix():
    cur = MagicMock()
    plate = bc.Plate(None, '000001', {'HTML_PLATE_TAB' : ''}, {}, cur, 'date')
    plate.sample_matrix = np.array([[bc.Sample(1,1,1) for _ in range(24)] for _ in range(16)])
    plate.barcodes_from_matrix(np.array([['AAA' for _ in range(24)] for _ in range(16)]))
    assert not (plate.df['barcode'] != 'AAA').any()

@patch("src.functions.lims_query")
def test_plate_lysis_elute(mock_lims_query):
    mock_lims_query.return_value = [('INACT00000001', 'ELUTE00000001', 'A01'), ('INACT00000001', 'ELUTE00000001', 'E05'),
                                    ('INACT00000002', 'ELUTE00000002', 'K12'), ('INACT00000002', 'ELUTE00000002', 'G08'),
                                    ('INACT00000003', 'ELUTE00000003', 'F05'), ('INACT00000004', 'ELUTE00000004', 'L12')]
    cur = MagicMock()
    plate = bc.Plate('POOL00000001', '000001', GLOBALS, {}, cur, 'date')
    expected = {'Pool plate' : 'POOL00000001', 'Nexar' : '', 'Araya' : '', 'Hydrocycler' : '', 'Hamilton' : '', 
              'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
              'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'),
              'INACT00000001' : None, 'ELUTE00000001' : {}, 'INACT00000002' : None, 'ELUTE00000002' : {},
              'INACT00000003' : None, 'ELUTE00000003' : {}, 'INACT00000004' : None, 'ELUTE00000004' : {}}
    
    assert plate._lysis_elute() == expected

@patch("src.functions.lims_query")
@patch("src.backend_classes.Plate._lysis_elute")
def test_plate_find_instruments(mock_lysis_elute, mock_lims_query):
    mock_lysis_elute.return_value = {'Pool plate' : 'POOL00000001', 'Nexar' : '', 'Araya' : '', 'Hydrocycler' : '', 'Hamilton' : '', 
              'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
              'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'),
              'INACT00000001' : None, 'ELUTE00000001' : {}, 'INACT00000002' : None, 'ELUTE00000002' : {},
              'INACT00000003' : None, 'ELUTE00000003' : {}, 'INACT00000004' : None, 'ELUTE00000004' : {}}
    mock_lims_query.return_value = [('TEST123', 'POOL00000001'), ('TEST321', 'INACT00000001'), ('HAM_DWP_01', 'INACT00000001'),
                                    ('KF_01', 'ELUTE00000001'), ('ARAYA_01', 'POOL00000001'), ('DRAGONFLY_02', 'ELUTE00000002'),
                                    ('DRAGONFLY_01', 'ELUTE00000001'), ('HAM_DWP_02', 'INACT00000002'), ('KF_02', 'ELUTE00000002'),
                                    ('HAM_DWP_03', 'INACT00000003'), ('KF_03', 'ELUTE00000003'), ('DRAGONFLY_03', 'ELUTE00000003'),
                                    ('HAM_DWP_04', 'INACT00000004'), ('KF_04', 'ELUTE00000004'), ('DRAGONFLY_04', 'ELUTE00000004'),
                                    ('NEXAR_01', 'POOL00000001'), ('HYDROCYCL_01', 'POOL00000001'), ('HAM_384_01', 'POOL00000001')]
    cur = MagicMock()
    plate = bc.Plate('POOL00000001', '000001', GLOBALS, {}, cur, 'date')
    expected = {'Pool plate' : 'POOL00000001', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_01', 'Hydrocycler' : 'HYDROCYCL_01', 
                 'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                 'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                 'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                 'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                 'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                 'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}
    plate.find_instruments()
    assert plate.instruments == expected
    
@patch("src.functions.lims_query")
def test_plate_create_matrices(mock_lims_query):
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    global_variables = {'NON_PATIENT_CODES' : ['', 'Con', 'SPA'], 'ACCUPLEX_WELLS' : ('O19', 'O20', 'P19', 'P20'), 
                     'QNOS_WELLS' : ('O23', 'O24', 'P23', 'P24'), 'NEGCON_WELLS' : ('O21', 'O22', 'P21', 'P22'),
                     'SOP_nVIC_ESCALATION_LIMIT' : (10, 3), 'SOP_ROX_FAIL_LIMIT' : (3, 2), 'SOP_PLOD_LIMIT' : (6, 'consult service guidance'),
                     'MM_ONLY_RULES' : dict(MIN_ROX = 1000, MAX_nVIC = 0.5, FAM_TO_VIC_LIMS = [1.25, 2.75]), 'HTML_PLATE_TAB' : ''}
    plate = f.pipe('', global_variables, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                   './/tests//', True)['000001']
    plate.data_as_df()
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    plate.barcodes_from_matrix(barcodes)
    output = plate._create_matrices()
    barcodes = np.genfromtxt('.//tests//expected//barcode_expected.csv', dtype = str, delimiter = ',')
    flags = np.genfromtxt('.//tests//expected//flags_expected.csv', dtype = str, delimiter = ',')
    result = np.genfromtxt('.//tests//expected//result_expected.csv', dtype = int, delimiter = ',')
    vic_result = np.genfromtxt('.//tests//expected//vic_result_expected.csv', dtype = int, delimiter = ',')
    fam = np.genfromtxt('.//tests//expected//fam_expected.csv', dtype = int, delimiter = ',')
    vic = np.genfromtxt('.//tests//expected//vic_expected.csv', dtype = int, delimiter = ',')
    rox = np.genfromtxt('.//tests//expected//rox_expected.csv', dtype = int, delimiter = ',')
    nfam = np.genfromtxt('.//tests//expected//nfam_expected.csv', dtype = float, delimiter = ',')
    nvic = np.genfromtxt('.//tests//expected//nvic_expected.csv', dtype = float, delimiter = ',')
    nfam = nfam.astype(str)
    nvic = nvic.astype(str)
    assert (output['vic_matrix'] == vic).all()
    assert (output['rox_matrix'] == rox).all()
    assert (output['fam_matrix'] == fam).all()
    assert (output['barcode_matrix'] == barcodes).all()
    assert (output['nvic_matrix'] == nvic).all()
    assert (output['nfam_matrix'] == nfam).all()
    assert (output['vic_result_matrix'] == vic_result).all()
    assert (output['result_matrix'] == result).all()
    assert (output['flag_matrix'] == flags).all()

    
@patch("src.functions.lims_query")
def test_plate_plate_info(mock_lims_query):
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    plate = f.pipe('', GLOBALS, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']], 
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    plate.data_as_df()
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    plate.barcodes_from_matrix(barcodes)
    plate.find_instruments()
    plate._create_matrices()
    plate.instruments = {'Pool plate' : 'POOL00000001', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_01', 'Hydrocycler' : 'HYDROCYCL_01', 
                 'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                 'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                 'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                 'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                 'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                 'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}
    expected = {'000001': ('POOL00000001', '', 'Q1', 'Q2', 'Q3', 'Q4'), 
                'Positives': ['56 (20.07%)', '', '19 (20.43%)', '19 (20.43%)', '18 (19.35%)', 0],
                'PLODs': ['31 (11.11%, 7 high)', '', 10, 10, 11, 0], 'Negatives': [126, '', 42, 42, 42, 0], 
                'VIC Failures' : [42, '', 14, 14, 14, 0], 'Total Samples' : [279, '', 93, 93, 93, 0],
                '': ['','','','','',''], 'Instrument info': ['', '', 'INACT00000001', 'INACT00000002', 'INACT00000003', 'INACT00000004'],
                'Nexar': ['NEXAR_01', '', 'HAM_DWP_01', 'HAM_DWP_02', 'HAM_DWP_03', 'HAM_DWP_04'],
                'Araya': ['ARAYA_01', '', 'ELUTE00000001', 'ELUTE00000002', 'ELUTE00000003', 'ELUTE00000004'],
                'Hydrocycler': ['HYDROCYCL_01', '', 'KF_01', 'KF_02', 'KF_03', 'KF_04'],
                '384 Hamilton': ['HAM_384_01', '', 'DRAGONFLY_01', 'DRAGONFLY_02', 'DRAGONFLY_03', 'DRAGONFLY_04']}
    plate.plate_info()
    assert plate.info == expected

def test_plate_rox_box():
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    global_variables = {'NON_PATIENT_CODES' : ['', 'Con', 'SPA'], 'ACCUPLEX_WELLS' : ('O19', 'O20', 'P19', 'P20'), 
                     'QNOS_WELLS' : ('O23', 'O24', 'P23', 'P24'), 'NEGCON_WELLS' : ('O21', 'O22', 'P21', 'P22'),
                     'SOP_nVIC_ESCALATION_LIMIT' : (10, 3), 'SOP_ROX_FAIL_LIMIT' : (3, 2), 'SOP_PLOD_LIMIT' : (6, 'consult service guidance'),
                     'MM_ONLY_RULES' : dict(MIN_ROX = 1000, MAX_nVIC = 0.5, FAM_TO_VIC_LIMS = [1.25, 2.75]), 'HTML_PLATE_TAB' : ''}
    plate = f.pipe('', global_variables, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    plate.barcodes_from_matrix(barcodes)
    plate.data_as_df()
    expected = {'Average ROX' : ['3635 RFU'], 'Standard Deviation' : [1052], 'CV' : ['28.95%'], 'ROX < 1600' : '35 (24 patient)', 'ROX >= 5000' : 4}
    assert plate.rox_box() == expected
    
def test_plate_detect_escalations_384():
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    global_variables = {'NON_PATIENT_CODES' : ['', 'Con', 'SPA'], 'ACCUPLEX_WELLS' : ('O19', 'O20', 'P19', 'P20'), 
                     'QNOS_WELLS' : ('O23', 'O24', 'P23', 'P24'), 'NEGCON_WELLS' : ('O21', 'O22', 'P21', 'P22'),
                     'SOP_nVIC_ESCALATION_LIMIT' : (10, 3), 'SOP_ROX_FAIL_LIMIT' : (3, 2), 'SOP_PLOD_LIMIT' : (6, 'consult service guidance'),
                     'MM_ONLY_RULES' : dict(MIN_ROX = 1000, MAX_nVIC = 0.5, FAM_TO_VIC_LIMS = [1.25, 2.75]), 'HTML_PLATE_TAB' : '',
                     'x96_CONTROL_WELLS' : ((7,11), (7,10), (7,9)), 'STRIPE_LIMIT' : (4, 5), 'STIPE_CHECK_LIMIT' : 22, 'REPOOL_CHECK' : False,
                     'RESULT_COLOURS' : ["rgb(0, 180, 0)", "rgb(255, 183, 71)", "rgb(227, 5, 19)"], 'BACKGROUND_COLOUR' : "rgb(235,235,235)",
                     'LY_EL_QUERY' : "select LYSIS_PLATE, ELUTION_PLATE, PLATE_COORDINATE from SAMPLE where JOB_NAME = '$pool' and PLATE_COORDINATE in $wells",
                     'INSTRUMENTS_QUERY' : "select VALUE, JOB from JOB_PARAMETER where JOB in $plates"}
    plate = f.pipe('', global_variables, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    plate.data_as_df()
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    plate.barcodes_from_matrix(barcodes)
    plate.find_instruments()
    plate.create_platemaps()
    assert 'Level 2 - Both positive controls on Q1 have failed' in plate.escalations
    assert 'Level 2 - Both positive controls on Q2 have failed' in plate.escalations
    assert 'Level 2 - The qnostic has failed on Q3, and the accuplex in the same quadrant contains RNaseP' in plate.escalations
    assert 'Level 2 - Negcon fail on Q1 has invalidated samples' in plate.escalations
    assert 'Level 2 - Negcon fail on Q2 has invalidated samples' in plate.escalations
    assert 'Level 2 - Negcon fail on Q3 has invalidated samples' in plate.escalations
    assert 'Level 3 - 10 or more RNaseP failures' in plate.escalations
    assert 'Level 2 - 3 or more ROX fails' in plate.escalations
    assert 'Level consult service guidance - 6 or more PLODs' in plate.escalations

def test_plate_quadrant_matrices():
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    plate = f.pipe('', GLOBALS, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    plate.data_as_df()
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    plate.barcodes_from_matrix(barcodes)
    plate.find_instruments()
    plate.create_platemaps()
    barcodes123 = np.genfromtxt('.//tests//expected//barcodes_q123.csv', dtype = str, delimiter = ',')
    assert ((plate.matrices['Q1']['barcode_matrix'] == barcodes123) & (plate.matrices['Q2']['barcode_matrix'] == barcodes123)
            & (plate.matrices['Q3']['barcode_matrix'] == barcodes123) & 
            (plate.matrices['Q4']['barcode_matrix'] == np.array([['' for _ in range(12)] for _ in range(8)]))).all()
    assert (plate.matrices['Q1']['fam_matrix'] ==  np.genfromtxt('.//tests//expected//fam_q1.csv', dtype = int, delimiter = ',')).all()
    assert (plate.matrices['Q2']['fam_matrix'] ==  np.genfromtxt('.//tests//expected//fam_q2.csv', dtype = int, delimiter = ',')).all()
    assert (plate.matrices['Q3']['fam_matrix'] ==  np.genfromtxt('.//tests//expected//fam_q3.csv', dtype = int, delimiter = ',')).all()
    assert (plate.matrices['Q4']['fam_matrix'] ==  np.genfromtxt('.//tests//expected//fam_q4.csv', dtype = int, delimiter = ',')).all()
    assert (plate.matrices['Q1']['flag_matrix'] ==  np.genfromtxt('.//tests//expected//flags_q1.csv', dtype = str, delimiter = ',')).all()
    assert (plate.matrices['Q2']['flag_matrix'] ==  np.genfromtxt('.//tests//expected//flags_q2.csv', dtype = str, delimiter = ',')).all()
    assert (plate.matrices['Q3']['flag_matrix'] ==  np.genfromtxt('.//tests//expected//flags_q3.csv', dtype = str, delimiter = ',')).all()
    assert (plate.matrices['Q4']['flag_matrix'] ==  np.genfromtxt('.//tests//expected//flags_q4.csv', dtype = str, delimiter = ',')).all()
    assert (plate.matrices['Q1']['nfam_matrix'] ==  np.genfromtxt('.//tests//expected//nfam_q1.csv', dtype = float, delimiter = ',').astype(str)).all()
    assert (plate.matrices['Q2']['nfam_matrix'] ==  np.genfromtxt('.//tests//expected//nfam_q2.csv', dtype = float, delimiter = ',').astype(str)).all()
    assert (plate.matrices['Q3']['nfam_matrix'] ==  np.genfromtxt('.//tests//expected//nfam_q3.csv', dtype = float, delimiter = ',').astype(str)).all()
    assert (plate.matrices['Q4']['nfam_matrix'] ==  np.genfromtxt('.//tests//expected//nfam_q4.csv', dtype = float, delimiter = ',').astype(str)).all()
    assert (plate.matrices['Q1']['nvic_matrix'] ==  np.genfromtxt('.//tests//expected//nvic_q1.csv', dtype = float, delimiter = ',').astype(str)).all()
    assert (plate.matrices['Q2']['nvic_matrix'] ==  np.genfromtxt('.//tests//expected//nvic_q2.csv', dtype = float, delimiter = ',').astype(str)).all()
    assert (plate.matrices['Q3']['nvic_matrix'] ==  np.genfromtxt('.//tests//expected//nvic_q3.csv', dtype = float, delimiter = ',').astype(str)).all()
    assert (plate.matrices['Q4']['nvic_matrix'] ==  np.genfromtxt('.//tests//expected//nvic_q4.csv', dtype = float, delimiter = ',').astype(str)).all()

def test_plate_create_platemaps():
    """All of the sub functions this uses are tested individually, so this just tests to see if the function makes all of the platemaps successfully"""
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    plate = f.pipe('', GLOBALS, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    plate.data_as_df()
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    plate.barcodes_from_matrix(barcodes)
    plate.find_instruments()
    plate.create_platemaps()
    assert type(plate.platemaps['384']) == jinja2.environment.Template
    assert type(plate.platemaps['Q1']) == jinja2.environment.Template
    assert type(plate.platemaps['Q2']) == jinja2.environment.Template
    assert type(plate.platemaps['Q3']) == jinja2.environment.Template
    assert type(plate.platemaps['Q4']) == jinja2.environment.Template
    
def test_plate_scatter_charts():
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    global_variables = {'NON_PATIENT_CODES' : ['', 'Con', 'SPA'], 'ACCUPLEX_WELLS' : ('O19', 'O20', 'P19', 'P20'), 
                     'QNOS_WELLS' : ('O23', 'O24', 'P23', 'P24'), 'NEGCON_WELLS' : ('O21', 'O22', 'P21', 'P22'),
                     'SOP_nVIC_ESCALATION_LIMIT' : (10, 3), 'SOP_ROX_FAIL_LIMIT' : (3, 2), 'SOP_PLOD_LIMIT' : (6, 'consult service guidance'),
                     'MM_ONLY_RULES' : dict(MIN_ROX = 1000, MAX_nVIC = 0.5, FAM_TO_VIC_LIMS = [1.25, 2.75]), 'HTML_PLATE_TAB' : '',
                     'x96_CONTROL_WELLS' : ((7,11), (7,10), (7,9)), 'STRIPE_LIMIT' : (4, 5), 'STIPE_CHECK_LIMIT' : 22, 
                     'RESULT_COLOURS' : ["rgb(0, 180, 0)", "rgb(255, 183, 71)", "rgb(227, 5, 19)"], 'BACKGROUND_COLOUR' : "rgb(235,235,235)",
                     'GRAPH_LINE_SIZE' : 3}
    plate = f.pipe('', global_variables, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']], 
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    plate.data_as_df()
    assert type(plate.scatter_charts()['rvf']) == jinja2.environment.Template
    assert type(plate.scatter_charts()['rvnf']) == jinja2.environment.Template
    assert type(plate.scatter_charts()['rvv']) == jinja2.environment.Template
    assert type(plate.scatter_charts()['rvnv']) == jinja2.environment.Template
    assert type(plate.scatter_charts()['nfvnv']) == jinja2.environment.Template
    
def check_plate_check_plate_flip():
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    global_variables = {'NON_PATIENT_CODES' : ['', 'Con', 'SPA'], 'ACCUPLEX_WELLS' : ('O19', 'O20', 'P19', 'P20'), 
                     'QNOS_WELLS' : ('O23', 'O24', 'P23', 'P24'), 'NEGCON_WELLS' : ('O21', 'O22', 'P21', 'P22'),
                     'SOP_nVIC_ESCALATION_LIMIT' : (10, 3), 'SOP_ROX_FAIL_LIMIT' : (3, 2), 'SOP_PLOD_LIMIT' : (6, 'consult service guidance'),
                     'MM_ONLY_RULES' : dict(MIN_ROX = 1000, MAX_nVIC = 0.5, FAM_TO_VIC_LIMS = [1.25, 2.75]), 'HTML_PLATE_TAB' : '',
                     'x96_CONTROL_WELLS' : ((7,11), (7,10), (7,9)), 'STRIPE_LIMIT' : (4, 5), 'STIPE_CHECK_LIMIT' : 22, 
                     'RESULT_COLOURS' : ["rgb(0, 180, 0)", "rgb(255, 183, 71)", "rgb(227, 5, 19)"], 'BACKGROUND_COLOUR' : "rgb(235,235,235)",
                     'GRAPH_LINE_SIZE' : 3}
    plates = f.pipe('', global_variables, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                    './/tests//', True)
    plate1 = plates['000002']
    plate1.pool = 'POOL00000001'
    plate1.data_as_df()
    plate2 = plates['000001']
    plate2.pool = 'POOL00000001'
    plate2.data_as_df()
    assert plate1.check_plate_flip()
    assert not plate2.check_plate_flip()

@patch("src.functions.lims_query")
def test_plate_get_comments(mock_lims_query):
    mock_lims_query.return_value = [('Pool plate comment', 'POOL00000001'), 
                                    ('Elute 1 comment', 'ELUTE00000001'), ('Inact 1 comment', 'INACT00000001'),
                                    ('Elute 2 comment', 'ELUTE00000002'), ('Inact 2 comment', 'INACT00000002'),
                                    ('Elute 3 comment', 'ELUTE00000003'), ('Inact 3 comment', 'INACT00000003'),
                                    ('Elute 4 comment', 'ELUTE00000004'), ('Inact 4 comment', 'INACT00000004')]
    
    cur = MagicMock()
    plate = bc.Plate(None, '000001', GLOBALS, {}, cur, 'date')
    plate.sample_matrix = np.array([[bc.Sample(1,1,1) for _ in range(24)] for _ in range(16)])
    
    plate.instruments = {'Pool plate' : 'POOL00000001', 'Nexar' : 'NEXAR_01', 'Araya' : 'ARAYA_01', 'Hydrocycler' : 'HYDROCYCL_01', 
                 'Hamilton' : 'HAM_384_01', 'Q1' : ('INACT00000001','ELUTE00000001'), 'Q2' : ('INACT00000002','ELUTE00000002'), 
                 'Q3' : ('INACT00000003','ELUTE00000003'), 'Q4' : ('INACT00000004','ELUTE00000004'), 'INACT00000001' : 'HAM_DWP_01', 
                 'ELUTE00000001' : {0 : 'KF_01', 1 : 'DRAGONFLY_01'}, 'INACT00000002' : 'HAM_DWP_02', 
                 'ELUTE00000002' : {0 : 'KF_02', 1 : 'DRAGONFLY_02'}, 'INACT00000003' : 'HAM_DWP_03', 
                 'ELUTE00000003' : {0 : 'KF_03', 1 : 'DRAGONFLY_03'}, 'INACT00000004' : 'HAM_DWP_04', 
                 'ELUTE00000004' : {0 : 'KF_04', 1 : 'DRAGONFLY_04'}, '' : '  '}
    
    plate.get_comments()
    assert plate.comments == """<br>Pool plate:<br><span style = "color:red;">Pool plate comment</span><br><br>INACT00000001 (Q1):<br><span style = "color:red;">Inact 1 comment</span><br><br>ELUTE00000001 (Q1):<br><span style = "color:red;">Elute 1 comment</span><br><br>INACT00000002 (Q2):<br><span style = "color:red;">Inact 2 comment</span><br><br>ELUTE00000002 (Q2):<br><span style = "color:red;">Elute 2 comment</span><br><br>INACT00000003 (Q3):<br><span style = "color:red;">Inact 3 comment</span><br><br>ELUTE00000003 (Q3):<br><span style = "color:red;">Elute 3 comment</span><br><br>INACT00000004 (Q4):<br><span style = "color:red;">Inact 4 comment</span><br><br>ELUTE00000004 (Q4):<br><span style = "color:red;">Elute 4 comment</span><br><br>"""

def test_plate_check_if_prio():
    cur = MagicMock()
    plate1 = bc.Plate(None, '000001', {'HTML_PLATE_TAB' : '', 'PRIO_CODES' : ['AVA', 'PRK']}, {}, cur, 'date')
    plate1.sample_matrix = np.array([[bc.Sample(1,1,1, 'AVA') for _ in range(24)] for _ in range(16)])
    plate1.comments = ''
    plate1.data_as_df()
    
    plate2 = bc.Plate(None, '000001', {'HTML_PLATE_TAB' : '', 'PRIO_CODES' : ['AVA', 'PRK']}, {}, cur, 'date')
    plate2.sample_matrix = np.array([[bc.Sample(1,1,1, 'AAA') for _ in range(24)] for _ in range(16)])
    plate2.comments = 'priority'
    plate2.data_as_df()

    plate4 = bc.Plate(None, '000001', {'HTML_PLATE_TAB' : '', 'PRIO_CODES' : ['AVA', 'PRK']}, {}, cur, 'date')
    plate4.sample_matrix = np.array([[bc.Sample(1,1,1, 'AAA') for _ in range(24)] for _ in range(16)])
    plate4.comments = ''
    plate4.data_as_df()

    assert plate1.check_if_prio()
    assert plate2.check_if_prio()
    assert not plate4.check_if_prio()
    
def test_plate_create_tab():
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    global_variables = {'NON_PATIENT_CODES' : ['', 'Con', 'SPA'], 'ACCUPLEX_WELLS' : ('O19', 'O20', 'P19', 'P20'), 
                     'QNOS_WELLS' : ('O23', 'O24', 'P23', 'P24'), 'NEGCON_WELLS' : ('O21', 'O22', 'P21', 'P22'),
                     'SOP_nVIC_ESCALATION_LIMIT' : (10, 3), 'SOP_ROX_FAIL_LIMIT' : (3, 2), 'SOP_PLOD_LIMIT' : (6, 'consult service guidance'),
                     'MM_ONLY_RULES' : dict(MIN_ROX = 1000, MAX_nVIC = 0.5, FAM_TO_VIC_LIMS = [1.25, 2.75]), 'HTML_PLATE_TAB' : '',
                     'x96_CONTROL_WELLS' : ((7,11), (7,10), (7,9)), 'STRIPE_LIMIT' : (4, 5), 'STIPE_CHECK_LIMIT' : 22, 
                     'RESULT_COLOURS' : ["rgb(0, 180, 0)", "rgb(255, 183, 71)", "rgb(227, 5, 19)"], 'BACKGROUND_COLOUR' : "rgb(235,235,235)",
                     'GRAPH_LINE_SIZE' : 3}
    plate = f.pipe('', global_variables, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    plate.data_as_df()
    plate.create_platemaps()
    plate.tab_str = """£tab_title£, £plate£, £background_color£, £384heatmap£, £Q1£, £Q2£, £Q3£, £Q4£, £plate_info£, £roxbox£,
                     £escalations£, £rvf£, £rvnf£, £rvv£, £rvnv£, £nfvnv£, £comments£"""
    tab = plate.create_tab('000001')
    assert type(tab) == str
    assert len(tab) > 100
    assert not '£nfvnv£' in tab
    

@patch("src.functions.get_araya")
@patch("src.functions.pipe")
def test_analysis_set_thresholds(mock_pipe, mock_get_araya):
    mock_pipe.return_value = {'000001' : MockPlate()}
    mock_get_araya.return_value = 'ARAYA_02'
    cur = MagicMock()
    analysis1 = MockAnalysis('Dev 2.0', '000001', cur)
    analysis1.set_thresholds()

    assert analysis1.thresholds['POSITIVE_THRESHOLD'] == 9.5
    assert analysis1.thresholds['NEGATIVE_THRESHOLD'] == 5
    assert analysis1.thresholds['nVIC_THRESHOLD'] == 1.2
    assert analysis1.thresholds['ROX_LIMIT'] == 1000
    assert analysis1.thresholds['HIGH_ROX'] == 4000
    
    mock_get_araya.return_value = None
    analysis2 = MockAnalysis('Dev 2.0', '000002', cur)
    analysis2.set_thresholds()
    assert analysis2.thresholds['POSITIVE_THRESHOLD'] == 9
    assert analysis2.thresholds['NEGATIVE_THRESHOLD'] == 4
    assert analysis2.thresholds['nVIC_THRESHOLD'] == 1
    assert analysis2.thresholds['ROX_LIMIT'] == 1600
    assert analysis2.thresholds['HIGH_ROX'] == 5000
    
def test_analysis_summary_buffer():
    cur = MagicMock()
    analysis = bc.Analysis('Dev 2.0', None, GLOBALS, THRESHOLDS, cur, from_files = True, mirrorless = True, filepath = './/tests//')
    df = dict(plates = [],
        plate_type = [],
        read_date = [],
        test_channel = [],
        patient_samples = [],
        positives = [],
        positive_wells = [],
        plods = [],
        plod_wells = [],
        vic_fails = [],
        vic_pos_wells = [],
        rox_failures = [],
        accu_fails = [],
        negcon_fails = [],
        poscon_fails = [],
        pos_rate = [],
        pos_punch = [],
        plod_punch = [],
        vic_punch = []) # df, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic
    result = analysis._summary_buffer(df, ['A1', 'A2'], ['A15', 'A16'], ['A5', 'A6'], ['A1', 'A5', 'A03'], ['A15', 'A3'])
    expected = {'plates': [], 'plate_type': ['Possible Buffer'], 'read_date': [], 'test_channel': ['-'], 
                'patient_samples': [0], 'positives': [2], 'positive_wells': ['A1, A2'], 'plods': [], 
                'plod_wells': [], 'vic_fails': ['-'], 'vic_pos_wells': ['A15, A16'], 'rox_failures': [], 
                'accu_fails': ['-'], 'negcon_fails': ['-'], 'poscon_fails': ['-'], 'pos_rate': ['-'], 
                'pos_punch': ['A1'], 'plod_punch': ['A5'], 'vic_punch': ['A15']}
    assert result == expected
    
def test_analysis_summary_patient():
    cur = MagicMock()
    thresholds = {'POSITIVE_THRESHOLD' : 9, 'NEGATIVE_THRESHOLD' : 4, 'nVIC_THRESHOLD' : 1, 'ROX_LIMIT' : 1600, 'HIGH_ROX' : 5000}
    plate = f.pipe('', GLOBALS, thresholds, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']],
                   './/tests//', True)['000001']
    plate.pool = 'POOL00000001'
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    plate.barcodes_from_matrix(barcodes)
    plate.data_as_df()
    plate.find_instruments()
    plate._create_matrices()
    plate.plate_info()
    
    cur = MagicMock()
    analysis = bc.Analysis('Dev 2.0', None, GLOBALS, THRESHOLDS, cur, from_files = True, mirrorless = True, filepath = './/tests//')
    analysis.set_thresholds()
    df = dict(plates = [],
        plate_type = [],
        read_date = [],
        test_channel = [],
        patient_samples = [],
        positives = [],
        positive_wells = [],
        plods = [],
        plod_wells = [],
        vic_fails = [],
        vic_pos_wells = [],
        rox_failures = [],
        accu_fails = [],
        negcon_fails = [],
        poscon_fails = [],
        pos_rate = [],
        pos_punch = [],
        plod_punch = [],
        vic_punch = []) # df, plate_pos, plate_vic, plate_plods, previous_fam, previous_vic
    analysis.plates['000001'] = plate
    analysis.plates['000001'].comments = 'OLT,    Priority  HTK'
    result = analysis._summary_patient(df, analysis.plates['000001'], ['A1', 'A2'], ['A15', 'A16'], ['A5', 'A6'], ['A1', 'A5', 'A03'], ['A15', 'A3'], True)
    
    expected = {'plates': [], 'plate_type': ['Patient'], 'read_date': [], 'test_channel': ['OLT, HTK, PRIO'], 
                'patient_samples': [279], 'positives': [56], 'positive_wells': ['-'], 'plods': [], 'plod_wells': [], 
                'vic_fails': [42], 'vic_pos_wells': ['-'], 'rox_failures': [], 'accu_fails': [2], 'negcon_fails': [2], 
                'poscon_fails': [2], 'pos_rate': ['20.07%'], 'pos_punch': ['A1'], 'plod_punch': ['A5'], 'vic_punch': ['A15']}
    assert result == expected

def test_analysis_buffer_summary():
    cur = MagicMock()
    analysis = bc.Analysis('Dev 2.0', None, GLOBALS, THRESHOLDS, cur, from_files = True, mirrorless = True, filepath = './/tests//')
    barcodes = np.array([['AAA' for _ in range(24)] for _ in range(16)])
    barcodes[14:16, 18:24] = 'Con'
    for row in range(8):
        for col in range(12):
            barcodes[row * 2 + 1, col * 2 + 1] = ''
    analysis.plates['000001'].pool = 'POOL00000001'
    analysis.plates['000001'].barcodes_from_matrix(barcodes)
    analysis.plates['000001'].data_as_df()
    analysis.plates['000001'].info = {'000001': ('POOL00000001', '', 'Q1', 'Q2', 'Q3', 'Q4'), 
                'Positives': ['56 (20.07%)', '', '19 (20.43%)', '19 (20.43%)', '18 (19.35%)', 0],
                'PLODs': ['31 (11.11%, 7 high)', '', 10, 10, 11, 0], 'Negatives': [126, '', 42, 42, 42, 0], 
                'VIC Failures' : [42, '', 14, 14, 14, 0], 'Total Samples' : [279, '', 93, 93, 93, 0],
                '': ['','','','','',''], 'Instrument info': ['', '', 'INACT00000001', 'INACT00000002', 'INACT00000003', 'INACT00000004'],
                'Nexar': ['NEXAR_01', '', 'HAM_DWP_01', 'HAM_DWP_02', 'HAM_DWP_03', 'HAM_DWP_04'],
                'Araya': ['ARAYA_01', '', 'ELUTE00000001', 'ELUTE00000002', 'ELUTE00000003', 'ELUTE00000004'],
                'Hydrocycler': ['HYDROCYCL_01', '', 'KF_01', 'KF_02', 'KF_03', 'KF_04'],
                '384 Hamilton': ['HAM_384_01', '', 'DRAGONFLY_01', 'DRAGONFLY_02', 'DRAGONFLY_03', 'DRAGONFLY_04']}
    analysis.plates.pop('000002')
    summary = analysis.buffer_summary()
    expected = {'Plate': ['000001', '000003'], 'Type': ['Patient', 'Possible Buffer'], 
                'Date': ['2021/04/21 17:44', '2022/05/24 09:19'], 'Channel': ['AVA', '-'], 
                'Num Samples': [279, 0], 'Positives': [56, 0], 'Pos Wells': ['-', ''], 'PLODs': [47, 1], 
                'PLOD Wells': ['A11, A12, B11, B12, C11, C12, D11, D12, E11, E12, F9, F10, F11, F12, G9, G10, G11, G12, H9, H10, H11, H12, I9, I10, I11, I12, J9, J10, J11, K9, K10, L9, L10, M9, M10, N9, N10, O9, O10, O20, O22, O24, P9, P10, P21, P22, P24', 'C20'], 
                'VIC Fails': [42, '-'], 'VIC Positives': ['-', ''], 'Low ROX': [35, 0], 'Accuplex Fails': [2, '-'], 
                'Negcon Fails': [2, '-'], 'Qnos Fails': [2, '-'], 'Patient Positivity': ['20.07%', '-'], 'Pos Punch': ['-', ''], 
                'Pos to PLOD': ['-', ''], 'VIC Punch': ['-', '']}

    assert summary.to_dict(orient = 'list') == expected

def test_analysis_run_analysis():
    cur = MagicMock()
    analysis = bc.Analysis('Dev 2.0', None, GLOBALS, THRESHOLDS, cur, from_files = True, mirrorless = True, filepath = './/tests//')
    html = analysis.run_analysis(test = True)
    assert type(html) == str  # The individual components of the Analysis class have already been tested, therefore I will not test
    assert len(html) > 100  # that the output of this html string exactly matches what would be expected
    assert not '£plate_tab£' in html
    

#test_plate_detect_escalations_384()
