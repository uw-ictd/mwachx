
#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet
from contacts.models import Contact

class Connection(models.Model):

    class Meta:
        app_label = 'contacts'

    objects = BaseQuerySet.as_manager()

    TYPE_CHOICES = (
        ('phone','Phone Number'),
        ('email','Email'),
    )

    identity = models.CharField(max_length=25,primary_key=True)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)

    description = models.CharField(max_length=150,blank=True,null=True,help_text='Description of phone numbers relationship to contact')
    connection_type = models.CharField(max_length=10,help_text='Type of connection',choices=TYPE_CHOICES,default='phone')

    is_primary = models.BooleanField(default=False)

class Facility(models.Model):

    class Meta:
        verbose_name_plural = 'facilities'
        app_label = 'contacts'

    name = models.CharField(max_length='50',help_text='Facility Name')

    def __str__(self):
        # Change snake_case to Snake Case
        return ' '.join([word.capitalize() for word in self.name.split('_')])

class Practitioner(models.Model):
    '''
    User profile for nurse practitioners to link a User profile to a Facility
    '''
    class Meta:
        app_label = 'contacts'

    user = models.OneToOneField(User)
    facility = models.ForeignKey('contacts.Facility')

    @property
    def username(self):
        return self.user.username

    def __str__(self):
        return '<{0!s}> <{1}>'.format(self.facility,self.user.username)
