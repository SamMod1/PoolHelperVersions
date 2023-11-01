import plotly
import numpy as np
from poolFinder.functions.app_functions import lims_query


LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
X_AXIS = [x + 1 for x in range(24)]


def add_leading_zeros(string: str, length_str_should_be: int) -> str:
    """Adds leading zeros to a string until the string matches the length it should be"""
    while len(string) < length_str_should_be:
        string = '0' + string
    return string


def find_arrays_in_current_batch(first_array_in_batch: int, upper_files, lower_files):
    """
    Takes a list of araya files obtained from the LIMS mirror and returns only the files which are in the current batch
    which is being analysed

    PARAMETERS:
        first_array_in_batch: str - The array code of a plate in the current batch
        upper_files: iterable - Contains tuples for each file: (array_code.csv, file (bytes object)). Only contains files matching
                            array codes which are higher than the first_array_in_batch
        lower_files: iterable - like upper_files but only contains files with array codes lower than first_array_in_batch

    RETURNS:
        list - contains the array codes (+ '.csv') of any files which have a file associated with them in LIMS and are in the
               current batch
    """
    str_array = str(first_array_in_batch)
    if len(str_array) < 6:
        str_array = add_leading_zeros(str_array, 6)
    arrays_to_keep = [str(str_array) + '.csv']
    current_array = first_array_in_batch

    for line in lower_files:
        array = int(line[0][:-4])
        if array == current_array - 1:
            str_array = str(array)
            if len(str_array) < 6:
                str_array = add_leading_zeros(str_array, 6)
            arrays_to_keep.append(str_array + '.csv')
            current_array = array
        else:
            break
    current_array = first_array_in_batch
    for line in upper_files:
        array = int(line[0][:-4])
        if array == current_array + 1:
            str_array = str(array)
            if len(str_array) < 6:
                str_array = add_leading_zeros(str_array, 6)
            arrays_to_keep.append(str_array + '.csv')
            current_array = array
        else:
            break

    return arrays_to_keep


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


def find_stripes(plate_matrix, flag_matrix, glob : dict):
    """
    Determines the size of every vertical and horiztonal stripe of positives on a microplate

    Parameters
    ----------
        plate_matrix : 2D numpy array
            A 2D matrix of this quadrant's nFAM values
        flag_matrix : 2D numpy array
            The current plate's flag matrix, as created by backend_classes.Plate._quadrant_matrices()
        flag_numbers : 2D numpy array
            The current plate's flag numbers matrix, as created by backend_classes.Plate._quadrant_matrices()
        glob : dict
            Contains the global variables for Pool Helper which are stored encrypted on the shared drive
        positive_threshold : int
            The positive threshold for nFAM of the current araya
    
    Returns
    -------
        A tuple containing two numpy arrays which are versions of the flag_matrix and the flag_numbers with any detected stripes
        added into them
    """
    #plate_matrix = plate_matrix.astype(float)
    plate_dimensions = (8, 12)
    for well in glob['x96_CONTROL_WELLS']:
        plate_matrix[well] = 0
    blank_matrix = np.array([[[0,0] for _ in range(plate_dimensions[1])] for _ in range(plate_dimensions[0])])
    adjacent_positives = []
    this_group = []
    for row in range(plate_dimensions[0]):
        for col in range(plate_dimensions[1]):
            if plate_matrix[row, col] > 1:
                if not col == plate_dimensions[1] - 1:
                    if plate_matrix[row, col + 1] > 1 and blank_matrix[row, col + 1][0] == 0:
                        blank_matrix[row, col][0] = 1
                        this_group = []
                        adjacent_positives = [(row, col)]
                        while len(adjacent_positives) > 0:
                            current_well = adjacent_positives[0]
                            this_group.append(current_well)
                            adjacent_positives.pop(0)
                            if current_well[1] + 1 > plate_dimensions[1] - 1:  # I.e if we hit the end of a row
                                break
                            right_well = (current_well[0], current_well[1] + 1)
                            if plate_matrix[right_well] > 1 and blank_matrix[right_well][0] == 0:
                                blank_matrix[right_well][0] = 1
                                adjacent_positives.append(right_well)
                        if len(this_group) >= glob['STRIPE_LIMIT'][0]:
                            for well in this_group:
                                if flag_matrix[well] == 'None':
                                    flag_matrix[well] = 'Stripe'
                if not row == plate_dimensions[0] - 1:
                    if plate_matrix[row + 1, col] > 1 and blank_matrix[row + 1, col][1] == 0:
                        blank_matrix[row, col][1] = 1
                        this_group = []
                        adjacent_positives = [(row, col)]
                        while len(adjacent_positives) > 0:
                            current_well = adjacent_positives[0]
                            this_group.append(current_well)
                            adjacent_positives.pop(0)
                            if current_well[0] + 1 > plate_dimensions[0] - 1:
                                break
                            well_below = (current_well[0] + 1, current_well[1])
                            if plate_matrix[well_below] > 1 and blank_matrix[well_below][1] == 0:
                                blank_matrix[well_below][1] = 1
                                adjacent_positives.append(well_below)
                        if len(this_group) >= glob['STRIPE_LIMIT'][1]:
                            for well in this_group:
                                if flag_matrix[well] == 'None':
                                    flag_matrix[well] = 'Stripe'
    return flag_matrix


def format_escalations(escalations):
    """
    Format the escalations in a more readable way
    
    Parameters
    ----------
        escalations : list
            A list of escalations stored as strings of text
        
    Returns
    -------
        A string of escalation reasons, each seperated by the characters '$$' (this can be saved to the database then later
        split into a list using str.split())
    """
    if not escalations:
        return 'NONE'
    escalations_str = ''
    for escalation in escalations:
        escalations_str += escalation + '$$'
    return escalations_str

def format_comments(comments : dict, pool : str):
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
    comments_str = f'<br>{pool}:<br>'
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
