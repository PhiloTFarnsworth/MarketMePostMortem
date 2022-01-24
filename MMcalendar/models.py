from django.db import models
from uuid import uuid4
from MMUX.models import User
from MMcalendar.util import initStaticValue

from datetime import timedelta, datetime

## Relationship Levels at this moment.  public events and public time are
## displayed to anyone, the following button makes the introduction, then
## clients graduate, at the calendar owner's discretion, to seeing relationship
## and priority relationship reserved time.
RELCHOICES = [
        (0, 'Public'),
        (1, 'Introduction'), ## Calendar owner is followed
        (2, 'Relationship'), ## Calendar owner solidifies relationship
        (3, 'Priority Relationship') ## top priority clients, full calendar/service access
        ]

class CalendarManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(owner=name)
# Create your models here.
class Calendar(models.Model):

    ## Seems pretty simple, we'll generate a default calendar on registration of an account,
    ## and give users the option to create additional calendars.  We can pass the name and
    ## lastModified information to the VCALENDAR header when we generate a ics file.
    name = models.CharField(max_length=128)
    lastModified = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['name', 'owner']

##EventCategory is another meh feature.  While we can hook it up and have an extra facet
## of searchability of our calendar objects, it's not really worth while to implement at
## this time as the nature of our calendars are mostly private.  More of an interesting
## feature for public calendars where you would want to use metadeta to get more eyes on it.

##class EventCategory(models.Model):
    ## We could allow users to submit their own categories, but I think for this purpose
    ## nudging users towards our own predefined categories will help to keep activities
    ## like searching simple on both the developer and user end.
    ##name = models.CharField(max_length=64)

    ##def __str__(self):
    ##    return f'{self.name}'

## baseEvent feeds to both services and events.  While I had considered making services take a user
## as the originator of the event, we simplify the logic (as well as create more customization for
## individual calendars) if we keep services and events as similar as possible.
class baseEvent(models.Model):
    summary = models.CharField(max_length=64) 
    ##categories = models.ManyToManyField(EventCategory)
    description = models.TextField(max_length=512)
    duration = models.DurationField() 
    ## eventClass determines private/public events
    CLASSKEYS = [
        ("PUBLIC", "PUBLIC"), 
        ("PRIVATE", "PRIVATE"), 
        ("CONFIDENTIAL", "CONFIDENTIAL")
    ]
    eventClass = models.CharField(max_length=16, choices=CLASSKEYS, default="PRIVATE")
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    class Meta:
        abstract = True

## Users can define thier own services which we can use to pre-populate event queries.
class Service(baseEvent):
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    
    ## used to determine which services are rendered
    relationRequired = models.IntegerField(choices=RELCHOICES, default=3)

class Event(baseEvent):
    ## We pass our events based on calendar, so we'll take calendars for the Organizer as well as Attendees
    mainCalendar = models.ForeignKey(Calendar, on_delete=models.CASCADE, related_name="Organizer")
    ## We're going to make our event model as similar as possible to ICal 5455 spec, so we'll want to try to keep
    ## our properties as similar to those as possible
    uid = models.CharField(max_length=100, primary_key=True, unique=True, default=uuid4)
    created = models.DateTimeField(auto_now_add=True) ## time created
    lastModified = models.DateTimeField(auto_now=True) 
    sequence = models.IntegerField(default=0) ## number of edits
    ## Use Datetime to find any collisions between times provided
    dtstart = models.DateTimeField() ## start of event
    dtend = models.DateTimeField(blank=True, null=True)    
    ## attendees can be added by event host, and the host can allow people to +1 public events
    attendee = models.ManyToManyField(Calendar, related_name="Attendees", blank=True)
    ## URL is for representations of this event, so we'll use Location for links/whathaveyou
    location = models.CharField(max_length=128, blank=True)
    ## confirmation will default to "tentative" when a participant makes a request, which should prompt
    ## some sort of message to the host for them to confirm the event.
    STATUSKEYS = [
        ('TENTATIVE','TENTATIVE'), 
        ('CONFIRMED','CONFIRMED'),
        ('CANCELLED', 'CANCELLED')
    ]
    status = models.CharField(max_length=16, choices=STATUSKEYS, default='TENTATIVE')
    ## TRANSP is more of a speculative class at the moment, I wouldn't want users to double book time.
    transp = models.CharField(max_length=16, default="OPAQUE") ## can easily swap out with TRANSPKEYS class

    def save(self, *args, **kwargs):
        ##Update the blank dtend to the end of the event
        self.dtend = self.dtstart + self.duration
        super().save(*args, **kwargs)

    ## TRANSP may play a role in this later, but to my mind any confirmed a event should own a start time.  Our client side handles
    ## a fair bit of restricting event creation to unoccupied time, but server side restrictions are prudent as well.
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['dtstart'], condition=models.Q(status='CONFIRMED'), name='unique_confirmed_event')
        ]

class AvailabilityRule(models.Model):
    ## So, for availability we want users to specify when they are available to when they aren't.  We
    ## also want to classify 4 tiers of time availability, which match our relationship tiers.  
    name = models.CharField(max_length=64)
    begin = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    unavailable = models.BooleanField(default=True)
    relationship = models.IntegerField(choices=RELCHOICES, default=0) ## Enable this for availability later
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    ## When we parse these choices, the more specific the choice, the higher the precedence. So if
    ## a user has 3 availability rules like Everyday:9-5, Weekends:10-2, Sunday: no time, then 
    ## Saturdays are 10-2, sundays are no time.
    DAYCHOICES = [
        ('EVD', 'Everyday'),
        ('WDY', 'Weekdays'),
        ('WND', 'Weekends'),
        ('MON', 'Mondays'),
        ('TUE', 'Tuesdays'),
        ('WED', 'Wednesdays'),
        ('THU', 'Thursdays'),
        ('FRI', 'Fridays'),
        ('SAT', 'Saturdays'),
        ('SUN', 'Sundays') 
    ]
    scope = models.CharField(max_length=3, choices=DAYCHOICES, default='EVD')
    ## Is this rule being applied, or just a saved preset?
    active = models.BooleanField(default=True)

## Ideally, we would have the user create a rule, then they can see it overlaid on a week
## table.  If they have multiple active, the overlay will morph to reflect that.  Besides
## the scope inheritance, we'll also have inheritance based on relationship.  So public
## availability -> ... -> Priority relationship.  Big question is whether we sequester each
## level of relationship in their own tab on the edit screen, or perhaps we color code our
## relationship availabilities to show all the info on one calendar page.