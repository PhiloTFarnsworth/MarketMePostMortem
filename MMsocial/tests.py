from django.test import TestCase
from MMUX.models import User
from .models import Post, Campaign, CampaignSequence
from datetime import timedelta

# Create your tests here.
class MMSocialTestCase(TestCase):
    def setUp(self):
        Jon = User.objects.create_user("Jon", "BigD@email.com", "Jonpass")
        Garfield = User.objects.create_user("Garfield", "Mondaze@email.com", "Lasagne")
        p1 = Post.objects.create(meat="You milquetoast!", owner=Garfield)
        p2 = Post.objects.create(meat="I want my enchiladas", owner=Garfield)
        p3 = Post.objects.create(meat="That's pretty mean, Garfield", owner=Jon)
        p4 = Post.objects.create(meat="I don't know, Garfield", owner=Jon)
        cGar = Campaign.objects.create(name="GarExample", owner=Garfield)
        cDav = Campaign.objects.create(name="JonExample", owner=Jon)
        CampaignSequence.objects.create(post=p2, campaign=cGar, order=0)
        CampaignSequence.objects.create(post=p1, campaign=cGar, order=1)
        CampaignSequence.objects.create(post=p4, campaign=cDav, order=0)
        CampaignSequence.objects.create(post=p3, campaign=cDav, order=1)
        ##cGar.postQueue.add(post=p2, campaign=cGar, order=0)
        ##cGar.postQueue.add(cs2)
        ##cDav.postQueue.add(cs4)
        ##cDav.postQueue.add(cs3)

    def test_PostModel(self):
        Jon = User.objects.get(username="Jon")
        Garfield = User.objects.get(username="Garfield")
        p = Post.objects.get(meat="You milquetoast!")
        self.assertEqual(p.owner, Garfield)
        Jons = Post.objects.filter(owner=Jon).all()
        self.assertEqual(2, len(Jons))
        self.assertEqual("That's pretty mean, Garfield", Jons[0].meat)
        for x in Jons:
            self.assertFalse(x.owner == Garfield)
    
    def test_CampaignModel(self):
        Jon = User.objects.get(username="Jon")
        Garfield = User.objects.get(username="Garfield")
        cJon = Campaign.objects.get(owner=Jon)
        cGarf = Campaign.objects.get(owner=Garfield)
        self.assertEqual(2, cJon.postQueue.count())
        garfposts = cGarf.postQueue.all()
        self.assertEqual("I want my enchiladas", garfposts[0].meat)
        self.assertEqual(timedelta(days=1), cGarf.interval)
