import poolFinder.functions.app_functions as func
from BackgroundTasks.PlateAnalysis.new_plates_manager import manual_upload
from django.shortcuts import redirect
from poolFinder.models import AnalysedPlate
from poolFinder.functions.config_parse import CONFIG, lims_login
from poolFinder.forms import PageForm, PlateUpdateForm


def upload_batch(request):
    """
    Allows users to upload a batch of plates directly, or specify an array code in a batch for the program to download
    and analyse automatically

    REDIRECTS:
        Pool Helper-Batch Overview (of the batch just uploaded)
    """

    if request.POST['array_search']:
        batch_name = manual_upload(request.POST['array_search'], str(request.user), request.POST['araya_choice'])
        return redirect('Pool Helper-Batch Overview', pk = batch_name)
    else:
        files = request.FILES.getlist('upload')
        batch_name = manual_upload(files, str(request.user), request.POST['araya_choice'])
        return redirect('Pool Helper-Batch Overview', pk = batch_name)


def hide_selection(request):
    """
    Modifies a selection of plates so that they will no longer appear in the 'Plates Awaiting Release' view
    
    REDIRECTS:
        Pool Helper-Plates in FF
    """

    plates = [x for x in request.POST if not x == 'csrfmiddlewaretoken']
    plates = AnalysedPlate.objects.filter(array_code__in=plates).all()

    for plate in plates:
        plate.show_in_plates_in_fastfinder = False
        plate.save()

    return redirect('Pool Helper-Plates in FF')


def modify_plate_redirect(request):
    """
    Redirects user to the 'Modify Plate' view based on the criteria in the POST request
    
    REDIRECTS:
        Pool Helper-Modify Plate
    """
    plates_str = ''
    for plate in request.POST:
        if not plate == 'csrfmiddlewaretoken':
            plates_str += '-' + plate
    return redirect('Pool Helper-Modify Plate', pk=plates_str[1:])


def page_select(request):
    """
    Redirects users to the appropriate page in the 'Archive' view based on the POST request
    
    REDIRECTS:
        Pool Helper-Archive
    """
    form = PageForm(request.POST)
    if form.is_valid():
        target_page = form.cleaned_data['page']
        return redirect('Pool Helper-Archive', pk=target_page)
    

def modify_plate(request, plates):
    """
    Currently only used to append an escalation to a plate or multiple plates

    REDIRECTS:
        Pool Helper-Plates in FF
    """
    plates_to_modify = plates.split('-')[1:]

    if not plates_to_modify:
        plates_to_modify = [plates]
    plates_to_modify = AnalysedPlate.objects.filter(array_code__in=plates_to_modify).all()

    form = PlateUpdateForm(request.POST)

    if form.is_valid() and not form.cleaned_data['escalation'] == '0':
        for plate in plates_to_modify:
            batch_to_modify = plate.batch

            if not batch_to_modify.escalations:
                batch_to_modify.escalations = plate.array_code
                batch_to_modify.save()
            elif not plate.array_code in batch_to_modify.escalations:
                batch_to_modify.escalations += ', ' + plate.array_code
                batch_to_modify.save()
                
            plate.escalation_reason += func.remove_text_in_brackets(CONFIG['ESCALATION_REASONS'].replace('\r', '').split('\n')[int(form.cleaned_data['escalation'])])
            if form.cleaned_data['comments']:
                    plate.escalation_reason += ' - Comment: ' + form.cleaned_data['comments']
            plate.escalation_reason = plate.escalation_reason.replace('NONE', '')
            plate.escalation_reason += '$$'
            plate.escalated = True
            plate.save()

    return redirect('Pool Helper-Plates in FF')
