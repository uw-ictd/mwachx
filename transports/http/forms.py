#Django Imports
from django.forms import ModelForm,ModelChoiceField

#Local App Imports
import mwbase.models as mwbase

class SpecialModelChoiceField(ModelChoiceField):

    def label_from_instance(self,obj):
        try:
            return obj.choice_label()
        except AttributeError as e:
            return str(obj)

class ParticipantSendForm(ModelForm):

    def __init__(self,*args,**kwargs):
        super(ParticipantSendForm,self).__init__(*args,**kwargs)
        self.fields['participant'] = SpecialModelChoiceField(queryset=mwbase.Participant.objects.filter(study_group='two-way'))

    class Meta:
        model = mwbase.Message
        fields = ['text', 'participant']

class SystemSendForm(ModelForm):

    def __init__(self,*args,**kwargs):
        super(SystemSendForm,self).__init__(*args,**kwargs)
        self.fields['participant'] = SpecialModelChoiceField(queryset=mwbase.Participant.objects.all())

    class Meta:
        model = mwbase.Message
        fields = ['text', 'participant']
