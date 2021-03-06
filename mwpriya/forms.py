# Django Imports
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit
from django import forms
from django.urls import reverse

# Local App Imports
import mwbase.models as mwbase
import utils.forms as util
from mwbase.utils import sms_bank

# Swapper Imports
import swapper
Participant = swapper.load_model("mwbase", "Participant")

class ParticipantAdd(forms.ModelForm):
    phone_number = forms.CharField(label='Phone Number',
                                   widget=forms.TextInput(attrs={'required': 'True', 'placeholder': '07xxxxxxx',
                                                                 'pattern': '^07[0-9]{8}'}))

    def clean_phone_number(self):
        ''' Add custom validation for unique phone number '''
        phone_number = '+254%s' % self.cleaned_data['phone_number'][1:]
        connection = mwbase.Connection.objects.get_or_none(identity=phone_number)
        if connection is not None:
            raise forms.ValidationError("Phone number provided already exists", code="unique")
        return self.cleaned_data['phone_number']

    clinic_visit = forms.DateField(label='Next Clinic Visit')

    def __init__(self, *args, **kwargs):
        super(ParticipantAdd, self).__init__(*args, **kwargs)

        self.fields['due_date'].widget = util.AngularPopupDatePicker({'required': True}, min=3)
        self.fields['birthdate'].widget = util.AngularPopupDatePicker(
            {'required': True, 'datepicker-position-right': True}, max=-5110  # 14 years or older
        )
        self.fields['prep_initiation'].widget = util.AngularPopupDatePicker({'required': True}, max=0)
        self.fields['clinic_visit'].widget = util.AngularPopupDatePicker({'required': True}, min=7)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-sm-6'
        self.helper.field_class = 'col-sm-6'
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Fieldset(
                'Study Information',
                Div(
                    Div('study_id', css_class="col-md-4"),
                    Div('anc_num', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('send_day', css_class="col-md-4"),
                    Div('send_time', css_class="col-md-4"),
                    css_class="row",
                ),
            ),

            Fieldset(
                'Client Information',
                Div(
                    Div('display_name', css_class="col-md-3"),
                    Div('sms_name', css_class="col-md-3"),
                    Div('phone_number', css_class="col-md-3"),
                    Div('birthdate', css_class="col-md-3"),
                    css_class="row"
                ),
                Div(
                    Div('relationship_status', css_class="col-md-4"),
                    Div('partner_name', css_class="col-md-4"),
                    css_class="row"
                ),
                Div(
                    Div('language', css_class="col-md-4"),
                    Div('condition', css_class="col-md-4"),
                    Div('previous_pregnancies', css_class="col-md-4"),
                    css_class="row"
                ),
            ),

            Fieldset(
                'Disclosure and Consent',
                Div(
                    Div('phone_shared', css_class="col-md-4"),
                    css_class="row"
                )
            ),

            Fieldset(
                'Important Dates',
                Div(
                    Div('prep_initiation', css_class="col-md-4"),
                    Div('due_date', css_class="col-md-4"),
                    Div('clinic_visit', css_class="col-md-4"),
                    css_class="row"
                )
            ),
            FormActions(
                Submit('submit', 'Enroll Participant', ng_disabled='participantNewForm.$invalid',
                       style='margin-bottom:20px'),
                css_class="row"
            )
        )

        # thank you: http://stackoverflow.com/questions/24663564/django-add-attribute-to-every-field-by-default
        for field in self:
            field.field.widget.attrs.update({
                'ng-model': 'participant.{0}'.format(field.name),
            })

    class Meta:
        model = Participant
        exclude = ['preg_status', 'facility', 'sms_status']

        widgets = {
            # validation
            'study_id': forms.TextInput(attrs={'ng-pattern': '/^(\d{4}|25\d{6}0)$/', 'required': True}),
            'anc_num': forms.TextInput(attrs={'ng-pattern': '/^\d{4}|(\d{2,}\/)+\d{2,}$/', 'required': True}),
            'previous_pregnancies': forms.NumberInput(attrs={'min': '0', 'max': '15'}),
            'send_day': forms.Select(attrs={'required': True}),
            'send_time': forms.Select(attrs={'required': True}),
            'condition': forms.Select(attrs={'required': True}),
            'sms_name': forms.TextInput(attrs={'required': True}),
            'display_name': forms.TextInput(attrs={'required': True}),
            'language': forms.Select(attrs={'required': True}),
            'phone_shared': forms.NullBooleanSelect(attrs={'required': True}),
        }


class ParticipantUpdate(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['send_day', 'send_time', 'due_date', 'prep_initiation', 'condition', 'quick_notes']

    def __init__(self, *args, **kwargs):
        super(ParticipantUpdate, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'participant-details-form'
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-7'

        self.fields['prep_initiation'].widget = util.AngularPopupDatePicker(max=0)
        self.fields['due_date'].widget = util.AngularPopupDatePicker(min=3, max=280)

        # thank you: http://stackoverflow.com/questions/24663564/django-add-attribute-to-every-field-by-default
        for field in self:
            field.field.widget.attrs.update({
                'ng-model': 'participant.{0}'.format(field.name),
            })


class ImportXLSXForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ImportXLSXForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.form_id = 'import_form'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('admin:smsbank_check_view')
        self.helper.add_input(Submit('submit', 'Check Import'))

    file = forms.FileField(label='Import new SMS Bank', required=True)
