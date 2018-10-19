from django.contrib import admin

from mwbase.admin import AutomatedMessageAdmin, ParticipantAdmin

import swapper
AutomatedMessage = swapper.load_model("mwbase", "AutomatedMessage")
Participant = swapper.load_model("mwbase", "Participant")

admin.site.unregister(AutomatedMessage)
@admin.register(AutomatedMessage)
class AutomatedMessageHIVAdmin(AutomatedMessageAdmin):
    smsbank_check_template = "admin/mwhiv/automatedmessagehiv/sms_bank_check.html"
    smsbank_import_template = "admin/mwhiv/automatedmessagehiv/sms_bank_import.html"
    list_filter = ('send_base', 'condition', 'group', 'hiv_messaging')

admin.site.unregister(Participant)
@admin.register(Participant)
class ParticipantHIVAdmin(ParticipantAdmin):
	list_display = ParticipantAdmin.list_display + ('hiv_messaging',)
	list_filter = ParticipantAdmin.list_filter + ('hiv_messaging',)
