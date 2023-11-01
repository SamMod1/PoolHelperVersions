from django.shortcuts import render, redirect
from django import forms
from poolFinder.models import Batch, AnalysedPlate, PoolFinderConfig
from poolFinder.forms import PlateSelectForm, PageForm
from django.contrib.auth.decorators import login_required
import poolFinder.functions.app_functions as func
from poolFinder.functions.config_parse import CONFIG
import poolFinder.functions.form_handlers as form_handlers
import math
import traceback
import random
import logging


logger = logging.getLogger('django')
RESULTS_PER_PAGE = 100


@login_required()
def batches_awaiting_release(request):
    """Displays all batches with plates still awaiting release. Also allows users to manually upload batches"""
    message_to_user = ''
    if request.method == 'POST':
        try:
            return form_handlers.upload_batch(request)
        except IndexError:
            logger.error(traceback.format_exc())
            message_to_user = "Something went wrong. The plate you entered may not be in LIMS or a file wasn't formatted properly"
        except ValueError:
            logger.error(traceback.format_exc())
            message_to_user = 'Something went wrong. Only numeric characters can be accepted in the plate search'
        except UnboundLocalError :
            logger.error(traceback.format_exc())
            message_to_user = 'Something went wrong. There may have been no araya files attached or array code given'

    context = {
        'title' : 'Batches Awaiting Release',
        'batches': Batch.objects.filter(in_ff=True).order_by('-batch_time').all(),
        'refresh_rate' : int(CONFIG['REFRESH_RATE']) * 2,
        'araya_choice' : func.create_araya_choices(),
        'message_to_user' : message_to_user
    }

    return render(request, 'poolFinder/list_views/batches_awaiting_release.html', context)


@login_required()
def plates_in_ff(request):
    """Displays all plates awaiting release from FastFinder and allows users to hide / escalate a selection of plates"""

    if request.method == 'POST':
        if request.POST['choice'] == 'HIDE':
            return form_handlers.hide_selection(request)
        else:
            return form_handlers.modify_plate_redirect(request)

    plates = AnalysedPlate.objects.filter(in_ff=True, show_in_plates_in_fastfinder=True).order_by('-date_in').all()
    plate_select_form = PlateSelectForm()
    choices = [('HIDE', 'Hide Selection'), ('ES', 'Escalate Selection')]
    fields = {'choice' : forms.ChoiceField(choices = choices)}
    for plate in plates:
        if plate.pool:
            fields[plate.array_code] = forms.BooleanField(label = plate.array_code, required=False)
    plate_select_form.fields = fields
    killroy = False
    if random.random() < 0.1:
        killroy = True

    context = {
        'title' : 'Plates in FastFinder',
        'plates' : plates,
        'refresh_rate' : CONFIG['REFRESH_RATE'],
        'plate_select_form' : plate_select_form,
        'killroy' : killroy
    }
    return render(request, 'poolFinder/list_views/plates_in_ff.html', context)


@login_required()
def archive(request, pk):
    """Plate archive - All plates not shown in 'Plates Awaiting Release'"""
    page_number = pk

    if request.method == 'POST':
        return form_handlers.page_select(request)

    number_of_plates = Batch.objects.filter(in_ff=False).order_by('-batch_time').all().count()
    possible_pages = math.ceil(number_of_plates / 100)
    page = int(page_number)
    upper = (page * RESULTS_PER_PAGE) - 1
    lower = upper - (RESULTS_PER_PAGE - 1)
    form = PageForm()
    context = {
        'title' : 'Archived Plates',
        'batches' : Batch.objects.filter(in_ff=False).order_by('-batch_time').all()[lower:upper],
        'current_page' : page,
        'possible_pages' : possible_pages,
        'refresh_rate' : CONFIG['REFRESH_RATE'],
        'form' : form
    }
    return render(request, 'poolFinder/list_views/archive.html', context)


@login_required()
def search_results(request, pk):
    """
    Displays the results of a search for a list of plates
    OR
    Redirects to a plate if the user only searched for one plate
    """
    search_term = pk
    
    pool = False
    if pk[:4] == 'POOL':
        pool = True
    if '-' in pk:
        pk = pk.split('-')
        if pool:
            plates = AnalysedPlate.objects.filter(pool__in=pk).all()
        else:
            plates = AnalysedPlate.objects.filter(array_code__in=pk).all()
    else:
        if pool:
            plates = AnalysedPlate.objects.filter(pool=pk).all()
        else:
            plates = AnalysedPlate.objects.filter(array_code=pk).all()
        if len(plates) == 1:
            return redirect('Pool Helper-Plate', pk=plates.first().array_code)

    insert = None
    if search_term.upper() == 'GOOSE':
        insert = CONFIG['EGGS_OF_EASTER'].split('$$')[0]

    context = {
        'title' : 'Search Results',
        'plates' : plates,
        'insert' : insert,
        'search_term' : search_term
    }

    return render(request, 'poolFinder/list_views/search_list.html', context)
