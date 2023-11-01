from django.shortcuts import render, redirect
from poolFinder.functions.config_parse import CONFIG
from poolFinder.models import Batch, AnalysedPlate
from poolFinder.forms import SearchForm, PlateUpdateForm, QueryForm
from django.contrib.auth.decorators import login_required
import poolFinder.functions.app_functions as func
from poolFinder.functions.create_graphs_for_plate import create_plate_charts
from poolFinder.functions.create_tables_for_plate import create_plate_tables
from BackgroundTasks.jobs import start_tasks
import sqlite3
import traceback
from sqlite3 import OperationalError
from django.http import HttpResponse
import poolFinder.functions.form_handlers as form_handlers


@login_required()
def home(request):
    """Displays various statisics for the day and a Levy-Jennings plot (not implimented yet)"""

    day_summary_stats, daily_contams = func.daily_summary()
    levy_jennings_a1 = func.levy_jennings_plot('ARAYA_01', int(CONFIG['LJ_PLATES_TO_DISPLAY']))
    levy_jennings_a2 = func.levy_jennings_plot('ARAYA_02', int(CONFIG['LJ_PLATES_TO_DISPLAY']))

    context = {
        'day_summary_stats' : day_summary_stats,
        'daily_contams' : daily_contams,
        'levy_jennings_a1' : levy_jennings_a1,
        'levy_jennings_a2' : levy_jennings_a2
    }

    return render(request, 'poolFinder/other_views/home.html', context)


@login_required()
def modify_plate(request, pk):
    """For now this is just used to append an escalation to a plates or number of plates"""
    plate_selection = pk

    if request.method  == 'POST':
        return form_handlers.modify_plate(request, plate_selection)

    plates_to_modify = plate_selection.split('-')[1:]
    if plates_to_modify:
        plates_str = ''
        for plate in plates_to_modify:
            plates_str += ', ' + plate
        plates_str = plates_str[2:]
    else:
        plates_str = plate_selection
    form = PlateUpdateForm()

    context = {
        'title' : 'Modify',
        'plates' : plates_str,
        'form' : form
    }

    return render(request, 'poolFinder/other_views/modify_plate.html', context)


@login_required()
def plate(request, pk):
    """Renders an inidividual plate in a way similar to other versions of Pool Helper"""
    array_code = pk

    if request.method == 'POST':
        return form_handlers.modify_plate(request, 'choice-' + array_code)

    plate = AnalysedPlate.objects.filter(array_code = array_code).first()
    batch = plate.batch
    batch_range = batch.batch.split(' - ')
    big_batch = False # Prevents the batchnav from covering up other elements
    if int(batch_range[1][:6]) - int(batch_range[0]) >= 15:
        big_batch = True
    batch_nav_main = func.create_batchnav(batch, plate = plate)
    form = PlateUpdateForm()
    plate = create_plate_charts(plate)
    plate = create_plate_tables(plate)

    context = {
        'title' : plate.array_code,
        'plate' : plate,
        'batch_nav' : batch_nav_main,
        'big_batch' : big_batch,
        'escalations' : plate.escalation_reason.split('$$'),
        'form' : form
    }

    return render(request, 'poolFinder/other_views/plate.html', context)


@login_required()
def batch_overview(request, pk):
    """
    Renders an overview table detailing numerous statistics about the batch and an escalations summary table which can
    be copied into an email easily
    """
    batch_name = pk

    batch = Batch.objects.filter(batch = batch_name).first()
    batch_nav_main = func.create_batchnav(batch)
    escalations = func.escalation_summary(batch)
    for escalation in escalations:
        escalation[escalation.index('user')] = str(request.user).replace('_', ' ').title()

    context = {
        'title' : batch.batch,
        'batch' : batch,
        'batch_nav' : batch_nav_main,
        'escalations' : escalations
    }

    return render(request, 'poolFinder/other_views/batch_overview.html', context)


@login_required()

def search(request):
    """Search for plates"""

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['psearch']
            return redirect('Pool Helper-Search Results', pk=search_term)

    form = SearchForm()
    return render(request, 'poolFinder/other_views/search.html', {'form' : form})


@login_required()
def restart_backgrouns_process(request):
    """
    This view starts a new background task searching for new plates in LIMS by calling BackgroundTasks.start_tasks()
    Useful for if this process has crashed for some reason. Only works if the user accessing the view has staff status
    """
    if request.user.is_staff:
        start_tasks()

    return redirect('Pool Helper-Home')


@login_required()
def database_api(request):
    if request.method == 'POST':
        form = QueryForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            try:
                connection = sqlite3.connect('file:db.sqlite3?mode=ro', uri=True)
                response = connection.execute(query).fetchall()
                return HttpResponse(response)
            except OperationalError:
                return HttpResponse(traceback.format_exc())

    form = QueryForm()
    return render(request, 'poolFinder/other_views/query.html', {'form' : form})
