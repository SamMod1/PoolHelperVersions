import sys
import plotly
import base64
import random
import numpy as np
import pandas as pd
from jinja2 import Template
import plotly.graph_objects as go
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
X_AXIS = [x + 1 for x in range(24)]
_384_WELL_POSITIONS = string = [["Q1 A1","Q2 A1","Q1 A2","Q2 A2","Q1 A3","Q2 A3","Q1 A4","Q2 A4","Q1 A5","Q2 A5","Q1 A6","Q2 A6","Q1 A7","Q2 A7","Q1 A8","Q2 A8","Q1 A9","Q2 A9","Q1 A10","Q2 A10","Q1 A11","Q2 A11","Q1 A12","Q2 A12"],["Q3 A1","Q4 A1","Q3 A2","Q4 A2","Q3 A3","Q4 A3","Q3 A4","Q4 A4","Q3 A5","Q4 A5","Q3 A6","Q4 A6","Q3 A7","Q4 A7","Q3 A8","Q4 A8","Q3 A9","Q4 A9","Q3 A10","Q4 A10","Q3 A11","Q4 A11","Q3 A12","Q4 A12"],["Q1 B1","Q2 B1","Q1 B2","Q2 B2","Q1 B3","Q2 B3","Q1 B4","Q2 B4","Q1 B5","Q2 B5","Q1 B6","Q2 B6","Q1 B7","Q2 B7","Q1 B8","Q2 B8","Q1 B9","Q2 B9","Q1 B10","Q2 B10","Q1 B11","Q2 B11","Q1 B12","Q2 B12"],["Q3 B1","Q4 B1","Q3 B2","Q4 B2","Q3 B3","Q4 B3","Q3 B4","Q4 B4","Q3 B5","Q4 B5","Q3 B6","Q4 B6","Q3 B7","Q4 B7","Q3 B8","Q4 B8","Q3 B9","Q4 B9","Q3 B10","Q4 B10","Q3 B11","Q4 B11","Q3 B12","Q4 B12"],["Q1 C1","Q2 C1","Q1 C2","Q2 C2","Q1 C3","Q2 C3","Q1 C4","Q2 C4","Q1 C5","Q2 C5","Q1 C6","Q2 C6","Q1 C7","Q2 C7","Q1 C8","Q2 C8","Q1 C9","Q2 C9","Q1 C10","Q2 C10","Q1 C11","Q2 C11","Q1 C12","Q2 C12"],["Q3 C1","Q4 C1","Q3 C2","Q4 C2","Q3 C3","Q4 C3","Q3 C4","Q4 C4","Q3 C5","Q4 C5","Q3 C6","Q4 C6","Q3 C7","Q4 C7","Q3 C8","Q4 C8","Q3 C9","Q4 C9","Q3 C10","Q4 C10","Q3 C11","Q4 C11","Q3 C12","Q4 C12"],["Q1 D1","Q2 D1","Q1 D2","Q2 D2","Q1 D3","Q2 D3","Q1 D4","Q2 D4","Q1 D5","Q2 D5","Q1 D6","Q2 D6","Q1 D7","Q2 D7","Q1 D8","Q2 D8","Q1 D9","Q2 D9","Q1 D10","Q2 D10","Q1 D11","Q2 D11","Q1 D12","Q2 D12"],["Q3 D1","Q4 D1","Q3 D2","Q4 D2","Q3 D3","Q4 D3","Q3 D4","Q4 D4","Q3 D5","Q4 D5","Q3 D6","Q4 D6","Q3 D7","Q4 D7","Q3 D8","Q4 D8","Q3 D9","Q4 D9","Q3 D10","Q4 D10","Q3 D11","Q4 D11","Q3 D12","Q4 D12"],["Q1 E1","Q2 E1","Q1 E2","Q2 E2","Q1 E3","Q2 E3","Q1 E4","Q2 E4","Q1 E5","Q2 E5","Q1 E6","Q2 E6","Q1 E7","Q2 E7","Q1 E8","Q2 E8","Q1 E9","Q2 E9","Q1 E10","Q2 E10","Q1 E11","Q2 E11","Q1 E12","Q2 E12"],["Q3 E1","Q4 E1","Q3 E2","Q4 E2","Q3 E3","Q4 E3","Q3 E4","Q4 E4","Q3 E5","Q4 E5","Q3 E6","Q4 E6","Q3 E7","Q4 E7","Q3 E8","Q4 E8","Q3 E9","Q4 E9","Q3 E10","Q4 E10","Q3 E11","Q4 E11","Q3 E12","Q4 E12"],["Q1 F1","Q2 F1","Q1 F2","Q2 F2","Q1 F3","Q2 F3","Q1 F4","Q2 F4","Q1 F5","Q2 F5","Q1 F6","Q2 F6","Q1 F7","Q2 F7","Q1 F8","Q2 F8","Q1 F9","Q2 F9","Q1 F10","Q2 F10","Q1 F11","Q2 F11","Q1 F12","Q2 F12"],["Q3 F1","Q4 F1","Q3 F2","Q4 F2","Q3 F3","Q4 F3","Q3 F4","Q4 F4","Q3 F5","Q4 F5","Q3 F6","Q4 F6","Q3 F7","Q4 F7","Q3 F8","Q4 F8","Q3 F9","Q4 F9","Q3 F10","Q4 F10","Q3 F11","Q4 F11","Q3 F12","Q4 F12"],["Q1 G1","Q2 G1","Q1 G2","Q2 G2","Q1 G3","Q2 G3","Q1 G4","Q2 G4","Q1 G5","Q2 G5","Q1 G6","Q2 G6","Q1 G7","Q2 G7","Q1 G8","Q2 G8","Q1 G9","Q2 G9","Q1 G10","Q2 G10","Q1 G11","Q2 G11","Q1 G12","Q2 G12"],["Q3 G1","Q4 G1","Q3 G2","Q4 G2","Q3 G3","Q4 G3","Q3 G4","Q4 G4","Q3 G5","Q4 G5","Q3 G6","Q4 G6","Q3 G7","Q4 G7","Q3 G8","Q4 G8","Q3 G9","Q4 G9","Q3 G10","Q4 G10","Q3 G11","Q4 G11","Q3 G12","Q4 G12"],["Q1 H1","Q2 H1","Q1 H2","Q2 H2","Q1 H3","Q2 H3","Q1 H4","Q2 H4","Q1 H5","Q2 H5","Q1 H6","Q2 H6","Q1 H7","Q2 H7","Q1 H8","Q2 H8","Q1 H9","Q2 H9","Q1 H10","Q2 H10","Q1 H11","Q2 H11","Q1 H12","Q2 H12"],["Q3 H1","Q4 H1","Q3 H2","Q4 H2","Q3 H3","Q4 H3","Q3 H4","Q4 H4","Q3 H5","Q4 H5","Q3 H6","Q4 H6","Q3 H7","Q4 H7","Q3 H8","Q4 H8","Q3 H9","Q4 H9","Q3 H10","Q4 H10","Q3 H11","Q4 H11","Q3 H12","Q4 H12"]]
_96_WELL_POSITIONS = string = {'Q1': np.array([['384 A1', '384 A3', '384 A5', '384 A7', '384 A9', '384 A11', '384 A13', '384 A15', '384 A17', '384 A19', '384 A21', '384 A23'], ['384 C1', '384 C3', '384 C5', '384 C7', '384 C9', '384 C11', '384 C13', '384 C15', '384 C17', '384 C19', '384 C21', '384 C23'], ['384 E1', '384 E3', '384 E5', '384 E7', '384 E9', '384 E11', '384 E13', '384 E15', '384 E17', '384 E19', '384 E21', '384 E23'], ['384 G1', '384 G3', '384 G5', '384 G7', '384 G9', '384 G11', '384 G13', '384 G15', '384 G17', '384 G19', '384 G21', '384 G23'], ['384 I1', '384 I3', '384 I5', '384 I7', '384 I9', '384 I11', '384 I13', '384 I15', '384 I17', '384 I19', '384 I21', '384 I23'], ['384 K1', '384 K3', '384 K5', '384 K7', '384 K9', '384 K11', '384 K13', '384 K15', '384 K17', '384 K19', '384 K21', '384 K23'], ['384 M1', '384 M3', '384 M5', '384 M7', '384 M9', '384 M11', '384 M13', '384 M15', '384 M17', '384 M19', '384 M21', '384 M23'], ['384 O1', '384 O3', '384 O5', '384 O7', '384 O9', '384 O11', '384 O13', '384 O15', '384 O17', '384 O19', '384 O21', '384 O23']], dtype=object),
          'Q2': np.array([['384 A2', '384 A4', '384 A6', '384 A8', '384 A10', '384 A12', '384 A14', '384 A16', '384 A18', '384 A20', '384 A22', '384 A24'], ['384 C2', '384 C4', '384 C6', '384 C8', '384 C10', '384 C12', '384 C14', '384 C16', '384 C18', '384 C20', '384 C22', '384 C24'], ['384 E2', '384 E4', '384 E6', '384 E8', '384 E10', '384 E12', '384 E14', '384 E16', '384 E18', '384 E20', '384 E22', '384 E24'], ['384 G2', '384 G4', '384 G6', '384 G8', '384 G10', '384 G12', '384 G14', '384 G16', '384 G18', '384 G20', '384 G22', '384 G24'], ['384 I2', '384 I4', '384 I6', '384 I8', '384 I10', '384 I12', '384 I14', '384 I16', '384 I18', '384 I20', '384 I22', '384 I24'], ['384 K2', '384 K4', '384 K6', '384 K8', '384 K10', '384 K12', '384 K14', '384 K16', '384 K18', '384 K20', '384 K22', '384 K24'], ['384 M2', '384 M4', '384 M6', '384 M8', '384 M10', '384 M12', '384 M14', '384 M16', '384 M18', '384 M20', '384 M22', '384 M24'], ['384 O2', '384 O4', '384 O6', '384 O8', '384 O10', '384 O12', '384 O14', '384 O16', '384 O18', '384 O20', '384 O22', '384 O24']], dtype=object),
          'Q3': np.array([['384 B1', '384 B3', '384 B5', '384 B7', '384 B9', '384 B11', '384 B13', '384 B15', '384 B17', '384 B19', '384 B21', '384 B23'], ['384 D1', '384 D3', '384 D5', '384 D7', '384 D9', '384 D11', '384 D13', '384 D15', '384 D17', '384 D19', '384 D21', '384 D23'], ['384 F1', '384 F3', '384 F5', '384 F7', '384 F9', '384 F11', '384 F13', '384 F15', '384 F17', '384 F19', '384 F21', '384 F23'], ['384 H1', '384 H3', '384 H5', '384 H7', '384 H9', '384 H11', '384 H13', '384 H15', '384 H17', '384 H19', '384 H21', '384 H23'], ['384 J1', '384 J3', '384 J5', '384 J7', '384 J9', '384 J11', '384 J13', '384 J15', '384 J17', '384 J19', '384 J21', '384 J23'], ['384 L1', '384 L3', '384 L5', '384 L7', '384 L9', '384 L11', '384 L13', '384 L15', '384 L17', '384 L19', '384 L21', '384 L23'], ['384 N1', '384 N3', '384 N5', '384 N7', '384 N9', '384 N11', '384 N13', '384 N15', '384 N17', '384 N19', '384 N21', '384 N23'], ['384 P1', '384 P3', '384 P5', '384 P7', '384 P9', '384 P11', '384 P13', '384 P15', '384 P17', '384 P19', '384 P21', '384 P23']], dtype=object),
          'Q4': np.array([['384 B2', '384 B4', '384 B6', '384 B8', '384 B10', '384 B12', '384 B14', '384 B16', '384 B18', '384 B20', '384 B22', '384 B24'], ['384 D2', '384 D4', '384 D6', '384 D8', '384 D10', '384 D12', '384 D14', '384 D16', '384 D18', '384 D20', '384 D22', '384 D24'], ['384 F2', '384 F4', '384 F6', '384 F8', '384 F10', '384 F12', '384 F14', '384 F16', '384 F18', '384 F20', '384 F22', '384 F24'], ['384 H2', '384 H4', '384 H6', '384 H8', '384 H10', '384 H12', '384 H14', '384 H16', '384 H18', '384 H20', '384 H22', '384 H24'], ['384 J2', '384 J4', '384 J6', '384 J8', '384 J10', '384 J12', '384 J14', '384 J16', '384 J18', '384 J20', '384 J22', '384 J24'], ['384 L2', '384 L4', '384 L6', '384 L8', '384 L10', '384 L12', '384 L14', '384 L16', '384 L18', '384 L20', '384 L22', '384 L24'], ['384 N2', '384 N4', '384 N6', '384 N8', '384 N10', '384 N12', '384 N14', '384 N16', '384 N18', '384 N20', '384 N22', '384 N24'], ['384 P2', '384 P4', '384 P6', '384 P8', '384 P10', '384 P12', '384 P14', '384 P16', '384 P18', '384 P20', '384 P22', '384 P24']], dtype=object)}
random.seed(1)


def lims_query(query : str, cur) -> list:
    """Executes and returns the query"""
    cur.execute(query)
    return cur.fetchall()


def pd_lims_query(query,connection):
    resultDF=pd.read_sql(query, con=connection)
    return(resultDF)


def get_araya(plate : str, cur):
    """
    Returns the name of the araya the plate was run on. If the plate cannot be found in LIMS, it returns None.
    
    Parameters:
        plate: A string of the tape ID (array code).
        cur: A cx_Oracle cursor which connects to the LIMS mirror database.
    
    Returns:
        str
    """
    query = f"""select VALUE from JOB_PARAMETER where JOB = (
    select JOB_NAME from JOB_HEADER where ARRAY_CODE = '{plate}' fetch first 1 rows only
    ) and VALUE like 'ARAYA%' fetch first 1 rows only"""  
    araya = lims_query(query, cur)
    if len(araya) == 0:
        return None
    else:
        return araya[0][0]
    

def give_warning(warning : str, quit_ = True, serious_error = False):
    """
    Gives a specified warning and asks whether the user wants to continue or not
    
    Parameters:
        warning: a string which will be displayed to the user.
        quit_: if this is False, the function will return False if the user selects 'N', if True the program will quit.
        serious_error: If True, the function will not give the user the option to continue.
    
    returns:
        True/False (if quit_ is False, else it returns nothing)
    """
    if serious_error:
        print('\n' + warning)
        input('Press enter to close the program')
        sys.exit()
    response = input(warning + ' (Y/N) ')
    if response.upper() != 'Y':
        if quit_:
            sys.exit()
        else:
            return False
    elif not quit_:
        return True

    
def encrypt(password : str, message : str) -> str:
    """
    Takes a password and use it to encrypt a string using AES in CBC mode with a 128-bit key for encryption.
    
    Parameters
    ----------
        password : str
            The password with which to encrypt the message
        message : str
            A message to encrypt
    Returns
    -------
        Bytes like encrypted text
    """
    try:
        encoded_message = message.encode()
        key = password_to_key(password)
        f1 = Fernet(key)
        encrypted = f1.encrypt(encoded_message)
        return encrypted
    except InvalidToken:
        return None


def decrypt(password : str, message : bytes) -> str:
    """
    Takes a password and use it to decrypt a string using AES in CBC mode with a 128-bit key for encryption.
    
    Parameters
    ----------
        password : str
            The password with which the message will be decrypted
        message : bytes
            A message to decrypt
    Returns
    -------
        Bytes like decrypted text
    """
    try:
        key = password_to_key(password)
        f2 = Fernet(key)
        decrypted = f2.decrypt(message)
        return decrypted
    except InvalidToken:
        return None


def password_to_key(password : str):
    """Takes a password and returns a key for authentication. This uses HMAC using SHA256 for authentication"""
    password = password.encode()
    salt = b'5\xbd:\x05(\xc3\xce\x18Q9.\xbd\xd8\xda\x80\xbd'
    kdf = PBKDF2HMAC(
        algorithm = hashes.SHA256(),
        length = 32,
        salt = salt,
        iterations = 1000000,
        backend = default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def extract_quadrant(matrix, quadrant : str):
    """Extracts the given quadrant from a two dimensional numpy array representing a 384-well plate"""
    quad_offsets = {'Q1' : [0, 0], 'Q2' : [0, 1], 'Q3' : [1, 0], 'Q4' : [1, 1]}
    new_matrix = np.array([[None for _ in range(12)] for _ in range(8)])
    for row in range(8):
        for col in range(12):
            for quadrant in ('Q1', 'Q2', 'Q3', 'Q4'):
                new_matrix[row, col] = matrix[row * 2 + quad_offsets[quadrant][0], col * 2 + quad_offsets[quadrant][1]]
    return new_matrix


def repooled_check(ELUTE_list, cur):
    """
    Function by @Graham Hill. Takes a list of the elution plates on a pool plate and returns True or False based on whether 
    it has been repooled or not
    
    Parameters
    ----------
        ELUTE_list : iterable
            A list of the elution plates used to make up the 384 plate
        cur : cx_Oracle cursor object
            A cursor object from a connection to the LIMS mirror datbase
            
    Returns
    -------
        Whether or not the plate has been repooled
    """
    if cur == None:
        return False
    if len(ELUTE_list) == 1:
        query = """select ELUTION_PLATE from VGSM.COMPRESSION_JOIN where ELUTION_PLATE = '"""+str(ELUTE_list[0])+"""'"""
        print(query)
    #Selects from Comression Join
    else:
        query = """select ELUTION_PLATE from VGSM.COMPRESSION_JOIN where ELUTION_PLATE in """+str(tuple(ELUTE_list))
    #The username and password parts here aren't being passed to this function, so beware!
    response = lims_query(query,cur)
    #Finds duplicates. Could offload into the SQL, but max df size ought to be 64 lines
    return not len(set(response)) == len(response)


def restamp_finder(from_date, to_date, cur):
    """Returns a list of plates which were re-stamped between (or equal to) the dates given"""
    if cur == None:
        return []
    query = f"""
select distinct j.job_name
from vgsm.sweeper_log s, vgsm.blob_values b, vgsm.job_header j
where b.blob_id=s.archived_file_blob and s.original_filename like '%PipetteLog%' and s.log_time >= to_date('{str(from_date)[0:10]}','yyyy-mm-dd') and s.log_time <= to_date('{str(to_date)[0:10]}','yyyy-mm-dd')
and j.job_name=substr(UTL_RAW.CAST_TO_VARCHAR2(DBMS_LOB.SUBSTR(b.blob_field, 600,1)),
instr(UTL_RAW.CAST_TO_VARCHAR2(DBMS_LOB.SUBSTR(b.blob_field, 600,1)),'<PLATECODE>')+11,12)
and j.job_name in
( select j1.job_name from vgsm.job_header j1, vgsm.sweeper_log s1, vgsm.blob_values b1 where b1.blob_id=s1.archived_file_blob and s1.original_filename like '%PipetteLog%' and j1.job_name=substr(UTL_RAW.CAST_TO_VARCHAR2(DBMS_LOB.SUBSTR(b1.blob_field, 600,1)),
instr(UTL_RAW.CAST_TO_VARCHAR2(DBMS_LOB.SUBSTR(b1.blob_field, 600,1)),'<PLATECODE>')+11,12)
group by j1.job_name having count(*)>1 )
/* and s.original_filename not in ( select s2.original_filename from vgsm.sweeper_log s2 where s2.original_filename like '%PipetteLog%' group by (s2.original_filename ) having count(*)>1 ) */
    """
    #query = """select JOB_NAME where """
    output = lims_query(query, cur)
    return output


def scatter_plot(
        plate_df, 
        x : str,
        y : str,
        background_color = "rgb(235,235,235)",
        bg_color = 'lightblue',
        width = 800,
        height = 500,
        title = None
        ):
    """
    Returns an HTML string encoding a plotly scatter plot of x vs y.
    
    Parameters
    ----------
        plate_df: The dataframe from which the data is to be plotted.
        x: The name of the column containing the x data.
        y: The name of the column containing the y data.
        background_color: A string in a format compatable with plotly defining a colour of the background on which the plot is plotted on.
        bg_color: A string in a format compatable with plotly defining a colour of the background for the plot itself.
        width: The width of the plot.
        height: The hight of the plot.
        title: Title of the graph.
    
    Returns
    -------
        A plotly scatter plot of the relevant data
    """
    plot = go.Figure().add_trace(go.Scatter(x = plate_df[x], y = plate_df[y], hovertext = plate_df['well'], mode = 'markers'))
    plot.update_layout(width = width, height = height)
    plot.update_xaxes(title_text = x)
    plot.update_yaxes(title_text = y)
    plot.update_layout(paper_bgcolor = background_color, plot_bgcolor = bg_color, title = title)
    plot.update_yaxes(rangemode="tozero"); plot.update_xaxes(rangemode="tozero")
    return plot


def add_plot_lines(plot, lines : list, line_width : int):
    """
    Adds dotted lines to a plotly scatter plot in the positions specified in the list lines.
    
    Parameters
    ----------
        plot: The plot to add lines to
        lines: a list containing a list or lists which themselves contain the following data for each line to be added to the plot:
            [axis, position of line on axis, colour of line]
    
    Returns
    -------
        A string of the html code needed to create the graph (without plotlyjs included)
    """
    shapes = []
    for line in lines:
        axis = line[0]
        if axis == 'y':
            other_axis = 'x'
        else:
            other_axis = 'y'
        shapes.append({'type' : 'line', axis+'ref' : axis, axis+'0' : line[1], axis+'1' : line[1], other_axis+'ref' : 'paper',
                                      other_axis+'0' : 0, other_axis+'1' : 1, 'line' : {'color' : line[2], 'width' : line_width, 'dash' : 'dot'}})
    plot.update_layout(shapes = shapes)

    return Template(plotly.offline.plot(plot, include_plotlyjs = False, output_type = 'div'))


def striping_pass_one(plate_matrix):
    plate_dimensions = plate_matrix.shape
    blank_matrix = np.array([[[0,0] for _ in range(plate_dimensions[1])] for _ in range(plate_dimensions[0])])
    adjacent_positives = []
    hor_group = 0
    hor_groups = []
    ver_group = 0
    ver_groups = []
    for row in range(plate_dimensions[0]):
        for col in range(plate_dimensions[1]):
            if plate_matrix[(row, col)] == 1:
                if not col == plate_dimensions[1] - 1:
                    if plate_matrix[(row, col + 1)] == 1 and blank_matrix[(row, col + 1)][0] == 0:
                        blank_matrix[(row, col)][0] = 1
                        hor_groups.append([(row, col)])
                        adjacent_positives = [(row, col)]
                        while len(adjacent_positives) > 0:
                            current_well = adjacent_positives[0]
                            adjacent_positives.pop(0)
                            if current_well[1] + 1 > plate_dimensions[1] - 1:  # I.e if we hit the end of a row
                                break
                            right_well = (current_well[0], current_well[1] + 1)
                            if plate_matrix[right_well] == 1 and blank_matrix[right_well][0] == 0:
                                blank_matrix[right_well][0] = 1
                                adjacent_positives.append(right_well)
                                hor_groups[hor_group].append(right_well)
                        hor_group += 1
                if not row == plate_dimensions[0] - 1:
                    if plate_matrix[(row + 1, col)] == 1 and blank_matrix[(row + 1, col)][1] == 0:
                        blank_matrix[(row, col)][1] = 1
                        ver_groups.append([(row, col)])
                        adjacent_positives = [(row, col)]
                        while len(adjacent_positives) > 0:
                            current_well = adjacent_positives[0]
                            adjacent_positives.pop(0)
                            if current_well[0] + 1 > plate_dimensions[0] - 1:
                                break
                            well_below = (current_well[0] + 1, current_well[1])
                            if plate_matrix[well_below] == 1 and blank_matrix[well_below][1] == 0:
                                blank_matrix[well_below][1] = 1
                                adjacent_positives.append(well_below)
                                ver_groups[ver_group].append(well_below)
                        ver_group += 1
    return (hor_groups, ver_groups)


def analyse_stripe(stripe, plate_matrix, barcode_matrix, simulations = 50000):
    """
    Determines the size of every vertical and horiztonal stripe of positives on a microplate

    Parameters:
    plate_matrix : Matrix
        A 2D matrix representing a microplate assay, zeros represent negative samples, ones represent positive values.
        Controls can be represented by any other value
    
    Returns:
    A tuple containing two lists of numbers. The numbers in the first list represent the sizes of each horizontal stripe,
    the second list contains the sizes of each vertical stripe of positves.
    """
    barcodes = []
    barcode_prev = {}
    for well in stripe:
        barcodes.append(barcode_matrix[well])
    for barcode in barcodes:
        barcode_results = plate_matrix[barcode_matrix == barcode]
        #print(barcode_results)
        barcode_prev[barcode] = (barcode_results == 1).sum() / len(barcode_results)
    results = np.array([], dtype = bool)
    #print(barcode_prev['AVA'])
    for _ in range(simulations):
        success = True
        for barcode in barcodes:
            num = random.random()
            #print(barcode)
            #print(num)
            #print(barcode_prev[barcode])
            if num > barcode_prev[barcode]:
                success = False
                break
        results = np.append(results, success)
    #print(alpha)
    p = results.sum() / len(results)
    return p


def plot_platemap(matrices : dict, width : int, height : int, title : str, glob : dict, quadrant = None):
    """
    Creates the interactive plotly heatmaps for the 384-well platemap and the quadrant platemaps
    
    Parameters
    ----------
        matrices : dict
            A dict with the following keys:
                nfam_matrix: Matrix containing the nFAM values as strings rounded to two decimals
                nvic_matrix: Contains the nVIC values as strings rounded to two decimals
                fam_matrix: Contains the FAM values
                vic_matrix: Contains the VIC values
                rox_matrix: Contains the ROX values
                result_matrix: A matrix representing the platemap of results based on the nFAM value. 0 = Negative, 1 = PLOD, 2 = Positive
                vic_result_matrix: The RNaseP result. 0 = Negative, 1 = Positive
                flag_matrix: A matrix of warnings for wells. Warnings include: PLOD, HI PLOD, VIC FAIL, Pos fail, Neg fail, etc...
                flag_numbers: A matrix of numbers which tells plotly what colour each warning in the notifications tab should be displayed as
                barcode_matrix: A platemap of the barcode preffixes of each sample on the plate
                barcode_colours: A matrix where each unique barcode preffix is assigned a number (used to determine the colours of barcodes)
        width : int
            The width the plot should be (1600 for the 384 platemap, 800 for the quadrant maps)
        height : int
            The hight the plot should be (1000 for the 384 platemap, 500 for the quadrant maps)
        title : str
            The title of the plot
        glob : dict
            Contains the global variables for Pool Helper which are stored encrypted on the shared drive
        plotly_js : bool
            Whether or not to include plotlyjs in the output html template (pool helper 2.0 now inserts a partial plotly bundle
            elsewhere in the code, so this should now always be False)
            
    Returns
    -------
        A jinja2 Template object of the plotly platemap
    """
    result_colours = glob['RESULT_COLOURS']
    plotly_js = False
    pos = ''
    vic_title = ''
    if not quadrant == None:
        labels = _96_WELL_POSITIONS[quadrant]
        if matrices['pos'] > 0:
            pos = f"({matrices['pos']} positives, {round((matrices['pos'] / matrices['total']) * 100, 1)}%)"
        else:
            pos = "(0 positives)"
    else:
        plotly_js = True
        labels = _384_WELL_POSITIONS
        pos = '<span style = "color:rgb(227,5,19);"> Positive</span>, <span style = "color:rgb(255,183,71);">PLOD</span>, <span style = "color:rgb(0,180,0);">Negative</span>'
        vic_title = '<span style = "color:rgb(0,0,188);font-size: 30px;"> Positive, </span><span style = "color:rgb(240,0,240);font-size: 30px;">Negative</span>'
    heatmap = go.Figure()
    heatmap.add_trace(go.Heatmap(x = X_AXIS[0:len(matrices['nfam_matrix'].tolist()[0])], y = LETTERS[0:len(matrices['nfam_matrix'])],
                                 z = matrices['result_matrix'], showscale = False, xgap = 2, ygap = 2, 
                                 colorscale = [[0.0, result_colours[0]], [0.5, result_colours[1]], [1.0, result_colours[2]]], 
                                 text = matrices['nfam_matrix'], texttemplate = "%{text}", zmin = 0, zmax = 2, customdata = labels,
                                 hovertemplate = '%{y}%{x}<br>(%{customdata})<extra></extra>'))
    heatmap['layout']['yaxis']['autorange'] = "reversed"
    heatmap.update_layout(
        paper_bgcolor = glob['BACKGROUND_COLOUR'], 
        title = f'<span style="font-size: 30px;"> {title} (nFAM) {pos}</span>',
        autosize = False,
        width = width,
        height = height,
        xaxis = dict(
            tickmode = 'linear',
            side = 'top',
            tick0 = 1,
            dtick = 1,
            tickfont = dict(size = 25),
            fixedrange = True
        ),
        yaxis = dict(
            tickfont = dict(size = 25),
            fixedrange = True
        ))
    heatmap.update_layout(  # Add dropdown menus:
        updatemenus=[
            dict(
                type="buttons",
                direction="down",
                x=-0.05,
                y=1,
                showactive=True,
                buttons=list(
                    [
                        dict(
                            label="nFAM",
                            method="update",
                            args=[{"z": [matrices['result_matrix']], 
                                   'texttemplate' : "%{text}", 
                                   'colorscale' : f'[[0.0, "{result_colours[0]}"], [0.5, "{result_colours[1]}"], [1.0, "{result_colours[2]}"]]', 
                                   'text': [matrices['nfam_matrix']], 
                                   'zauto' : False,
                                   'zmin' : '0', 
                                   'zmax' : '2'}, 
                                  {'title.text' : f'<span style="font-size: 30px;"> {title} (nFAM) {pos}</span>'}],
                        ),
                        dict(  # Force colorscale here?
                            label="Notifications",
                            method="update",
                            args=[{"z": [matrices['flag_numbers']], 
                                   'texttemplate' : "%{text}", 
                                   'colorscale' : 'Rainbow', 
                                   'text' : [matrices['flag_matrix']], 
                                   'zauto' : False, 
                                   'zmin' : '0', 
                                   'zmax' : '8'}, 
                                  {'title.text' : f'<span style="font-size: 30px;"> {title} (Notifications) </span>',}], # Could be Bluered, hot
                        ),
                        dict(
                             label = "Barcodes",
                             method = "update",
                             args=[{"z": [matrices['barcode_colours']], 
                                    'texttemplate' : "%{text}", 
                                    'colorscale' : 'Rainbow', 
                                    'text' : [matrices['barcode_matrix']], 
                                    'zauto' : True}, 
                                   {'title.text' : f'<span style="font-size: 30px;"> {title} (Barcode prefixes) </span>'}],
                        ),
                        dict(
                            label="nVIC",
                            method="update",
                            args=[{"z": [matrices['vic_result_matrix']], 
                                   'texttemplate' : "%{text}", 
                                   'colorscale' : '[[0.0, "rgb(240, 0, 240)"], [1.0, "rgb(0, 0, 188)"]]', 
                                   'text': [matrices['nvic_matrix']], 
                                   'zauto' : False,
                                   'zmin' : '0', 
                                   'zmax' : '1'}, 
                                  {'title.text' : f'<span style="font-size: 30px;"> {title} (nVIC) </span>' + vic_title}], # Could be Bluered, hot, YlOrRd
                        ),
                        dict(
                            label="FAM",
                            method="update",
                            args=[{"z": [matrices['fam_matrix']], 
                                   'texttemplate' : "%{text}", 
                                   'colorscale' : 'Portland', 
                                   'text' : [matrices['fam_matrix']], 
                                   'zauto' : True}, 
                                  {'title.text' : f'<span style="font-size: 30px;"> {title} (FAM RFU) </span>'}], # Could be Bluered, hot
                        ),
                        dict(
                            label="VIC",
                            method="update",
                            args=[{"z": [matrices['vic_matrix']], 
                                   'texttemplate' : "%{text}", 
                                   'colorscale' : 'Portland', 
                                   'text' : [matrices['vic_matrix']], 
                                   'zauto' : True}, 
                                  {'title.text' : f'<span style="font-size: 30px;"> {title} (VIC RFU) </span>'}], # Could be Bluered, hot
                        ),
                        dict(
                            label="ROX",
                            method="update",
                            args=[{"z": [matrices['rox_matrix']], 
                                   'texttemplate' : "%{text}", 
                                   'colorscale' : 'Portland', 
                                   'text' : [matrices['rox_matrix']],
                                   'zauto' : False,
                                   'zmin' : '1000', 
                                   'zmax' : '6000'},  
                                  {'title.text' : f'<span style="font-size: 30px;"> {title} (ROX RFU) </span>'}], # Could be Bluered, hot
                        )
                    ]
                ),
            )
        ]
    )
    return Template(plotly.offline.plot(heatmap, include_plotlyjs = plotly_js, output_type = 'div'))
        

def format_comments(comments : dict):
    """
    Format the comments in a more readable way
    
    Parameters
    ----------
        comments : dict
            A dict with the keys: Pool, Q1, Q2, Q3, Q4. Each quadrant's values are themselves dictionaries who's keys are the inact
            and elution plates for that quadrant, who's values are a list of comments on that plate in LIMS
        
    Returns
    -------
        A string of html encoding the comments in a way that is nicer to read (the actual comments should appear in red to make them
        stand out)
    """
    comments_str = '<br>Pool plate:<br>'
    if len(comments['Pool']) == 0:
        comments_str += 'None<br>'
    else:
        for comment in comments['Pool']:
            comments_str += f'<span style = "color:red;">{str(comment)}</span><br>'
    comments_str += '<br>'
    for _quadrant in ('Q1', 'Q2', 'Q3', 'Q4'):
        for plate in comments[_quadrant]:
            comments_str += str(plate) + ' (' + _quadrant + '):<br>'
            if len(comments[_quadrant][plate]) == 0:
                comments_str += 'None<br>'
            else:
                for comment in comments[_quadrant][plate]:
                    comments_str += f'<span style = "color:red;">{str(comment)}</span><br>'
            comments_str += '<br>'
    return comments_str


def format_escalations(escalations):
    """
    Format the escalations in a more readable way
    
    Parameters
    ----------
        escalations : list
            A list of escalations stored as strings of text
        
    Returns
    -------
        A string of html encoding the escalations in a way that is nicer to read (the actual escalations should appear in red to make them
        stand out)
    """
    escalations_str = ''
    if len(escalations) == 0:
        escalations_str = 'None<br>'
    else:
        for escalation in escalations:
            escalations_str += f'<span style = "color:red;">{escalation}</span><br>'
    escalations_str += """<br>NOTE: This is not an exhaustive list and service-guidance escalations are not included in this list. You must contine to follow the SOP and service guidance"""
    return escalations_str


def detect_carryover(plate_pos, plate_vic, plate_plods, previous_fam, previous_vic):
    """
    Detects carry-over events of pos to pos, pos to PLOD and RNaseP to RNaseP between one plate and the next
    
    Parameters
    ----------
        plate_pos : iterable
            List of well coordinates which are positive in the current plate
        plate_vic : iterable
            List of well coordinates which are positive for RNaseP in the current plate
        plate_plods : iterable
            List of well coodinates which are PLOD in the current plate
        previous_fam : iterable
            List of well coordinates which were nFAM positive or PLOD in the previous plate
        previous_vic : iterable
            List of well coordinates which were nVIC positive in the previous plate
    """
    pos_carried = ''
    for well in plate_pos:
        if well in previous_fam:
            pos_carried += well + ', '
    pos_carried = pos_carried[0 : len(pos_carried) - 2]
    vic_carried = ''
    for well in plate_vic:
        if well in previous_vic:
            vic_carried += well + ', '
    vic_carried = vic_carried[0 : len(vic_carried) - 2]
    pos_to_plod = ''
    for well in plate_plods:
        if well in previous_fam:
            pos_to_plod += well + ', '
    pos_to_plod = pos_to_plod[0 : len(pos_to_plod) - 2]
    
    return (pos_carried, vic_carried, pos_to_plod)


def get_pool(array_code : str, cur):
    """If the array code's plate is in LIMS, this will return the POOL ID, else it will return None"""
    if cur == None:
        return None
    pool = lims_query(f"""select JOB_NAME from JOB_HEADER where ARRAY_CODE = '{array_code}'""", cur)
    if len(pool) == 0:
        return None
    else:
        return pool[0][0]
