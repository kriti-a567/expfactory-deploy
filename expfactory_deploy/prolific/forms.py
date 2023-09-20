
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit, Div
from django import forms
from django.forms import ModelForm
from django.forms import modelformset_factory, formset_factory

from experiments import models as exp_models
from prolific import models

class SimpleCCForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model  = models.SimpleCC
        fields = ["completion_url"]

class StudyCollectionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model  = models.StudyCollection
        fields = ["name", "project", "reward", "total_available_places", "estimated_completion_time", "title"]
        widgets = {
            "name": forms.TextInput(),
            "project": forms.TextInput(),
            "title": forms.TextInput(),
        }

class StudyForm(ModelForm):
    class Meta:
        model  = models.Study
        fields = ["battery"]

'''
class StudyRankForm(ModelForm):
    class Meta:
        model  = models.StudyRank
        fields = ["study", "rank"]


StudyRankFormset = modelformset_factory(
    models.StudyRank,
    form=StudyRankForm,
    can_delete=True,
    extra=0,
)

'''
class BatteryRankForm(forms.Form):
    rank = forms.IntegerField()
    battery = forms.ModelChoiceField(queryset=exp_models.Battery.objects.all())

    class Meta:
        widgets = {
            "rank": forms.HiddenInput(),
            "battery": forms.HiddenInput(),
        }

BatteryRankFormset = formset_factory(
    form=BatteryRankForm,
    can_delete=True,
    extra=0,
)

class ParticipantIdForm(forms.Form):
    ids = forms.CharField(widget=forms.Textarea(attrs={"cols": 60, "rows": 25}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))

    def clean_ids(self):
        ids = self.cleaned_data["ids"]
        ids_split = ids.replace('\n', ',').split(',')
        ids_cleaned = [x.strip() for x in ids_split if len(x) > 4]
        return ids_cleaned
