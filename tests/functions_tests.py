"python -m pytest tests/functions_tests.py"

from Pool_Helper_Config_Encryptor.poolHelperConfig import GLOBALS, THRESHOLDS
from unittest.mock import patch, MagicMock
import src.backend_classes as bc
import src.functions as f
import pandas as pd
import numpy as np
import plotly
import io
import os


CUR = MagicMock()


class SpoofBytesIO:
    def read(self):
        return 'test'
    def readlines(self):
        barray = []
        with open('.//tests//test-araya_bytes.txt', 'r', encoding = 'utf-8') as file:
            array = file.read().split('\\n')
        for x in array:
            barray.append(x.encode().replace(b'\\n', b'\n').replace(b'\\r', b'\r'))
        return barray


@patch("src.functions.lims_query")
def test_get_araya(mock_lims_query):
    mock_lims_query.return_value = [('ARAYA_01',)]
    assert f.get_araya('123456', CUR) == 'ARAYA_01'
    mock_lims_query.return_value = []
    assert f.get_araya('123456', CUR) == None


def test_encrypt_decrypt_password_to_key():
    """These three functions really need to be tested together for obvious reasons"""
    secret_string = "This is a test, the positive threshold on araya 2 is 9.5"
    password = "password"
    encrypted = f.encrypt(password, secret_string)
    decrypted = f.decrypt(password, encrypted).decode()
    assert decrypted == secret_string


def test_extract_quadrant():
    matrix = np.array([['AAA' for x in range(24)] for _ in range(16)])
    matrix[1, 1] = 'ZZZ'
    assert 'ZZZ' in f.extract_quadrant(matrix, 'Q4')
    

@patch("src.functions.lims_query")
def test_repooled_check(mock_lims_query):
    mock_lims_query.return_value = [('ELUTE00000001',), ('ELUTE00000002',)]
    assert not f.repooled_check(['ELUTE00000001', 'ELUTE00000001'], CUR, [GLOBALS['REPOOL_QUERY_1'], GLOBALS['REPOOL_QUERY_2']])
    mock_lims_query.return_value = [('ELUTE00000001',), ('ELUTE00000002',), ('ELUTE00000001',)]
    assert f.repooled_check(['ELUTE00000001', 'ELUTE00000001'], CUR, [GLOBALS['REPOOL_QUERY_1'], GLOBALS['REPOOL_QUERY_2']])

# Restamp finder will not be tested as the function itself is so simple (the sql is complex, but that cannot be tested without
# actually connecting to the LIMS mirror)


def test_scatter_plot():
    df = pd.DataFrame({'ROX' : [2000, 2000, 2000], 'nFAM' : [10, 1, 10], 'well' : ['A01', 'A02', 'A03']})
    plot = f.scatter_plot(df, 'ROX', 'nFAM', title = 'Title')
    assert type(plot) == plotly.graph_objs._figure.Figure


def test_add_plot_lines():
    df = pd.DataFrame({'ROX' : [2000, 2000, 2000], 'nFAM' : [10, 1, 10], 'well' : ['A01', 'A02', 'A03']})
    plot = f.scatter_plot(df, 'ROX', 'nFAM', title = 'Title')
    plot = f.add_plot_lines(plot, [['y', 4, 'Green'], ['y', 9, 'Red']], 3).render()
    assert type(plot) == str
    assert len(plot) > 10


def test_find_stripes():
    flag_matrix = np.array([[None for _ in range(12)] for _ in range(8)])
    flag_numbers = np.array([[0 for _ in range(12)] for _ in range(8)])
    nfam_matrix = np.array([[1 for _ in range(12)] for _ in range(8)])
    for row in range(8):
        for col in range(12):
            flag_matrix[row, col] = 'None'
    assert not 'Stripe' in f.find_stripes(nfam_matrix, flag_matrix, flag_numbers, GLOBALS, 9)[0]
    nfam_matrix[3:8, 3] = 10
    assert (f.find_stripes(nfam_matrix, flag_matrix, flag_numbers, GLOBALS, 9)[0][3:8, 3] == 'Stripe').all()
    nfam_matrix = np.array([[1 for _ in range(12)] for _ in range(8)])
    nfam_matrix[3, 3:8] = 10
    flag_matrix = np.array([[None for _ in range(12)] for _ in range(8)])
    flag_numbers = np.array([[0 for _ in range(12)] for _ in range(8)])
    for row in range(8):
        for col in range(12):
            flag_matrix[row, col] = 'None'
    assert (f.find_stripes(nfam_matrix, flag_matrix, flag_numbers, GLOBALS, 9)[0][3, 3:8] == 'Stripe').all()
    
    
def test_plot_platemap():
    _384_matrices = dict(
        nfam_matrix = np.array([['1' for _ in range(24)] for _ in range(16)]),  # Initialise all the matrices
        vic_matrix = np.array([[10 for _ in range(24)] for _ in range(16)]),
        fam_matrix = np.array([[10 for _ in range(24)] for _ in range(16)]),
        rox_matrix = np.array([[2000 for _ in range(24)] for _ in range(16)]),
        result_matrix = np.array([[0 for _ in range(24)] for _ in range(16)]),
        vic_result_matrix = np.array([[0 for _ in range(24)] for _ in range(16)]),
        nvic_matrix = np.array([['1' for _ in range(24)] for _ in range(16)]),
        flag_matrix = np.array([['None' for _ in range(24)] for _ in range(16)]),
        flag_numbers = np.array([[0 for _ in range(24)] for _ in range(16)]),
        barcode_colours = np.array([[0 for _ in range(24)] for _ in range(16)]),
        barcode_matrix = np.array([['AAA' for _ in range(24)] for _ in range(16)])
        )
    plot = f.plot_platemap(_384_matrices, 1600, 800, 'Test', GLOBALS).render()
    assert type(plot) == str
    assert len(plot) > 100
    _96_matrices = dict(
        nfam_matrix = np.array([['1' for _ in range(12)] for _ in range(8)]),  # Initialise all the matrices
        vic_matrix = np.array([[10 for _ in range(12)] for _ in range(8)]),
        fam_matrix = np.array([[10 for _ in range(12)] for _ in range(8)]),
        rox_matrix = np.array([[2000 for _ in range(12)] for _ in range(8)]),
        result_matrix = np.array([[0 for _ in range(12)] for _ in range(8)]),
        vic_result_matrix = np.array([[0 for _ in range(12)] for _ in range(8)]),
        nvic_matrix = np.array([['1' for _ in range(12)] for _ in range(8)]),
        flag_matrix = np.array([['None' for _ in range(12)] for _ in range(8)]),
        flag_numbers = np.array([[0 for _ in range(12)] for _ in range(8)]),
        barcode_colours = np.array([[0 for _ in range(12)] for _ in range(8)]),
        barcode_matrix = np.array([['AAA' for _ in range(12)] for _ in range(8)]),
        pos = 3,
        total = 93
        )
    plot = f.plot_platemap(_96_matrices, 1000, 500, 'Test', GLOBALS).render()
    assert type(plot) == str
    assert len(plot) > 100
    

def test_format_comments():
    comments = {'Q1': {'INACT00000001': ['Lysis Q1'], 'ELUTE00000001': []}, 'Q2': {'INACT00000002': ['Lysis Q2'], 'ELUTE00000002': []}, 
                'Q3': {'INACT00000003': ['Lysis Q3'], 'ELUTE00000003': []}, 'Q4': {'INACT00000004': ['Lysis Q4'], 'ELUTE00000004': []}, 
                'Pool': ['Pool Comment']}
    expected = """<br>Pool plate:<br><span style = "color:red;">Pool Comment</span><br><br>INACT00000001 (Q1):<br><span style = "color:red;">Lysis Q1</span><br><br>ELUTE00000001 (Q1):<br>None<br><br>INACT00000002 (Q2):<br><span style = "color:red;">Lysis Q2</span><br><br>ELUTE00000002 (Q2):<br>None<br><br>INACT00000003 (Q3):<br><span style = "color:red;">Lysis Q3</span><br><br>ELUTE00000003 (Q3):<br>None<br><br>INACT00000004 (Q4):<br><span style = "color:red;">Lysis Q4</span><br><br>ELUTE00000004 (Q4):<br>None<br><br>"""
    assert f.format_comments(comments) == expected


def test_format_escalations():
    escalations = ['Level 2 - 3 or more ROX fails', 'Level consult service guidance - 6 or more PLODs',
                   'Level 2 - Negcon fail on Q1 has invalidated samples', 'Level 3 - 10 or more RNaseP failures',
                   'Level 2 - Both positive controls on Q2 have failed', 
                   'Level 2 - The qnostic has failed on Q3, and the accuplex in the same quadrant contains RNaseP',
                   'Level consult service guidance - 6 or more PLODs']
    expected = """<span style = "color:red;">Level 2 - 3 or more ROX fails</span><br><span style = "color:red;">Level consult service guidance - 6 or more PLODs</span><br><span style = "color:red;">Level 2 - Negcon fail on Q1 has invalidated samples</span><br><span style = "color:red;">Level 3 - 10 or more RNaseP failures</span><br><span style = "color:red;">Level 2 - Both positive controls on Q2 have failed</span><br><span style = "color:red;">Level 2 - The qnostic has failed on Q3, and the accuplex in the same quadrant contains RNaseP</span><br><span style = "color:red;">Level consult service guidance - 6 or more PLODs</span><br><br>NOTE: This is not an exhaustive list and service-guidance escalations are not included in this list. You must contine to follow the SOP and service guidance"""
    assert f.format_escalations(escalations) == expected
    escalations = []
    expected = """None<br><br>NOTE: This is not an exhaustive list and service-guidance escalations are not included in this list. You must contine to follow the SOP and service guidance"""
    assert f.format_escalations(escalations) == expected
    

def test_detect_carryover():
    pos = ['A1', 'A2']
    vic = ['A15', 'A16']
    plods = ['A5', 'A6']
    previous_fam = ['A1', 'A5', 'A03']
    previous_vic = ['A15', 'A3']
    assert f.detect_carryover(pos, vic, plods, previous_fam, previous_vic) == ('A1', 'A15', 'A5')
    

@patch('io.BytesIO')
def test_plate_read(MockBytesIO):
    cur = None
    plate = f._plate_read('test-araya_000001.csv', '000001', None, GLOBALS, THRESHOLDS, cur, filepath = './/tests//')
    plate.barcodes_from_matrix(np.array([['AAA' for _ in range(24)] for _ in range(16)]))
    plate.data_as_df()
    expected = pd.read_csv('.//tests//expected df1.csv')
    expected['well'] = pd.Series([x[0] + x[2] if int(x[1:]) < 10 else x for x in expected['well']])
    assert expected.to_dict() == plate.df.to_dict()
    MockBytesIO.return_value = SpoofBytesIO()
    plate = f._plate_read(SpoofBytesIO(), '000001', None, GLOBALS, THRESHOLDS, cur, filepath = './/tests//')
    plate.barcodes_from_matrix(np.array([['AAA' for _ in range(24)] for _ in range(16)]))
    plate.data_as_df()
    expected = pd.read_csv('.//tests//expected df2.csv')
    expected['well'] = pd.Series([x[0] + x[2] if int(x[1:]) < 10 else x for x in expected['well']])
    assert expected.round(2).to_dict() == plate.df.round(2).to_dict()
    os.remove('.//tests//20220601041151_00890018002017-00620210125-566493.csv')
    

@patch("src.functions.lims_query")
def test_get_files(mock_lims_query):
    mock_lims_query.return_value = [('000001.csv', 'File 01',), ('000002.csv', 'File 02',), ('000008.csv', 'File 08',),
                                    ('000009.csv', 'File 09',), ('000010.csv', 'File 10',), ('000011.csv', 'File 11',)]
    expected = [('000008.csv', 'File 08'), ('000009.csv', 'File 09'), ('000010.csv', 'File 10'), ('000011.csv', 'File 11')]
    assert f._get_files('000009', CUR, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']]) == expected
    
    
@patch("src.functions.lims_query")
def test_get_pool(mock_lims_query):
    mock_lims_query.return_value = [('POOL00000001',)]
    assert f._get_pool('000001', CUR) == 'POOL00000001'
    mock_lims_query.return_value = []
    assert f._get_pool('000001', CUR) == None
    

@patch("src.functions._get_pool")
@patch('io.BytesIO')
@patch("src.functions._get_files")
def test_pipe(mock_get_files, MockBytesIO, mock_get_pool):
    cur = None
    MockBytesIO.return_value = SpoofBytesIO()
    mock_get_files.return_value = [('000008.csv', SpoofBytesIO(),), ('000009.csv', SpoofBytesIO(),), 
                                   ('000010.csv', SpoofBytesIO(),), ('000011.csv', SpoofBytesIO(),)]
    mock_get_pool.return_value = 'POOL00000001'
    plates = f.pipe('000009', GLOBALS, THRESHOLDS, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']])
    assert plates.keys() == {'000008' : None, '000009' : None, '000010' : None, '000011' : None}.keys()
    assert plates['000008']['A1'].all_data() == {'FAM': 4022, 'VIC': 9617, 'ROX': 4125, 'nFAM': 0.975030303030303, 
                                                'nVIC': 2.3313939393939394, 'barcode': ''}
    plates = f.pipe(None, GLOBALS, THRESHOLDS, cur, [GLOBALS['GET_FILES_QUERY_1'], GLOBALS['GET_FILES_QUERY_2'], GLOBALS['POOL_QUERY']], 
                    filepath = './/tests//', from_files = True)
    print(plates.keys())
    assert plates.keys() == {'000001' : None, '000002' : None, '000003' : None}.keys()
    assert plates['000001']['A1'].all_data() == {'FAM': 60000, 'VIC': 120, 'ROX': 4000, 'nFAM': 15, 
                                                'nVIC': 0.03, 'barcode': ''}


#test_plate_read()
