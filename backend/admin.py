from django.contrib import admin
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.urls import path, reverse

# Local Imports
import backend.models as back
from mwbase.forms import ImportXLSXForm
from mwbase.utils import sms_bank


# Register your models here.

@admin.register(back.AutomatedMessage)
class AutomatedMessageAdmin(admin.ModelAdmin):
    list_display = ('description', 'english', 'todo')
    list_filter = ('send_base', 'condition', 'group', 'todo')
    change_list_template = "admin/backend/automatedmessage/change_list.html"
    smsbank_check_template = "admin/backend/automatedmessage/sms_bank_check.html"
    smsbank_import_template = "admin/backend/automatedmessage/sms_bank_import.html"
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['form'] = ImportXLSXForm
        return super(AutomatedMessageAdmin, self).changelist_view(request, extra_context=extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(r'smsbank_check_view/', self.admin_site.admin_view(self.smsbank_check_view), name='smsbank_check_view'),
            path(r'smsbank_import_view/', self.admin_site.admin_view(self.smsbank_import_view), name='smsbank_import_view')
        ]
        urls = my_urls + urls
        return urls
    
    def smsbank_import_view(self, request, extra_context=None):
        opts = self.model._meta
        app_label = opts.app_label
        form = ImportXLSXForm(request.POST or None, request.FILES or None)
        counts, existing, diff, todo_messages = [], [], [], []
        error = ""
        
        if request.method == 'POST':
            if form.is_valid():
                file = form.cleaned_data.get("file")
                try:
                    counts, existing, diff, todo_messages = sms_bank.import_messages(file)
                except Exception as e:
                    print(e)
                    error = "There was an error importing the given file.  Please try again."
                
                
            context = {
                **self.admin_site.each_context(request),
                'module_name': str(opts.verbose_name_plural),
                'opts': opts,
                'counts': counts,
                'existing': existing,
                'diff': diff,
                'todo_messages': todo_messages,
                'error': error,
                **(extra_context or {}),
            }
        
            return TemplateResponse(request, self.smsbank_import_template or [
                'admin/%s/%s/sms_bank_import.html' % (app_label, opts.model_name),
                'admin/%s/sms_bank_import.html' % app_label,
                'admin/sms_bank_import.html'
            ], context)
    
    def smsbank_check_view(self, request, extra_context=None):
        opts = self.model._meta
        app_label = opts.app_label
        items = duplicates = descriptions = total = todo = None
        form = ImportXLSXForm(request.POST or None, request.FILES or None)

        if request.method == 'POST':
            if form.is_valid():
                file = form.cleaned_data.get("file")
                (items, duplicates, descriptions, total, todo ) = sms_bank.check_messages(file)
                form.helper.form_action = reverse('admin:smsbank_import_view')
                for input in form.helper.inputs:
                    if input.name == 'submit':
                        input.value = "Import File"
        
        context = {
            **self.admin_site.each_context(request),
            'module_name': str(opts.verbose_name_plural),
            'opts': opts,
            'form': form,
            'items': items,
            'duplicates': duplicates,
            'descriptions': descriptions,
            'total': total,
            'todo': todo,
            **(extra_context or {}),
        }
                
        return TemplateResponse(request, self.smsbank_check_template or [
            'admin/%s/%s/sms_bank_check.html' % (app_label, opts.model_name),
            'admin/%s/sms_bank_check.html' % app_label,
            'admin/sms_bank_check.html'
        ], context)

# Example of how to change the admin site if swapping AutomatedMessage class
# @admin.register(back.AutomatedMessageHIV)
# class AutomatedMessageAdminHIV(AutomatedMessageAdmin):
#     list_filter = ('send_base', 'condition', 'group', 'hiv_messaging', 'todo')

