from django import forms
from poolFinder.functions.config_parse import CONFIG


if 'ESCALATION_REASONS' in CONFIG:
    ESCALATION_REASONS = CONFIG['ESCALATION_REASONS'].replace('\r', '').split('\n')
    ESCALATIONS = [(str(x), ESCALATION_REASONS[x]) for x in range(len(ESCALATION_REASONS))]
else:
    ESCALATION_REASONS = None
    ESCALATIONS = None


class SearchForm(forms.Form):
    psearch = forms.CharField(label = 'Search', max_length=128)


class QueryForm(forms.Form):
    query = forms.CharField(label = 'Query', max_length=128)


class PageForm(forms.Form):
    page = forms.CharField(label = 'Go to Page', max_length=128)


class PlateUpdateForm(forms.Form):
    if ESCALATIONS:
        escalation = forms.ChoiceField(choices = ESCALATIONS)
    comments = forms.CharField(label = 'Comments', widget=forms.Textarea, required=False)


class PlateSelectForm(forms.Form):
    pass
