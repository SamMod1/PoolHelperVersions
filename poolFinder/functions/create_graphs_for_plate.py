from poolFinder.models import ArayaThresholds, Sample
from poolFinder.functions.config_parse import CONFIG
from poolFinder.functions.app_functions import round_fixed
import plotly
import numpy as np
import pandas as pd


_384_WELL_POSITIONS = string = [["Q1 A1","Q2 A1","Q1 A2","Q2 A2","Q1 A3","Q2 A3","Q1 A4","Q2 A4","Q1 A5","Q2 A5","Q1 A6","Q2 A6","Q1 A7","Q2 A7","Q1 A8","Q2 A8","Q1 A9","Q2 A9","Q1 A10","Q2 A10","Q1 A11","Q2 A11","Q1 A12","Q2 A12"],["Q3 A1","Q4 A1","Q3 A2","Q4 A2","Q3 A3","Q4 A3","Q3 A4","Q4 A4","Q3 A5","Q4 A5","Q3 A6","Q4 A6","Q3 A7","Q4 A7","Q3 A8","Q4 A8","Q3 A9","Q4 A9","Q3 A10","Q4 A10","Q3 A11","Q4 A11","Q3 A12","Q4 A12"],["Q1 B1","Q2 B1","Q1 B2","Q2 B2","Q1 B3","Q2 B3","Q1 B4","Q2 B4","Q1 B5","Q2 B5","Q1 B6","Q2 B6","Q1 B7","Q2 B7","Q1 B8","Q2 B8","Q1 B9","Q2 B9","Q1 B10","Q2 B10","Q1 B11","Q2 B11","Q1 B12","Q2 B12"],["Q3 B1","Q4 B1","Q3 B2","Q4 B2","Q3 B3","Q4 B3","Q3 B4","Q4 B4","Q3 B5","Q4 B5","Q3 B6","Q4 B6","Q3 B7","Q4 B7","Q3 B8","Q4 B8","Q3 B9","Q4 B9","Q3 B10","Q4 B10","Q3 B11","Q4 B11","Q3 B12","Q4 B12"],["Q1 C1","Q2 C1","Q1 C2","Q2 C2","Q1 C3","Q2 C3","Q1 C4","Q2 C4","Q1 C5","Q2 C5","Q1 C6","Q2 C6","Q1 C7","Q2 C7","Q1 C8","Q2 C8","Q1 C9","Q2 C9","Q1 C10","Q2 C10","Q1 C11","Q2 C11","Q1 C12","Q2 C12"],["Q3 C1","Q4 C1","Q3 C2","Q4 C2","Q3 C3","Q4 C3","Q3 C4","Q4 C4","Q3 C5","Q4 C5","Q3 C6","Q4 C6","Q3 C7","Q4 C7","Q3 C8","Q4 C8","Q3 C9","Q4 C9","Q3 C10","Q4 C10","Q3 C11","Q4 C11","Q3 C12","Q4 C12"],["Q1 D1","Q2 D1","Q1 D2","Q2 D2","Q1 D3","Q2 D3","Q1 D4","Q2 D4","Q1 D5","Q2 D5","Q1 D6","Q2 D6","Q1 D7","Q2 D7","Q1 D8","Q2 D8","Q1 D9","Q2 D9","Q1 D10","Q2 D10","Q1 D11","Q2 D11","Q1 D12","Q2 D12"],["Q3 D1","Q4 D1","Q3 D2","Q4 D2","Q3 D3","Q4 D3","Q3 D4","Q4 D4","Q3 D5","Q4 D5","Q3 D6","Q4 D6","Q3 D7","Q4 D7","Q3 D8","Q4 D8","Q3 D9","Q4 D9","Q3 D10","Q4 D10","Q3 D11","Q4 D11","Q3 D12","Q4 D12"],["Q1 E1","Q2 E1","Q1 E2","Q2 E2","Q1 E3","Q2 E3","Q1 E4","Q2 E4","Q1 E5","Q2 E5","Q1 E6","Q2 E6","Q1 E7","Q2 E7","Q1 E8","Q2 E8","Q1 E9","Q2 E9","Q1 E10","Q2 E10","Q1 E11","Q2 E11","Q1 E12","Q2 E12"],["Q3 E1","Q4 E1","Q3 E2","Q4 E2","Q3 E3","Q4 E3","Q3 E4","Q4 E4","Q3 E5","Q4 E5","Q3 E6","Q4 E6","Q3 E7","Q4 E7","Q3 E8","Q4 E8","Q3 E9","Q4 E9","Q3 E10","Q4 E10","Q3 E11","Q4 E11","Q3 E12","Q4 E12"],["Q1 F1","Q2 F1","Q1 F2","Q2 F2","Q1 F3","Q2 F3","Q1 F4","Q2 F4","Q1 F5","Q2 F5","Q1 F6","Q2 F6","Q1 F7","Q2 F7","Q1 F8","Q2 F8","Q1 F9","Q2 F9","Q1 F10","Q2 F10","Q1 F11","Q2 F11","Q1 F12","Q2 F12"],["Q3 F1","Q4 F1","Q3 F2","Q4 F2","Q3 F3","Q4 F3","Q3 F4","Q4 F4","Q3 F5","Q4 F5","Q3 F6","Q4 F6","Q3 F7","Q4 F7","Q3 F8","Q4 F8","Q3 F9","Q4 F9","Q3 F10","Q4 F10","Q3 F11","Q4 F11","Q3 F12","Q4 F12"],["Q1 G1","Q2 G1","Q1 G2","Q2 G2","Q1 G3","Q2 G3","Q1 G4","Q2 G4","Q1 G5","Q2 G5","Q1 G6","Q2 G6","Q1 G7","Q2 G7","Q1 G8","Q2 G8","Q1 G9","Q2 G9","Q1 G10","Q2 G10","Q1 G11","Q2 G11","Q1 G12","Q2 G12"],["Q3 G1","Q4 G1","Q3 G2","Q4 G2","Q3 G3","Q4 G3","Q3 G4","Q4 G4","Q3 G5","Q4 G5","Q3 G6","Q4 G6","Q3 G7","Q4 G7","Q3 G8","Q4 G8","Q3 G9","Q4 G9","Q3 G10","Q4 G10","Q3 G11","Q4 G11","Q3 G12","Q4 G12"],["Q1 H1","Q2 H1","Q1 H2","Q2 H2","Q1 H3","Q2 H3","Q1 H4","Q2 H4","Q1 H5","Q2 H5","Q1 H6","Q2 H6","Q1 H7","Q2 H7","Q1 H8","Q2 H8","Q1 H9","Q2 H9","Q1 H10","Q2 H10","Q1 H11","Q2 H11","Q1 H12","Q2 H12"],["Q3 H1","Q4 H1","Q3 H2","Q4 H2","Q3 H3","Q4 H3","Q3 H4","Q4 H4","Q3 H5","Q4 H5","Q3 H6","Q4 H6","Q3 H7","Q4 H7","Q3 H8","Q4 H8","Q3 H9","Q4 H9","Q3 H10","Q4 H10","Q3 H11","Q4 H11","Q3 H12","Q4 H12"]]
_96_WELL_POSITIONS = string = {'Q1': np.array([['384 A1', '384 A3', '384 A5', '384 A7', '384 A9', '384 A11', '384 A13', '384 A15', '384 A17', '384 A19', '384 A21', '384 A23'], ['384 C1', '384 C3', '384 C5', '384 C7', '384 C9', '384 C11', '384 C13', '384 C15', '384 C17', '384 C19', '384 C21', '384 C23'], ['384 E1', '384 E3', '384 E5', '384 E7', '384 E9', '384 E11', '384 E13', '384 E15', '384 E17', '384 E19', '384 E21', '384 E23'], ['384 G1', '384 G3', '384 G5', '384 G7', '384 G9', '384 G11', '384 G13', '384 G15', '384 G17', '384 G19', '384 G21', '384 G23'], ['384 I1', '384 I3', '384 I5', '384 I7', '384 I9', '384 I11', '384 I13', '384 I15', '384 I17', '384 I19', '384 I21', '384 I23'], ['384 K1', '384 K3', '384 K5', '384 K7', '384 K9', '384 K11', '384 K13', '384 K15', '384 K17', '384 K19', '384 K21', '384 K23'], ['384 M1', '384 M3', '384 M5', '384 M7', '384 M9', '384 M11', '384 M13', '384 M15', '384 M17', '384 M19', '384 M21', '384 M23'], ['384 O1', '384 O3', '384 O5', '384 O7', '384 O9', '384 O11', '384 O13', '384 O15', '384 O17', '384 O19', '384 O21', '384 O23']], dtype=object),
          'Q2': np.array([['384 A2', '384 A4', '384 A6', '384 A8', '384 A10', '384 A12', '384 A14', '384 A16', '384 A18', '384 A20', '384 A22', '384 A24'], ['384 C2', '384 C4', '384 C6', '384 C8', '384 C10', '384 C12', '384 C14', '384 C16', '384 C18', '384 C20', '384 C22', '384 C24'], ['384 E2', '384 E4', '384 E6', '384 E8', '384 E10', '384 E12', '384 E14', '384 E16', '384 E18', '384 E20', '384 E22', '384 E24'], ['384 G2', '384 G4', '384 G6', '384 G8', '384 G10', '384 G12', '384 G14', '384 G16', '384 G18', '384 G20', '384 G22', '384 G24'], ['384 I2', '384 I4', '384 I6', '384 I8', '384 I10', '384 I12', '384 I14', '384 I16', '384 I18', '384 I20', '384 I22', '384 I24'], ['384 K2', '384 K4', '384 K6', '384 K8', '384 K10', '384 K12', '384 K14', '384 K16', '384 K18', '384 K20', '384 K22', '384 K24'], ['384 M2', '384 M4', '384 M6', '384 M8', '384 M10', '384 M12', '384 M14', '384 M16', '384 M18', '384 M20', '384 M22', '384 M24'], ['384 O2', '384 O4', '384 O6', '384 O8', '384 O10', '384 O12', '384 O14', '384 O16', '384 O18', '384 O20', '384 O22', '384 O24']], dtype=object),
          'Q3': np.array([['384 B1', '384 B3', '384 B5', '384 B7', '384 B9', '384 B11', '384 B13', '384 B15', '384 B17', '384 B19', '384 B21', '384 B23'], ['384 D1', '384 D3', '384 D5', '384 D7', '384 D9', '384 D11', '384 D13', '384 D15', '384 D17', '384 D19', '384 D21', '384 D23'], ['384 F1', '384 F3', '384 F5', '384 F7', '384 F9', '384 F11', '384 F13', '384 F15', '384 F17', '384 F19', '384 F21', '384 F23'], ['384 H1', '384 H3', '384 H5', '384 H7', '384 H9', '384 H11', '384 H13', '384 H15', '384 H17', '384 H19', '384 H21', '384 H23'], ['384 J1', '384 J3', '384 J5', '384 J7', '384 J9', '384 J11', '384 J13', '384 J15', '384 J17', '384 J19', '384 J21', '384 J23'], ['384 L1', '384 L3', '384 L5', '384 L7', '384 L9', '384 L11', '384 L13', '384 L15', '384 L17', '384 L19', '384 L21', '384 L23'], ['384 N1', '384 N3', '384 N5', '384 N7', '384 N9', '384 N11', '384 N13', '384 N15', '384 N17', '384 N19', '384 N21', '384 N23'], ['384 P1', '384 P3', '384 P5', '384 P7', '384 P9', '384 P11', '384 P13', '384 P15', '384 P17', '384 P19', '384 P21', '384 P23']], dtype=object),
          'Q4': np.array([['384 B2', '384 B4', '384 B6', '384 B8', '384 B10', '384 B12', '384 B14', '384 B16', '384 B18', '384 B20', '384 B22', '384 B24'], ['384 D2', '384 D4', '384 D6', '384 D8', '384 D10', '384 D12', '384 D14', '384 D16', '384 D18', '384 D20', '384 D22', '384 D24'], ['384 F2', '384 F4', '384 F6', '384 F8', '384 F10', '384 F12', '384 F14', '384 F16', '384 F18', '384 F20', '384 F22', '384 F24'], ['384 H2', '384 H4', '384 H6', '384 H8', '384 H10', '384 H12', '384 H14', '384 H16', '384 H18', '384 H20', '384 H22', '384 H24'], ['384 J2', '384 J4', '384 J6', '384 J8', '384 J10', '384 J12', '384 J14', '384 J16', '384 J18', '384 J20', '384 J22', '384 J24'], ['384 L2', '384 L4', '384 L6', '384 L8', '384 L10', '384 L12', '384 L14', '384 L16', '384 L18', '384 L20', '384 L22', '384 L24'], ['384 N2', '384 N4', '384 N6', '384 N8', '384 N10', '384 N12', '384 N14', '384 N16', '384 N18', '384 N20', '384 N22', '384 N24'], ['384 P2', '384 P4', '384 P6', '384 P8', '384 P10', '384 P12', '384 P14', '384 P16', '384 P18', '384 P20', '384 P22', '384 P24']], dtype=object)}
X_AXIS = [x + 1 for x in range(24)]
LETTERS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P")
x384_PLATE_DIMENSIONS = (16, 24)
x96_PLATE_DIMENSIONS = (8, 12)
FLAG_COLOURS = {'None': 0, 'Pos fail': 1, 'Neg fail': 1, 'VIC accu': 1, 'ROX accu': 1, 'ROX qnos': 1, 'ROX negcon': 1, 'Stripe': 3,
                    'SPA ROX': 6, 'ENV ROX': 6, 'ROX fail': 6, 'Contam': 5, 'MM-only': 2, 'VIC fail': 4, 'PLOD': 8, 'HI PLOD': 7}
QUAD_OFFSETS = {'Q1' : [0, 0], 'Q2' : [0, 1], 'Q3' : [1, 0], 'Q4' : [1, 1]}


def _plot_platemap(matrices : dict, width : int, height : int, title : str, quadrant = None):
    """
    Creates the interactive plotly heatmaps for the 384-well platemap and the quadrant platemaps
    
    Parameters
    ----------
        matrices : dict
            A dict with the following keys:
                nfam_matrix: Matrix containing the nFAM values as strings round_fixed(ed to two decimals
                nvic_matrix: Contains the nVIC values as strings round_fixed(ed to two decimals
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
        bg_colour : str
            The colour for the background_fixed( of the plot
        plotly_js : bool
            Whether or not to include plotlyjs in the output html template (pool helper 2.0 now inserts a partial plotly bundle
            elsewhere in the code, so this should now always be False)
            
    Returns
    -------
        An html string containing the js code of the plotly platemap
    """
    result_colours = ["rgb(0, 180, 0)", "rgb(255, 183, 71)", "rgb(227, 5, 19)"]
    heading = ''
    vic_title = ''
    patient_barcodes = ~(np.isin(matrices['barcode_matrix'], CONFIG['NON_PATIENT_CODES'].split(', ')))
    pos = ((matrices['result_matrix'] == 2) & patient_barcodes).sum()
    if not quadrant == None:
        total = patient_barcodes.sum()
        labels = _96_WELL_POSITIONS[quadrant]
        if pos > 0:
            heading = f"({pos} positives, {round_fixed((pos / total) * 100, 1)}%)"
        else:
            heading = "(0 positives)"
    else:
        labels = _384_WELL_POSITIONS
        heading = '<span style = "color:rgb(227,5,19);"> Positive</span>, <span style = "color:rgb(255,183,71);">PLOD</span>, <span style = "color:rgb(0,180,0);">Negative</span>'
        vic_title = '<span style = "color:rgb(0,0,188);font-size: 30px;"> Positive, </span><span style = "color:rgb(240,0,240);font-size: 30px;">Negative</span>'
    heatmap = plotly.graph_objects.Figure()
    heatmap.add_trace(plotly.graph_objects.Heatmap(x = X_AXIS[0:len(matrices['nfam_matrix'].tolist()[0])], y = LETTERS[0:len(matrices['nfam_matrix'])],
                                 z = matrices['result_matrix'], showscale = False, xgap = 2, ygap = 2, 
                                 colorscale = [[0.0, result_colours[0]], [0.5, result_colours[1]], [1.0, result_colours[2]]], 
                                 text = matrices['nfam_matrix'], texttemplate = "%{text}", zmin = 0, zmax = 2, customdata = labels,
                                 hovertemplate = '%{y}%{x}<br>(%{customdata})<extra></extra>'))
    heatmap['layout']['yaxis']['autorange'] = "reversed"
    heatmap.update_layout(
        paper_bgcolor = CONFIG['BACKGROUND_COLOUR'], 
        title = f'<span style="font-size: 30px;"> {title} (nFAM) {heading}</span>',
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
                                  {'title.text' : f'<span style="font-size: 30px;"> {title} (nFAM) {heading}</span>'}],
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
    return plotly.offline.plot(heatmap, include_plotlyjs = False, output_type = 'div')


def get_thresholds(araya):
    """This function is duplicated from poolFinder//functions//app_functions due to circular dependency issue IDK how to fix"""
    thresholds = ArayaThresholds.objects.filter(araya = araya).first()
    return dict(
        POSITIVE = thresholds.positive,
        NEGATIVE = thresholds.negative,
        nVIC = thresholds.nvic,
        LOW_ROX = thresholds.low_rox,
        HIGH_ROX = thresholds.high_rox
    )


def scatter_plot(
        plate_df, 
        x : str,
        y : str,
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
        background_fixed(_color: A string in a format compatable with plotly defining a colour of the background_fixed( on which the plot is plotted on.
        bg_color: A string in a format compatable with plotly defining a colour of the background_fixed( for the plot it
        width: The width of the plot.
        height: The hight of the plot.
        title: Title of the graph.
    
    Returns
    -------
        A plotly scatter plot of the relevant data
    """
    plot = plotly.graph_objects.Figure().add_trace(plotly.graph_objects.Scatter(x = plate_df[x], y = plate_df[y], hovertext = plate_df['x384_well'], mode = 'markers'))
    plot.update_layout(width = width, height = height)
    plot.update_xaxes(title_text = x)
    plot.update_yaxes(title_text = y)
    plot.update_layout(paper_bgcolor = CONFIG['BACKGROUND_COLOUR'], plot_bgcolor = bg_color, title = title)
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

    return plotly.offline.plot(plot, include_plotlyjs = False, output_type = 'div')

def _set_fam_result(nfam: float, thresholds: dict):
    """
    Based on the araya threshold returns:
    0 = Negative
    1 = PLOD
    2 = Positive
    """
    if nfam < thresholds['NEGATIVE']:
        return 0
    elif thresholds['NEGATIVE'] <= nfam < thresholds['POSITIVE']:
        return 1
    else:
        return 2

def _set_vic_result(nvic: float, thresholds: dict):
    """
    Based on the araya threshold returns:
    0 = Negative
    1 = Positive
    """
    if nvic < thresholds['nVIC']:
        return 0
    else:
        return 1

def _df_col_to_384_matrix(series):
    """Reshapes a pandas series with a length of 384 into a numpy array with the same dimensions as a 384-well plate"""
    return np.reshape(series.to_numpy(), x384_PLATE_DIMENSIONS)

def _set_flag_color(flag):
    """Because the pandas doccumentation doesn't say that series.apply() can work on dictionary keys"""
    return FLAG_COLOURS[flag]

def _set_barcode_colours(barcodes):
    """
    Takes an iterable of barcode preffixes and turns them into a numbers which represent each unique barcode prefix on the plate
    contained in a numpy array with the dimensions of a 384-well plate.

    RETURNS:
        np.array - Numbers starting from 0 which map to each unique barcode prefix in the given iterable of barcode prefixes
    """
    seen_barcodes = []
    barcode_colours = []
    colour = 0

    for barcode in barcodes:
        if barcode in seen_barcodes:
            barcode_colours.append(seen_barcodes.index(barcode))
        else:
            seen_barcodes.append(barcode)
            barcode_colours.append(colour)
            colour += 1
    
    return np.reshape(np.array(barcode_colours), x384_PLATE_DIMENSIONS)

_number_to_str = np.vectorize(str) # Vectorises the str() function for faster application to numpy arrays

def _create_matrices(plate_df, thresholds):
    """
    Takes a pandas dataframe containing all the data for a given plate and turns that data into 384-well numpy
    array matrices (also creates a few extra matrices relating to the result (according to the araya thresholds)
    and the colours for the flags and barcodes)

    RETURNS:
        dict - containing the following matrices:
            nfam_matrix: Matrix containing the nFAM values as strings round_fixed(ed to two decimals
            nvic_matrix: Contains the nVIC values as strings round_fixed(ed to two decimals
            fam_matrix: Contains the FAM values
            vic_matrix: Contains the VIC values
            rox_matrix: Contains the ROX values
            result_matrix: A matrix representing the platemap of results based on the nFAM value. 0 = Negative, 1 = PLOD, 2 = Positive
            vic_result_matrix: The RNaseP result. 0 = Negative, 1 = Positive
            flag_matrix: A matrix of warnings for wells. Warnings include: PLOD, HI PLOD, VIC FAIL, Pos fail, Neg fail, etc...
            flag_numbers: A matrix of numbers which tells plotly what colour each warning in the notifications tab should be displayed as
            barcode_matrix: A platemap of the barcode preffixes of each sample on the plate
            barcode_colours: A matrix where each unique barcode preffix is assigned a number (used to determine the colours of barcodes)
    """
    result_matrix = _df_col_to_384_matrix(plate_df['nfam'].apply(_set_fam_result, args = (thresholds,)))
    vic_result_matrix = _df_col_to_384_matrix(plate_df['nvic'].apply(_set_vic_result, args = (thresholds,)))
    nfam_matrix = _number_to_str(_df_col_to_384_matrix(plate_df['nfam']))
    nvic_matrix = _number_to_str(_df_col_to_384_matrix(plate_df['nvic']))
    fam_matrix = _df_col_to_384_matrix(plate_df['fam'])
    vic_matrix = _df_col_to_384_matrix(plate_df['vic'])
    rox_matrix = _df_col_to_384_matrix(plate_df['rox'])
    flag_matrix = _df_col_to_384_matrix(plate_df['flag'])
    flag_numbers = _df_col_to_384_matrix(plate_df['flag'].apply(_set_flag_color))
    barcode_colours = _set_barcode_colours(plate_df['barcode'])
    barcode_matrix = _df_col_to_384_matrix(plate_df['barcode'])

    return dict(nfam_matrix = nfam_matrix, rox_matrix = rox_matrix, nvic_matrix = nvic_matrix, result_matrix = result_matrix, 
        vic_result_matrix = vic_result_matrix, fam_matrix = fam_matrix, vic_matrix = vic_matrix, flag_matrix = flag_matrix, 
        flag_numbers = flag_numbers, barcode_colours = barcode_colours, barcode_matrix = barcode_matrix)

def _extract_quadrant_matrices(matrices):
    """
    Extracts the four quadrants from a dictionary of 384-well numpy matrices and returns the dictionary with these new matrices
    added into it. This method also checks for striping of positive samples on quadrants based on service guidance and alters the
    flag_matrix accordingly
    
    PARAMETERS:
        matrices: A dictionary containing various 384-well matrices, including a flag matrix
        
    RETURNS:
        dict containing all the matrices passed to the function with new keys: Q1, Q2, Q3 & Q4 who's values are dictionaries containing
        all the matrices for that individual quadrant
    """
    new_matrices = {
        '384' : matrices, 
        'Q1' : {}, 
        'Q2' : {}, 
        'Q3' : {}, 
        'Q4' : {}
    }
    for matrix in matrices:
        for quadrant in QUAD_OFFSETS:
            new_matrices[quadrant][matrix] = np.array([[None for _ in range(12)] for _ in range(8)])
            for row in range(x96_PLATE_DIMENSIONS[0]):
                for col in range(x96_PLATE_DIMENSIONS[1]):
                    new_matrices[quadrant][matrix][row, col] = matrices[matrix][row * 2 + QUAD_OFFSETS[quadrant][0], col * 2 + QUAD_OFFSETS[quadrant][1]]
    return new_matrices

def create_plate_charts(plate):
    """
    Creates the plotly platemaps and scatter charts for a given plate
    
    This function will then append the javascript code for these platemaps to attributes of the plate named:
        plate.x384_platemap - 384-well platemap
        plate.q1_platemap, plate.q2_platemap, plate.q3_platemap, plate.q4_platemap - 96-well platemaps for each quadrant
        plate.rox_v_fam_scatter - ROX vs FAM scatterchart
        plate.rox_v_nfam_scatter - ROX vs nFAM scatterchart
        plate.rox_v_vic_scatter - ROX vs VIC scatterchart
        plate.rox_v_nvic_scatter - ROX vc nVIC scatterchart
        plate.nfam_v_nvic_scatter - nFAM vs nVIC scatterchart
    
    RETURNS:
        AnalysedPlate - The supplied plate object with the above attributes appended
    """
    thresholds = get_thresholds(plate.araya)
    plate_df = pd.DataFrame(list(Sample.objects.filter(plate=plate.array_code).all().values()))

    matrices = _create_matrices(plate_df, thresholds)
    matrices = _extract_quadrant_matrices(matrices)
    plate.x384_platemap = _plot_platemap(matrices['384'], 1400, 800, '384 platemap')
    plate.q1_platemap = _plot_platemap(matrices['Q1'], 775, 470, 'Quadrant 1', quadrant = 'Q1')
    plate.q2_platemap = _plot_platemap(matrices['Q2'], 775, 470, 'Quadrant 2', quadrant = 'Q2')
    plate.q3_platemap = _plot_platemap(matrices['Q3'], 775, 470, 'Quadrant 3', quadrant = 'Q3')
    plate.q4_platemap = _plot_platemap(matrices['Q4'], 775, 470, 'Quadrant 4', quadrant = 'Q4')

    rvf = scatter_plot(plate_df, 'rox', 'fam', title = 'ROX vs FAM')
    rvnf = scatter_plot(plate_df, 'rox', 'nfam', title = 'ROX vs nFAM')
    rvv = scatter_plot(plate_df, 'rox', 'vic', title = 'ROX vs VIC')
    rvnv = scatter_plot(plate_df, 'rox', 'nvic', title = 'ROX vs nVIC')
    nfvnv = scatter_plot(plate_df, 'nvic', 'nfam', title = 'nFAM vs nVIC')
    
    rvf = add_plot_lines(rvf, [['x', thresholds['LOW_ROX'], 'Orange'],
                                    ['x', thresholds['HIGH_ROX'], 'Orange'],], int(CONFIG['GRAPH_LINE_SIZE']))
    rvnf = add_plot_lines(rvnf, [['y', thresholds['NEGATIVE'], 'Green'],
                                    ['y', thresholds['POSITIVE'], 'Red'],
                                    ['x', thresholds['LOW_ROX'], 'Orange'],
                                    ['x', thresholds['HIGH_ROX'], 'Orange'],], int(CONFIG['GRAPH_LINE_SIZE']))
    rvv = add_plot_lines(rvv, [['x', thresholds['LOW_ROX'], 'Orange'],
                                    ['x', thresholds['HIGH_ROX'], 'Orange'],], int(CONFIG['GRAPH_LINE_SIZE']))
    rvnv = add_plot_lines(rvnv, [['y', thresholds['nVIC'], 'Yellow'],
                                    ['x', thresholds['LOW_ROX'], 'Orange'],
                                    ['x', thresholds['HIGH_ROX'], 'Orange'],], int(CONFIG['GRAPH_LINE_SIZE']))
    nfvnv = add_plot_lines(nfvnv, [['y', thresholds['NEGATIVE'], 'Green'],
                                    ['y', thresholds['POSITIVE'], 'Red'],
                                    ['x', thresholds['nVIC'], 'Yellow']], int(CONFIG['GRAPH_LINE_SIZE']))
    plate.rox_v_fam_scatter = rvf
    plate.rox_v_nfam_scatter = rvnf
    plate.rox_v_vic_scatter = rvv
    plate.rox_v_nvic_scatter = rvnv
    plate.nfam_v_nvic_scatter = nfvnv
    
    plate.thresholds = thresholds # for use in a function later on

    return plate
