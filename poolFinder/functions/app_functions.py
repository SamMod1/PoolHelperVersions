from poolFinder.models import AnalysedPlate, Batch, ArayaThresholds, Sample
from poolFinder.functions.config_parse import CONFIG
import plotly
from decimal import Decimal
from django.urls import reverse
from datetime import datetime
import pandas as pd


def lims_query(query : str) -> list:
    """Executes and returns the query"""
    CONFIG['CUR'].execute(query)
    return CONFIG['CUR'].fetchall()


def round_fixed(flt : float, decimal_places = 0):
    """Rounds without floating point errors (yay!)"""
    return float(round(Decimal(str(flt)), decimal_places))


def get_thresholds(araya):
    """
    Gets the araya thresholds (defined in the Pool Helper database) for the given araya and returns them in a dictionary

    RETURNS:
        Dict - Contains thresholds in the keys: POSITIVE, NEGATIVE, nVIC, LOW_ROX, HIGH_ROX    
    """
    thresholds = ArayaThresholds.objects.filter(araya = araya).first()
    return dict(
        POSITIVE = thresholds.positive,
        NEGATIVE = thresholds.negative,
        nVIC = thresholds.nvic,
        LOW_ROX = thresholds.low_rox,
        HIGH_ROX = thresholds.high_rox
    )


def create_batchnav(batch, plate = None):
    """
    Creates html code for a list of buttons which navigate to all the plate pages in the given batch as well as the
    batch overview page for the batch
    
    RETURNS:
        str - HTML code for the batch navigation list
    """
    batch_nav_main = CONFIG['BATCHNAV_MAIN']
    batch_nav_item = CONFIG['BATCHNAV_ITEM']
    if plate:
        items_str = f'<a href="{reverse("Pool Helper-Batch Overview", args={batch.batch: "pk"})}" class="list-group-item list-group-item-action bg-light text-dark font-weight-bold">Overview</a>'
    else:
        items_str = f'<a href="{reverse("Pool Helper-Batch Overview", args={batch.batch: "pk"})}" class="list-group-item list-group-item-action bg-secondary text-light font-weight-bold">Overview</a>'

    buffers = batch.buffers
    prios = batch.prio_plates
    vips = batch.vip_plates

    for batch_plate in batch.plates.split('-'):
        text_color = 'text-dark'
        plate_str = batch_nav_item
        #plate_str = plate_str.replace('$button_name$', batch_plate)
        plate_str = plate_str.replace('$ref$', reverse('Pool Helper-Plate', args={batch_plate: 'pk'})).replace('$button_name$', batch_plate)

        if plate:
            if batch_plate == plate.array_code:
                text_color = 'text-light'
                plate_str = plate_str.replace('bg-light', 'bg-secondary').replace(
                    f'/Pool-Helper/plate/{plate.array_code}/', '#')
        if batch_plate in buffers:
            text_color = 'text-success'
        elif batch_plate in vips:
            text_color = 'text-warning'
        elif batch_plate in prios:
            text_color = 'text-danger'

        items_str += plate_str.replace('$text_color$', text_color)

    return batch_nav_main.replace('$items$', items_str)


def remove_text_in_brackets(string):
    """Does what it says on tin"""
    if not '(' in string or not ')' in string:
        return string
    string = string.split('(')[0] + string.split(')')[1]
    if '  ' in string:
        string = string.replace('  ', ' ')
    if string[-1] == ' ':
        string = string[:-1]
    return string


def create_araya_choices():
    """Returns HTML code for a dropdown selection box containing selections for each available araya"""
    arayas = [x.araya for x in ArayaThresholds.objects.all()]
    choice_html = '<select name="araya_choice" id="araya_choice">'
    for araya in arayas:
        choice_html += f'<option value="{araya}">{araya}</option>'
    choice_html += '</select>'
    return choice_html


def _daily_contams(plates_today):
    """
    Creates a list of tuples which together represent a table of information about all of the blank-well contaminations on
    the given plates

    PARAMETERS
        plates_today - An iterable containing all AnalysedPlate objects of plates from today

    RETURNS
        list - Containing tuples with following data: (
            plate array code, 
            number of positive contams, 
            number of negative contams,
            plate type ('SAMPLE' or 'BUFFER')
        )
    """
    blanks = pd.DataFrame(list(Sample.objects.filter(plate__in=plates_today, barcode='').all().values()))
    blanks['result'] = 0

    for plate in plates_today:
        thresholds = get_thresholds(plate.araya)
        blanks = blanks.loc[~((blanks['rox'] < thresholds['LOW_ROX']) & (blanks['plate_id'] == plate.array_code))]
        blanks.loc[(blanks['nfam'] >= thresholds['POSITIVE']) & (blanks['plate_id'] == plate.array_code), 'result'] = 2
        blanks.loc[
            (thresholds['NEGATIVE'] <= blanks['nfam']) &
            (blanks['nfam'] < thresholds['POSITIVE']) &
            (blanks['plate_id'] == plate.array_code),
            'result'
        ] = 1

    blank_contams = blanks.loc[blanks['result'] > 0]
    contams = []
    contam_plates = blank_contams['plate_id'].unique()

    for plate in plates_today:
        if plate.array_code in contam_plates:
            plate_name = plate.array_code
            pos_contams = len(blank_contams.loc[
                (blank_contams['plate_id'] == plate.array_code) &
                (blank_contams['result'] == 2)
            ])
            plod_contams = len(blank_contams.loc[
                (blank_contams['plate_id'] == plate.array_code) &
                (blank_contams['result'] == 1)
            ])
            if plate.pool == 'None':
                plate_type = 'Buffer'
            else:
                plate_type = 'Sample'
            contams.append((plate_name, pos_contams, plod_contams, plate_type))

    contams.append((':', 'Total: ' + str(sum([x[1] for x in contams])), 'Total: ' + str(sum([x[2] for x in contams])), ''))

    return contams

def daily_summary():
    """
    Creates a summary of the number of plates and samples released today and all plates which have had contaminated blank
    wells today
    """
    batches_today = Batch.objects.filter(batch_time__date=datetime.today().date()).all()
    plates_today = []
    for batch in batches_today:
        plates_today.extend([x for x in batch.plates.split('-')])
    plates_today = AnalysedPlate.objects.filter(array_code__in=plates_today).all()
    plates_today = [x for x in plates_today if len(x.array_code) == 6]
    not_in_ff = []
    in_ff = []
    pools = []
    for plate in plates_today:
        if not plate.in_ff:
            not_in_ff.append(plate.array_code)
            if not plate.pool == 'None':
                pools.append(plate.pool)
        elif plate.show_in_plates_in_fastfinder:
            in_ff.append(plate.array_code)

    if pools:
        pools_str = str(tuple(pools))
        if len(pools) == 1:
            pools_str = pools_str.replace(',', '')
        query = CONFIG['SAMPLES_RELEASED_QUERY'].replace('$plates$', pools_str)
        samp_table = [x for x in lims_query(query) if not x[2] in CONFIG['NON_PATIENT_CODES']]

        num_plates_released = len(set([x[0] for x in samp_table]))
        num_samples_released = len(samp_table)

        daily_contams = _daily_contams(plates_today)
    else:
        num_plates_released = 0
        num_samples_released = 0

        daily_contams = ()

    daily_summary = ('Number of plates released: ', num_plates_released), ('Number of samples released: ', num_samples_released)

    return daily_summary, daily_contams


def find_test_channels_from_comments(plate):
    """
    RETURNS:
        str - contains a list of test channels for the current plate
    """
    plate_comments = plate.formatted_info['comments'].upper()
    channels = ''

    if 'VIP' in plate_comments:
        channels += 'VIP, '
    if 'OLT' in plate_comments:
        channels += 'OLT, '
    if 'RTS' in plate_comments:
        channels += 'RTS, '
    if 'HTK' in plate_comments:
        channels += 'HTK, '
    if 'PRK' in plate_comments:
        channels += 'PRK, '
    if 'AVA' in plate_comments:
        channels += 'AVA, '
    if plate.is_prio:
        channels += 'PRIO, '
    if plate.is_vip:
        channels += 'VIP, '
    if channels == '':
        channels = 'Not Given, '

    return channels[:-2]


def _format_escalations(escalations):
    escalations_str = ''

    escalations_list = [x for x in escalations.split('$$') if x]
    for escalation in escalations_list:
        escalations_str += 'Reason: ' + escalation.replace(' - Comment:', '<br>Comment:') + '<br><br>'
    return escalations_str[:-8]


def escalation_summary(batch):
    """
    Creates a list of lists which represents the data for a table containing all of the escalation details for each
    escalated plate on the given batch

    RETURNS
        list - Contains lists with the following data for each escalated plate:
            array code,
            test channels,
            escalation reason(s),
            user (just a string which says 'user', this is later replaced with the current user)
    """
    summaries = []
    user = 'user'
    escalations = batch.escalations

    if escalations:
        for array_code in escalations.split(', '):
            plate = AnalysedPlate.objects.filter(array_code=array_code).first()
            plate.is_prio = plate.prio
            plate.is_vip = plate.vip
            plate.formatted_info = {'comments' : plate.pl_comments}
            channels = find_test_channels_from_comments(plate)
            escalation_reason = _format_escalations(plate.escalation_reason)
            summaries.append([array_code, channels, escalation_reason, '', '', user, '', '', '', ''])
        return summaries
    else:
        return [['No Escalations', '', '', '', '', user, '', '', '', '']]


def _add_lj_plot_lines(araya : str, control : str, line_width : int):
    """
    Creates a list of dictionaries which can be used to add plot lines to plotly graphs. These lines will correspond
    to the levy-jennings mean, and sd lines
    
    Parameters
    ----------
        araya: str - The araya the plate was run on
        control: str - which control has been used. Choices: accu, qpos, qneg
        line_width: the width of the plotly lines
    
    Returns
    -------
        A list which can be added to a plotly object as shapes (will contain the lines specified by the parameters above)
    """
    araya_config = ArayaThresholds.objects.filter(araya=araya).first()
    mean = getattr(araya_config, f'lj_mean_{control}')
    sd = getattr(araya_config, f'lj_sd_{control}')

    lines = [
        ['y', mean, 'grey'],
        ['y', mean + sd, 'green'],
        ['y', mean - sd, 'green'],
        ['y', mean + sd*2, 'orange'],
        ['y', mean - sd*2, 'orange'],
        ['y', mean + sd*3, 'red'],
        ['y', mean - sd*3, 'red']
    ]

    shapes = []
    for line in lines:
        axis = line[0]
        if axis == 'y':
            other_axis = 'x'
        else:
            other_axis = 'y'
        shapes.append({'type' : 'line', axis+'ref' : axis, axis+'0' : line[1], axis+'1' : line[1], other_axis+'ref' : 'paper',
                                      other_axis+'0' : 0, other_axis+'1' : 1, 'line' : {'color' : line[2], 'width' : line_width, 'dash' : 'dot'}})
    return shapes


def _create_lj_plot(df, araya):
    accu_wells = CONFIG['ACCUPLEX_WELLS'].split(', ')
    negcon_wells = CONFIG['NEGCON_WELLS'].split(', ')
    qnos_wells = CONFIG['QNOS_WELLS'].split(', ')

    accu_plate_means = []
    neg_plate_means = []
    qnos_plate_means = []
    
    accu_df = df.loc[df['x384_well'].isin(accu_wells)]
    negcon_df = df.loc[df['x384_well'].isin(negcon_wells)]
    qnos_df = df.loc[df['x384_well'].isin(qnos_wells)]
    
    unique_plates = df['plate_id'].unique()

    for plate in unique_plates:
        accu_plate_means.append(accu_df.loc[accu_df['plate_id'] == plate, 'nfam'].mean())
        neg_plate_means.append(negcon_df.loc[negcon_df['plate_id'] == plate, 'nfam'].mean())
        qnos_plate_means.append(qnos_df.loc[qnos_df['plate_id'] == plate, 'nfam'].mean())

    plot = plotly.graph_objects.Figure()
    plot.add_trace(plotly.graph_objects.Scatter(
        name = 'Accuplex',
        x=accu_df['plate_id'], y=accu_df['nfam'], 
        mode = 'markers', marker={'color':'red'}
    ))
    plot.add_trace(plotly.graph_objects.Scatter(
        name = 'Accu Mean',
        x = unique_plates, y = accu_plate_means,
        mode = 'lines', marker={'color':'red'}
    ))

    plot.add_trace(plotly.graph_objects.Scatter(
        name = 'Qnos Negative',
        x=negcon_df['plate_id'], y=negcon_df['nfam'], 
        mode = 'markers', marker={'color':'darkgreen'}
    ))
    plot.add_trace(plotly.graph_objects.Scatter(
        name = 'Qneg Mean',
        x = unique_plates, y = neg_plate_means,
        mode = 'lines', marker={'color':'darkgreen'}
    ))

    plot.add_trace(plotly.graph_objects.Scatter(
        name = 'Qnos Positive',
        x=qnos_df['plate_id'], y=qnos_df['nfam'], 
        mode = 'markers', marker={'color':'blue'}
    ))
    plot.add_trace(plotly.graph_objects.Scatter(
        name = 'Qpos Mean',
        x = unique_plates, y = qnos_plate_means,
        mode = 'lines', marker={'color':'blue'}
    ))

    accu_lines = _add_lj_plot_lines(araya, 'accu', CONFIG['GRAPH_LINE_SIZE'])
    qneg_lines = _add_lj_plot_lines(araya, 'qneg', CONFIG['GRAPH_LINE_SIZE'])
    qpos_lines = _add_lj_plot_lines(araya, 'qpos', CONFIG['GRAPH_LINE_SIZE'])

    plot.update_layout(
        updatemenus=[
        dict(
            type="buttons",
            direction="right",
            active=0,
            x=0.57,
            y=1.2,
            buttons=list([
                dict(label="All",
                     method="update",
                     args=[{"visible": [True, True, True, True, True, True]},
                        {"shapes": []}]),
                dict(label="Accuplex",
                     method="update",
                     args=[{"visible": [True, True, False, False, False, False]},
                     {"shapes": accu_lines}]),
                dict(label="Negative",
                     method="update",
                     args=[{"visible": [False, False, True, True, False, False]},
                     {"shapes": qneg_lines}]),
                dict(label="Qnos Positive",
                     method="update",
                     args=[{"visible": [False, False, False, False, True, True]},
                     {"shapes": qpos_lines}]),
            ]),
        )
    ]
    )
    plot.update_layout(paper_bgcolor = CONFIG['BACKGROUND_COLOUR'], width = 1000, plot_bgcolor = 'lightblue')
    plot.update_xaxes(title_text = 'Plate')
    plot.update_yaxes(title_text = 'nFAM')

    return plot


def levy_jennings_plot(araya : str, n_plates : int):
    if CONFIG['DISPLAY_LEVY_JENNINGS'] == 'FALSE':
        return 'Feature Disabled'

    plates_to_include = AnalysedPlate.objects.filter(araya=araya).exclude(pool='None').order_by('-date_in')[:n_plates]
    
    df = pd.DataFrame(Sample.objects.filter(
        plate__in=plates_to_include,
        barcode='Con',
    ).all().values())

    if len(df) == 0:
        return
    
    plate_order = [x.array_code for x in plates_to_include]
    plate_order.reverse()
    df['plate_id'] = df['plate_id'].astype('category')
    df['plate_id'].cat.set_categories(plate_order, inplace=True)
    df = df.sort_values(['plate_id'])

    plot = _create_lj_plot(df, araya)

    plot = plotly.offline.plot(plot, include_plotlyjs=False, output_type='div')

    return plot
