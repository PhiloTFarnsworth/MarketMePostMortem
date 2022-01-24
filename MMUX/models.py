from django.db import models
from django.contrib.auth.models import AbstractUser

import pytz

COMMON_TIMEZONETUPLE = []
for timezone in pytz.common_timezones:
    COMMON_TIMEZONETUPLE.append((timezone, timezone))


## We'll use the UX app to store our user model.
class User(AbstractUser):
    socialTool = models.BooleanField(default=False)
    mediaTool = models.BooleanField(default=False)
    serviceTool = models.BooleanField(default=False)
    defaultTZ = models.CharField(max_length=64, choices=COMMON_TIMEZONETUPLE)

## When a user 'follows' another, they will spawn a relationship, which allows
## access to the other users calendar.  At this point, the person followed
## will have access to a list of followers where they can assign the level
## of the relationship.  This relationship level will dictate what types of
## service the followed will offer, as well as calendar access, as we'll
## have different levels of availability for scheduling.  The idea here is
## that you may prefer screening clients to gauge their interest, so if you're
## offering a social service, like career counseling, you may not want to have
## your calendar filled with requests from users that may not follow up.
class Relationship(models.Model):
    level = models.IntegerField(default=0)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vendor")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client")

    ## We'll create a revoked field so that we can remember if a user has had their relationship
    ## revoked.  This will allow vendors to remove permissions from clients, to represent a
    ## dissolution of a business relationship
    revoked = models.BooleanField(default=False)

## To make our markdown a little more dynamic, we'll shoot for three designs that
## satisfy our mobile-friendly objective while also allowing for customization.
class Theme(models.Model):
    name = models.CharField(max_length=32)
    source = models.URLField()

class Profile(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)

    ## This might be a little tricky to implement, but I think we should be able
    ## to use sass to generate stylesheets based on their choice.  Biggest block
    ## is ensuring color contrast, but if built correctly, we multiply our output
    ## while building themes, so I think it worthwhile.
    primaryColor = models.CharField(max_length=10)
    markupContents = models.TextField(max_length=1024)
    location = models.CharField(max_length=128)
    publicContact = models.EmailField()
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, null=True, blank=True)
    image = models.URLField(blank=True, null=True)
