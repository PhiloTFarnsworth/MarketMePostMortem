from django.forms.widgets import EmailInput
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, reverse
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core import serializers

from .models import User, Relationship, Profile
from .forms import ProfileForm, LoginForm, RegisterForm, RelationshipManager, UserSettings
from MMcalendar.forms import ServiceForm, EventForm, AvailabilityForm
from MMcalendar.models import Calendar, Event, Service, AvailabilityRule
from MMsocial.models import Campaign, Post
from MMcalendar.util import customHTMLCalendar, AvailabilityArbiter


# Create your views here.

## this index route is going to be tricky, but I'd rather have users directed to their portals when
## logged in than have them take an extra step of going through an index page every time they load.
## While there are benefits to a community model, I would rather have the communities on other
# platforms so the attention stays on the person who refers the customer to the site.
def index(request):
    """Index view"""
    if request.user.is_authenticated:
        calendars = Calendar.objects.filter(owner=request.user).all()
        events = {}
        availability = {}
        pendingEvents = {}
        for calendar in calendars:
            query = Q(mainCalendar=calendar) | Q(attendee=calendar)
            events[calendar.name] = Event.objects.filter(query).exclude(
                status='TENTATIVE').exclude(
                    dtstart__lt=timezone.now()).all().order_by('dtstart')
            availability[calendar.name] = AvailabilityRule.objects.filter(calendar=calendar).all()
            pendingHost = Event.objects.filter(
                mainCalendar=calendar).exclude(
                    status='CONFIRMED').all().order_by('dtstart')
            pendingAttend = Event.objects.filter(
                attendee=calendar).exclude(
                    status='CONFIRMED').all().order_by('dtstart')
            pendingEvents[calendar.name] = pendingHost | pendingAttend
        
        ## Grab all relations that have passed beyond public.
        relationAsVendor = Relationship.objects.filter(
            vendor=request.user,
            level__gt=0).all()
        relationAsClient = Relationship.objects.filter(
            client=request.user,
            level__gt=0).all()
        relations = relationAsVendor | relationAsClient
        services = Service.objects.filter(organizer=request.user).all()
        campaigns = Campaign.objects.filter(owner=request.user).all()
        return render(request, "MMUX/index.html", {
            'calendars': calendars,
            'events': events,
            'availability': availability,
            'services': services,
            'campaigns': campaigns,
            'pendingEvents': pendingEvents,
            'relations': relations
        })
    else:
        form = RegisterForm()
        return render(request, "MMUX/index.html", {
            'form': form
        })

def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, "MMUX/login.html", {
                "message": "Invalid username and/or password.",
                "form": form
                })
    else:
        return render(request, "MMUX/login.html", {
            'form': form
        })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirm"]
        if password != confirmation:
            return render(request, "MMUX/register.html", {
            "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            return render(request, "MMUX/register.html", {
                "message": "Username already taken.",
                "form": RegisterForm()
            })

        ## add in our additional data
        user.first_name = request.POST["first_name"]
        user.last_name = request.POST["last_name"]


        ## wierd django functionality here, as they visualize checkboxes as on/off switches instead 
        ## of true/false.  So instead of simply assigning the value, we instead check whether the
        ## the POST data is omitted or not.  (Still, I find it funny that of all the things a vanilla
        ## django checkbox could return in a request, they settled on "on")
        if "socialTool" in request.POST:
            user.socialTool = True
        if "mediaTool" in request.POST:
            user.mediaTool = True
        if "serviceTool" in request.POST:
            user.serviceTool = True
        
        
        ## We register the user's timezone, saving it both to the User and to their session.
        user.defaultTZ = request.POST['defaultTZ']
        request.session['django_timezone'] = request.POST['defaultTZ']
        user.save()
        
        ## initialize a calendar for every user
        userCal = Calendar.objects.create(name=f"{user.first_name} {user.last_name}", owner=user)
        userCal.save()

        ## initialize a Profile for every user
        user_profile = Profile.objects.create(owner=user,
            primaryColor='#FFFFFF',
            markupContents='',
            location='',
            publicContact=email)
        user_profile.save()

        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "MMUX/register.html", {
            'form': RegisterForm()
        })

## Allow users to change what they have on their dashboard.
@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        if request.POST['first_name'] != '':
            user.first_name = request.POST['first_name']
        if request.POST['last_name'] != '':
            user.last_name = request.POST['last_name']
        if 'socialTool' in request.POST:
            user.socialTool = True
        else:
            user.socialTool = False
        if 'mediaTool' in request.POST:
            user.mediaTool = True
        else:
            user.socialTool = False
        if 'serviceTool' in request.POST:
            user.serviceTool = True
        else:
            user.serviceTool = False
        user.defaultTZ = request.POST['defaultTZ']
        request.session['django_timezone'] = request.POST['defaultTZ']
        user.save()
        return HttpResponseRedirect(reverse('index'))
    else:   
        form = UserSettings(initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'socialTool': user.socialTool,
            'mediaTool': user.mediaTool,
            'serviceTool': user.serviceTool,
            'defaultTZ': user.defaultTZ 
        })
        return render(request, "MMUX/settings.html", {
            'form': form
        })

@login_required
def profile_settings(request):
    user = request.user 
    this_profile = Profile.objects.get(owner=user)
    print(request.POST)
    print(this_profile.markupContents)
    if request.method == 'POST':
        this_profile.primaryColor = request.POST['primaryColor']
        this_profile.markupContents = request.POST['markupContents']
        this_profile.location = request.POST['location']
        this_profile.publicContact = request.POST['publicContact']
        this_profile.image = request.POST['image']
        this_profile.save()
        print(this_profile.markupContents)
        return HttpResponseRedirect(reverse('index'))
    else:
        form = ProfileForm(initial={
            'publicContact': this_profile.publicContact,
            'markupContents': this_profile.markupContents,
            'location': this_profile.location,
            'primaryColor': this_profile.primaryColor,
            'image': this_profile.image
        })
        return render(request, "MMUX/profile_settings.html", {
            'form': form
        })
## Users should have a landing page that they share that gives the requester some basic information about them
## and their services, as well as access to their calendar to schedule events (based on availability).  Logged 
## in users will additionally be able to click a button to introduce themselves, and raise their relationship
## level by one.  Doing so will unlock basic scheduling services, which can be upgraded at the vendor's discretion.
## We will want to also create some amount of personalization.  For the time being we'll likely reuse the markdown
## module to allow user formatting, while using some providing some options for theme and color (likely by designing
## layouts as 'themes' and using Sass's color functions to create several standard tonal variations).

def profile(request, username):
    thisUser = User.objects.get(username=username)
    thisProfile = Profile.objects.get(owner=thisUser)
    print(thisProfile.markupContents)
    return render(request, 'MMUX/profile.html', {
        'thisUser': thisUser,
        'Profile': thisProfile
    })

## We get the vendor of a relationship for free in this instance, since users will only navigate to here from the 
## relationship manager in their dashboard.  We'll pass the username of the client, grab that, change the relationship.
def relationUpgrade(request, username):
    client = User.objects.get(username=username)
    relation = Relationship.objects.get(vendor=request.user, client=client)
    relation.level = relation.level + 1
    relation.save()

    ## This could an area where we incorporate a fetch and simply update the relation area of our dashboard, for the
    ## time being we'll just reload the page.
    return HttpResponseRedirect(reverse('index'))

## Same soup as relationUpgrade.  We won't mess with the level since it's concievable relations can be resumed.
def relationRevoke(request, username):
    client = User.objects.get(username=username)
    relation = Relationship.objects.get(vendor=request.user, client=client)
    relation.revoked = True
    relation.save()
    return HttpResponseRedirect(reverse('index'))

## Restoring a revoked relationship
def relationRestore(request, username):
    client = User.objects.get(username=username)
    relation = Relationship.objects.get(vendor=request.user, client=client)
    relation.revoked = False
    relation.save()
    return HttpResponseRedirect(reverse('index'))

def fetchProfile(request, username):
    thisUser = User.objects.get(username=username)
    thisProfile = Profile.objects.get(owner=thisUser)
    return HttpResponse(thisProfile.markupContents)

def fetchServices(request, username):
    thisUser = User.objects.get(username=username)
    theirServices = serializers.serialize(
        'json',
        Service.objects.get(organizer=thisUser)
    )
    return HttpResponse(theirServices)
    
## A prime candidate for optimization, we're borrowing the calendar_view logic to generate our calendar for browsing users, while
## removing the rendering and instead passing only our html calendar.
def fetchCalendar(request, username):
    thisUser = User.objects.get(username=username)
    calendar = f"{thisUser.first_name} {thisUser.last_name}"
    thisCalendar = Calendar.objects.get(
        name=calendar,
        owner=thisUser)
    now = timezone.now()
    year = now.year
    month = now.month
    requestingCalendars = Calendar.objects.filter(owner=request.user).all()
    availability = AvailabilityRule.objects.filter(calendar=thisCalendar).all()
    if thisUser != request.user:
        combinedVisible = []
        combinedAnon = []
        for aCalendar in requestingCalendars:
            visibleHostedEvents = Event.objects.filter(
                mainCalendar=thisCalendar, 
                attendee=aCalendar, 
                dtstart__month=month).exclude(status='TENTATIVE').all()
            visibleAttendEvents = Event.objects.filter(
                mainCalendar=aCalendar, 
                attendee=thisCalendar, 
                dtstart__month=month).exclude(status='TENTATIVE').all()
            
            anonymousHostedEvents = Event.objects.filter(
                mainCalendar=thisCalendar, 
                dtstart__month=month).exclude(attendee=aCalendar).exclude(status='TENTATIVE').all()
            anonymousAttendEvents = Event.objects.filter(
                attendee=thisCalendar,
                dtstart__month=month).exclude(mainCalendar=aCalendar).exclude(status='TENTATIVE').all()

            combinedVisible.append((visibleAttendEvents | visibleHostedEvents).distinct())
            combinedAnon.append((anonymousAttendEvents | anonymousHostedEvents).distinct())
        
        anonymousEvents = Event.objects.none()
        visibleEvents = Event.objects.none()
        for i in range(len(combinedVisible)):
            anonymousEvents |= combinedAnon[i]
            visibleEvents |= combinedVisible[i]
    else:
        visibleHostEvents = Event.objects.filter(
            mainCalendar=thisCalendar, 
            dtstart__month=month).exclude(status='TENTATIVE').all()
        visibleAttendEvents = Event.objects.filter(
            attendee=thisCalendar, 
            dtstart__month=month).exclude(status='TENTATIVE').all()
        anonymousEvents = []
        visibleEvents = (visibleHostEvents | visibleAttendEvents).distinct()

    availRuleDict = AvailabilityArbiter(availability)
    eventDict = {}
    anonDict = {}  
    for x in range(1, 32):
        eventDict[x] = []
    for x in range(1, 32):
        anonDict[x] = []
    for event in visibleEvents:
        eventDict[event.dtstart.day].append(event)
    for event in anonymousEvents:
        anonDict[event.dtstart.day].append(event)
    graphicCal = customHTMLCalendar(year, month, eventDict, anonDict, availRuleDict, username, calendar)
    return HttpResponse(graphicCal)