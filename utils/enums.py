GROUP_CHOICES = (
    ('control', 'Control'),
    ('one-way', 'One Way'),
    ('two-way', 'Two Way'),
)

FACILITY_CHOICES = (
    ('mathare', 'Mathare'),
    ('bondo', 'Bondo'),
    ('ahero', 'Ahero'),
    ('siaya', 'Siaya'),
    ('rachuonyo', 'Rachuonyo'),
    ('riruta', 'Riruta'),
)


NO_SMS_STATUS = ('stopped', 'other', 'sae', 'quit')
NOT_ACTIVE_STATUS = NO_SMS_STATUS + ('completed',)
