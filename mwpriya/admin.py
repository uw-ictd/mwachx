from django.contrib import admin

from mwbase.admin import AutomatedMessageAdmin, ParticipantAdmin

import swapper
AutomatedMessage = swapper.load_model("mwbase", "AutomatedMessage")
Participant = swapper.load_model("mwbase", "Participant")

admin.site.unregister(AutomatedMessage)
@admin.register(AutomatedMessage)
class AutomatedMessagePriyaAdmin(AutomatedMessageAdmin):
    smsbank_check_template = "admin/mwpriya/automatedmessagepriya/sms_bank_check.html"
    smsbank_import_template = "admin/mwpriya/automatedmessagepriya/sms_bank_import.html"
    list_filter = ('send_base', 'condition')

admin.site.unregister(Participant)
@admin.register(Participant)
class ParticipantPriyaAdmin(ParticipantAdmin):
	list_display = ParticipantAdmin.list_display
	list_filter = ParticipantAdmin.list_filter
