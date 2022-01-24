from django.test import TestCase
from .models import Calendar, Event, Service, AvailabilityRule
from MMUX.models import User, Relationship
from datetime import timedelta, datetime, tzinfo, timezone
# Create your tests here.

class MMcalendarTestCase(TestCase):
    def setUp(self):
        Jon = User.objects.create_user("Jon", "Johnnyboy@email.com", "Jonpass")
        Garfield = User.objects.create_user("Garfield", "Mondaze@email.com", "Lasagne")
        Oodie = User.objects.create_user("Oodie", "dog@dog.com", "password")
        ## I just spent several minutes considering what access level a cartoon cat would
        ## have with a cartoon dog.  Poor Jon.
        JonGarfieldRel = Relationship.objects.create(level=3, vendor=Jon, client=Garfield)
        GarfieldJonRel = Relationship.objects.create(level=1, vendor=Garfield, client=Jon)
        OodieJonRel = Relationship.objects.create(level=3, vendor=Oodie, client=Jon)
        JonOodieRel = Relationship.objects.create(level=2, vendor=Jon, client=Oodie)
        GarfieldOodieRel = Relationship.objects.create(level=0, vendor=Garfield, client=Oodie)
        OodieGarfieldRel = Relationship.objects.create(level=1, vendor=Oodie, client=Garfield)
        
        GarCalendar = Calendar.objects.create(name="Garfield's Calendar", owner=Garfield)
        JonCalendar = Calendar.objects.create(name="Jon's Calendar", owner=Jon)
        OodieCalendar = Calendar.objects.create(name="Oodie's Calendar", owner=Oodie)
        
        
        LasagneService = Service.objects.create(
            summary="Make Lasagne", 
            description="Will make lasagne",
            organizer=Jon,
            duration=timedelta(hours=3),
            eventClass="PRIVATE",
            price=15.00,
            relationRequired=3
        )
        CruelBarb = Service.objects.create(
            summary="Make Cruel Barbs",
            description="Some quips about how Jon is so lame he talks to a cat",
            organizer=Garfield,
            duration=timedelta(minutes=15),
            eventClass="PRIVATE",
            price=0.00,
            relationRequired=1
        )
        BeADog = Service.objects.create(
            summary="Do Dog Things",
            description="Just general dog stuff",
            organizer=Oodie,
            duration=timedelta(hours=1, minutes=30),
            eventClass="PUBLIC",
            price=1.00,
            relationRequired=0
        )
        

        JonFridayNight = Event.objects.create(
            summary="Weeping",
            description="Weep in the shower, then talk to a cat",
            mainCalendar=JonCalendar,
            duration=timedelta(hours=1,minutes=15),
            eventClass="PRIVATE",
            status="CONFIRMED",
            price=0.00,
            dtstart=datetime(year=2020,month=9,day=4,hour=19,minute=30, tzinfo=timezone.utc),
            location="My House"
        )
        JonFridayNight.attendee.add(GarCalendar) 

    def test_Calendar_Object(self):
        Jon = User.objects.get(username="Jon")
        Garfield = User.objects.get(username="Garfield")
        Oodie = User.objects.get(username="Oodie")
        jonCal = Calendar.objects.filter(owner=Jon).get(name="Jon's Calendar")
        jonHostedEvents = Event.objects.filter(mainCalendar=jonCal).all()
        self.assertEqual(1, len(jonHostedEvents))
        self.assertEqual("Weeping", jonHostedEvents[0].summary)