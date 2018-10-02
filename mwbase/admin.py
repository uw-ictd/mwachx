from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.urls import path, reverse
from django.utils import html

from openpyxl.writer.excel import save_virtual_workbook

import utils.admin as utils
# Local Imports
from mwbase import models as mwbase
from mwbase.forms import ImportXLSXForm
from mwbase.utils import sms_bank

import swapper
AutomatedMessage = swapper.load_model("mwbase", "AutomatedMessage")


class ConnectionInline(admin.TabularInline):
    model = mwbase.Connection
    extra = 0


class NoteInline(admin.TabularInline):
    model = mwbase.Note
    extra = 1


def mark_quit(modeladmin, request, queryset):
    ''' mark all mwbase in queryset as quit and save '''
    for c in queryset:
        c.set_status('quit', comment='Status set from bulk quit action')


mark_quit.short_description = 'Mark participant as quit'


def revert_status(modeladmin, request, queryset):
    ''' set the status for each participant in queryset to their previous status '''
    for c in queryset:
        old_status = c.statuschange_set.last().old
        c.set_status(old_status, comment='Status reverted from bulk action')


revert_status.short_description = 'Revert to last status'


@admin.register(mwbase.Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('study_id', 'nickname', 'status', 'description', 'facility',
                    'phone_number', 'due_date', 'language', 'send_day', 'is_validated', 'created')
    list_display_links = ('study_id', 'nickname')
    list_filter = (
    'facility', 'study_group', ('created', admin.DateFieldListFilter), 'status', 'is_validated',
    'language', 'send_day')

    ordering = ('study_id',)

    search_fields = ('study_id', 'nickname', 'connection__identity', 'anc_num')
    readonly_fields = ('last_msg_client', 'last_msg_system', 'created', 'modified')

    inlines = (ConnectionInline, NoteInline)
    actions = (mark_quit, revert_status,)


class ParticipantAdminMixin(object):

    participant_field = 'participant'

    def participant_name(self, obj):
        participant = getattr(obj, self.participant_field)
        if participant is not None:
            return html.format_html(
                "<a href='../participant/{0.pk}'>({0.study_id}) {0.nickname}</a>".format(participant))

    participant_name.short_description = 'Nickname'
    participant_name.admin_order_field = '{}__study_id'.format(participant_field)

    def facility(self, obj):
        participant = getattr(obj, self.participant_field)
        if participant is not None:
            return participant.facility.capitalize()

    facility.admin_order_field = '{}__facility'.format(participant_field)

    def study_id(self, obj):
        return getattr(obj, self.participant_field).study_id

    study_id.short_description = 'Study ID'
    study_id.admin_order_field = '{}__study_id'.format(participant_field)

    def phone_number(self, obj):
        connection = getattr(obj, self.participant_field).connection()
        if connection is not None:
            return html.format_html("<a href='../connection/{0.pk}'>{0.identity}</a>".format(connection))

    phone_number.short_description = 'Number'
    phone_number.admin_order_field = '{}__connection__identity'.format(participant_field)


@admin.register(mwbase.Message)
class MessageAdmin(admin.ModelAdmin, ParticipantAdminMixin):
    list_display = ('text', 'participant_name', 'identity', 'is_system',
                    'is_outgoing', 'is_reply', 'external_status', 'translation_status', 'created')
    list_filter = ('is_system', 'is_outgoing', 'external_status', ('participant', utils.NullFieldListFilter),
                   ('created', admin.DateFieldListFilter), 'connection__participant__facility',
                   'translation_status', 'is_related', 'external_success')

    date_hierarchy = 'created'

    search_fields = ('participant__study_id', 'participant__nickname', 'connection__identity')
    readonly_fields = ('created', 'modified')

    def identity(self, obj):
        return html.format_html("<a href='./?q={0.identity}'>{0.identity}</a>".format(
            obj.connection
        ))
        
    identity.short_description = 'Number'
    identity.admin_order_field = 'connection__identity'


@admin.register(mwbase.PhoneCall)
class PhoneCallAdmin(admin.ModelAdmin, ParticipantAdminMixin):
    list_display = ('comment', 'participant_name', 'phone_number', 'outcome', 'is_outgoing', 'created')
    date_hierarchy = 'created'
    list_filter = ('outcome', 'is_outgoing')
    readonly_fields = ('created', 'modified')
    search_fields = ('participant__study_id', 'participant__nickname')


@admin.register(mwbase.Note)
class NoteAdmin(admin.ModelAdmin, ParticipantAdminMixin):
    list_display = ('participant_name', 'comment', 'created')
    date_hierarchy = 'created'


@admin.register(mwbase.Connection)
class ConnectionAdmin(admin.ModelAdmin, ParticipantAdminMixin):
    list_display = ('identity', 'participant_name', 'facility', 'is_primary')
    search_fields = ('participant__study_id', 'participant__nickname', 'identity')


@admin.register(mwbase.Visit)
class VisitAdmin(admin.ModelAdmin, ParticipantAdminMixin):
    list_display = ('study_id', 'participant_name', 'visit_type', 'scheduled',
                    'notification_last_seen', 'notify_count', 'arrived', 'status')
    date_hierarchy = 'scheduled'
    list_filter = ('status', 'visit_type', 'arrived', 'scheduled')
    search_fields = ('participant__study_id', 'participant__nickname')


@admin.register(mwbase.ScheduledPhoneCall)
class ScheduledPhoneCall(admin.ModelAdmin, ParticipantAdminMixin):
    list_display = ('study_id', 'participant_name', 'call_type', 'scheduled',
                    'notification_last_seen', 'notify_count', 'arrived', 'status')
    date_hierarchy = 'scheduled'
    list_filter = ('status', 'call_type', 'arrived', 'scheduled')
    search_fields = ('participant__study_id', 'participant__nickname')


@admin.register(mwbase.Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ('facility', 'username', 'password_changed')


@admin.register(mwbase.StatusChange)
class StatusChangeAdmin(admin.ModelAdmin, ParticipantAdminMixin):
    list_display = ('comment', 'participant_name', 'old', 'new', 'type', 'created')
    search_fields = ('participant__study_id', 'participant__nickname')


@admin.register(mwbase.EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'created')


class PractitionerInline(admin.TabularInline):
    model = mwbase.Practitioner


class UserAdmin(UserAdmin):
    inlines = (PractitionerInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(AutomatedMessage)
class AutomatedMessageAdmin(admin.ModelAdmin):
    list_display = ('description', 'english')
    list_filter = ('send_base', 'condition', 'group')
    change_list_template = "admin/mwbase/automatedmessage/change_list.html"
    smsbank_check_template = "admin/mwbase/automatedmessage/sms_bank_check.html"
    smsbank_import_template = "admin/mwbase/automatedmessage/sms_bank_import.html"
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['form'] = ImportXLSXForm
        return super(AutomatedMessageAdmin, self).changelist_view(request, extra_context=extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(r'smsbank_check_view/', self.admin_site.admin_view(self.smsbank_check_view), name='smsbank_check_view'),
            path(r'smsbank_import_view/', self.admin_site.admin_view(self.smsbank_import_view), name='smsbank_import_view'),
            path(r'smsbank_create_xlsx/', self.admin_site.admin_view(self.smsbank_create_xlsx), name='smsbank_create_xlsx')
        ]
        urls = my_urls + urls
        return urls
    
    def smsbank_create_xlsx(self, request, extra_context=None):
        wb = sms_bank.create_xlsx()
        response = HttpResponse(save_virtual_workbook(wb), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="smsbank.xlsx"'
        
        return response
    
    def smsbank_import_view(self, request, extra_context=None):
        opts = self.model._meta
        app_label = opts.app_label
        form = ImportXLSXForm(request.POST or None, request.FILES or None)
        counts, existing, diff= [], [], []
        error = ""
        
        if request.method == 'POST':
            if form.is_valid():
                file = form.cleaned_data.get("file")
                # try:
                counts, existing, diff= sms_bank.import_messages(file)
                # except Exception as e:
                #     print(e)
                #     error = "There was an error importing the given file.  Please try again."


            context = {
                **self.admin_site.each_context(request),
                'module_name': str(opts.verbose_name_plural),
                'opts': opts,
                'counts': counts,
                'existing': existing,
                'diff': diff,
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
        items = duplicates = descriptions = total = None
        form = ImportXLSXForm(request.POST or None, request.FILES or None)

        if request.method == 'POST':
            if form.is_valid():
                file = form.cleaned_data.get("file")
                (items, duplicates, descriptions, total ) = sms_bank.check_messages(file)
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
            **(extra_context or {}),
        }

        return TemplateResponse(request, self.smsbank_check_template or [
            'admin/%s/%s/sms_bank_check.html' % (app_label, opts.model_name),
            'admin/%s/sms_bank_check.html' % app_label,
            'admin/sms_bank_check.html'
        ], context)
