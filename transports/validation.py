import re

from .validators import KeywordValidator, Validator

# Arrary of validator actions
validators = []

########################################
# Define Validators
########################################

#############
stop_validator = KeywordValidator('stop')
validators.append(stop_validator)


@stop_validator.set('action')
def validator_action(message):
    print('STOP messaging for {}'.format(message.participant))
    message.participant.set_status('stopped', 'Participant sent stop keyword')
    message.text += ' - participant withdrew'
    message.participant.send_automated_message(
        send_base='stop',
        send_offset=0,
        group='one-way',
        hiv_messaging=False,
        control=True
    )
    return False


###############
validation_validator = Validator('validation')
validators.append(validation_validator)


@validation_validator.set('check')
def validator_action(message):
    if re.match('^\d{5}$', message.text) and not message.participant.is_validated:
        message.topic = 'validation'
        message.is_related = True
        message.is_viewed = True
        if message.participant.validation_key == message.text.strip():
            message.text = 'Validation Code Correct: ' + message.text
            return True
        else:
            message.text = 'Validation Code Incorrect: ' + message.text
            return False
    return False


@validation_validator.set('action')
def validator_action(message):
    message.participant.is_validated = True
    message.contparticipant.save()
    return False  # Don't continue validation check  s


###############
study_group_validator = Validator('study_group')
validators.append(study_group_validator)


@study_group_validator.set('check')
def validator_action(message):
    if message.participant.study_group in ('one-way', 'control'):
        message.text = "WARNGING: {} {}".format(message.participant.study_group.upper(), message.text)
        message.is_viewed = True
        return True
    return False


@study_group_validator.set('action')
def validator_action(message):
    # Send participant bounce message
    message.participant.send_automated_message(send_base='bounce', send_offset=0, hiv_messaging=False, control=True)
