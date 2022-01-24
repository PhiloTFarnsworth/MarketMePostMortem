from django import template
from datetime import time

## Translate our day codes.
DAYCHOICES = {
        'EVD': 'Everyday',
        'WDY': 'Weekdays',
        'WND': 'Weekends',
        'MON': 'Mondays',
        'TUE': 'Tuesdays',
        'WED': 'Wednesdays',
        'THU': 'Thursdays',
        'FRI': 'Fridays',
        'SAT': 'Saturdays',
        'SUN': 'Sundays' 
    }

register = template.Library()

## On loan from StackOverflow.

@register.filter(name='lookup')
def lookup(value, arg):
    return value[arg]

##{{ mydict|lookup:item.name }}

## We'll need to make one of these myself, to display duration
@register.filter(name='duration')
def duration(value):
    hours = int(value.seconds)/3600
    humanizedString = f'{hours} hours'
    return humanizedString

@register.filter(name='dayAbbr')
def dayAbbr(value):
    newValue = DAYCHOICES[value]
    return newValue