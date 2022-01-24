from django.db import models
from MMUX.models import User
from datetime import timedelta
## for this area, what we really want to have is a system where a user can
## build a marketing campaign in their down time.  So instead of spending 
## 30 minutes a day navigating social networks and potentially getting distracted
## they can create a couple posts, put them on a queue and they'll be posted over
## the next couple of days over social media.  The user should be easily able to
## add/remove posts, rearrange how often they want automatic posts to go out and 
## at what time.

## so we start with our base unit, a post.
class Post(models.Model):
    meat = models.TextField(max_length=280)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    ## For both space and privacy concerns, I think we should have a policy of
    ## deleting inactive Posts (not hosted on a Post Queue) after a certain amount
    ## of time.  Either way, this can help users sort through these to put together
    ## new queues, even if we keep posts forever.
    active = models.BooleanField(default=False)

## Now for the mothership, Post queues which we'll call campaigns.  They need
## to have a user recognizable name, and they have to contain references to 
## all the posts.  Most Importantly, they need a mechanism for being sorted by
## the user.  If User wants Post #3 to be posted before Post #1, then we have a 
## problem just using a vanilla Django model. 
class Campaign(models.Model):
    name = models.CharField(max_length=64)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    postQueue = models.ManyToManyField(
        Post,
        through='CampaignSequence',
        blank=True
        )
    interval = models.DurationField(default=timedelta(days=1))

class CampaignSequence(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    order = models.PositiveIntegerField() 

    class Meta:
        unique_together = (('post', 'campaign'))
        ordering = ['order']