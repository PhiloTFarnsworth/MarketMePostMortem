from django.db import models
from uuid import uuid4
from MMUX.models import User
from MMcalendar.util import initStaticValue

# Create your models here.
class Calendar(models.Model):
    ## Seems pretty simple, we'll generate a default calendar on registration of an account,
    ## and give users the option to create additional calendars.  We can pass the name and
    ## lastModified information to the VCALENDAR header when we generate a ics file.
    name = models.CharField(max_length=64)
    lastModified = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

class EventCategory(models.Model):
    ## We could allow users to submit their own categories, but I think for this purpose
    ## nudging users towards our own predefined categories will help to keep activities
    ## like searching simple on both the developer and user end.
    name = models.CharField(max_length=64)

## We're going to have an inheritance model for accepted values for properties like
## tranps and status
class AcceptedValues(models.Model):
    value = models.CharField(max_length=32)

    @classmethod
    def create(cls, value):
        staticValue = cls(value=value)
        return staticValue

    class Meta:
        abstract = True

class StatusKeys(AcceptedValues):
    pass
## On one hand, we could add these using the Django Admin, but I feel if they change the values in
## a future RFC, changes to these keys should be left to a developer.
initStaticValue(StatusKeys, "TENTATIVE", "CONFIRMED", "CANCELLED")

class ClassKeys(AcceptedValues):
    pass

initStaticValue(ClassKeys, "PUBLIC", "PRIVATE", "CONFIDENTIAL")

## Users can define thier own services which we can use to pre-populate event queries.
class Service(models.Model):
    summary = models.CharField(max_length=64) 
    categories = models.ManyToManyField(EventCategory)
    description = models.TextField(max_length=512)
    organizer = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    duration = models.DurationField() 
    ## eventClass determines private/public events
    eventClass = models.ForeignKey(ClassKeys, on_delete=models.CASCADE)
    price = models.FloatField()

## we don't really need the Service's id field when it's being used
class Event(Service):
    ## We're going to make our event model as similar as possible to ICal 5455 spec, so we'll want to try to keep
    ## our properties as similar to those as possible
    uid = models.CharField(max_length=100, primary_key=True, unique=True, default=uuid4)
    created = models.DateTimeField(auto_now_add=True) ## time created
    lastModified = models.DateTimeField(auto_now=True) 
    dtstamp = lastModified ## This value is to be replaced when we construct the .ics with a method attached.
    sequence = models.IntegerField() ## number of edits
    ## Use Datetime to find any collisions between times provided
    dtstart = models.DateTimeField() ## start of event
    ##dtend = models.DateTimeField() ## ...
    ## attendees can be added by event host, and the host can allow people to +1 public events
    attendee = models.ManyToManyField(Calendar)
    ## URL is for representations of this event, so we'll use Location for links/whathaveyou
    location = models.CharField(max_length=128)
    ## confirmation will default to "tentative" when a participant makes a request, which should prompt
    ## some sort of message to the host for them to confirm the event.
    status = models.ForeignKey(StatusKeys, on_delete=models.CASCADE)
    ## TRANSP is more of a speculative class at the moment, I wouldn't want users to double book time.
    transp = models.CharField(default="OPAQUE") ## can easily swap out with TRANSPKEYS class

