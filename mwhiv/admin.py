from django.contrib import admin

from mwbase.admin import AutomatedMessageAdmin

import swapper
AutomatedMessage = swapper.load_model("mwbase", "AutomatedMessage")

admin.site.unregister(AutomatedMessage)
@admin.register(AutomatedMessage)
class AutomatedMessageHIVAdmin(AutomatedMessageAdmin):
    smsbank_check_template = "admin/mwhiv/automatedmessagehiv/sms_bank_check.html"
    smsbank_import_template = "admin/mwhiv/automatedmessagehiv/sms_bank_import.html"
    list_filter = ('send_base', 'condition', 'group', 'hiv_messaging')
