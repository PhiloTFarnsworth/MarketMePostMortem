from django.shortcuts import render, HttpResponse, HttpResponseRedirect, reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail

from .MMiCAL import MMiCal, classes
from .util import customHTMLCalendar, AvailabilityArbiter, eventCleaner, dayPlannerScaffold, applySchedule
from .models import Service, Calendar, Event, AvailabilityRule
from .forms import ServiceForm, AvailabilityForm
from MMUX.models import User, Relationship

from datetime import timedelta, datetime, time, date
from datetime import timezone as DTTZ
import pytz
import os

PYTHON_WEEKDAYS = {
    0: 'MON',
    1: 'TUE',
    2: 'WED',
    3: 'THU',
    4: 'FRI',
    5: 'SAT',
    6: 'SUN'
}
# Create your views here.

## We're going to keep views in their apps, while our MMUX urls file will be the master controller
## of all our routes.
@login_required
def create_service(request):
    if request.method == 'POST':
        timeVal = request.POST['duration'].split(':')
        duration = timedelta(minutes=int(timeVal[1]), hours=int(timeVal[0]))
        newService = Service.objects.create(
            summary=request.POST['summary'],
            description=request.POST['description'],
            duration=duration,
            eventClass="PRIVATE", ## Can't charge for public events, who knows what's up with confidential.
            price=request.POST['price'],
            relationRequired=request.POST['relationRequired'],
            organizer=request.user
        )
        ## this needs to return to a detail page of the service, which allows users to confirm all the info
        ## provided.  I think we lead to a services detail page, which lists all the services, likely in order
        ## of creation with the newest first.  Note: I would like to give users the ability to control the order
        ## in which services appear on their own profiles, but I think for the detail view our default works.
        newService.save()
        return HttpResponseRedirect(reverse('my services'))
    else:
        form = ServiceForm()
        
        return render(request, "MMUX/create.html", {
            'form': form,
            'formTitle': 'Create Service',
            'formAddress': '/user/createService'
        })

@login_required
def myServices(request):
    ## just a get page that fetches the user's services
    services = Service.objects.filter(organizer=request.user).all().order_by('id')
    return render(request, "MMcalendar/services.html", {
        'services':services
    })

## Our monthly calendar view.  By default, we'll direct the user to this month, and we'll grab all their events,
## see which are a part of this month, then pass it to a custom HTMLcalendar based on the python HTMLCalendar 
## with edits using BeautifulSoup4.
def calendar_view(request, username, calendar, year=0, month=0):
    now = timezone.now()
    if year == 0:
        year = now.year
    if month == 0:
        month = now.month
    thisUser = User.objects.get(username=username)
    thisCalendar = Calendar.objects.filter(owner=thisUser).get(name=calendar)
    if request.user.id != None:
        requestingCalendars = Calendar.objects.filter(owner=request.user).all()
    else:
        requestingCalendars = []
    availability = AvailabilityRule.objects.filter(calendar=thisCalendar).all()
    if thisUser != request.user:
        ## We need to pull both visible events and events the user won't see.  For the events the user won't see we
        ## just want to reserve those blocks of time, and for the visible events we want to indicate that there are
        ## events whose data you can browse
        combinedVisible = []
        combinedAnon = []
        for aCalendar in requestingCalendars:
            visibleHostedEvents = Event.objects.filter(mainCalendar=thisCalendar, attendee=aCalendar, dtstart__month=month).exclude(status='TENTATIVE').all()
            visibleAttendEvents = Event.objects.filter(mainCalendar=aCalendar, attendee=thisCalendar, dtstart__month=month).exclude(status='TENTATIVE').all()
            
            anonymousHostedEvents = Event.objects.filter(mainCalendar=thisCalendar, dtstart__month=month).exclude(attendee=aCalendar).exclude(status='TENTATIVE').all()
            anonymousAttendEvents = Event.objects.filter(attendee=thisCalendar,dtstart__month=month).exclude(mainCalendar=aCalendar).exclude(status='TENTATIVE').all()

            combinedVisible.append((visibleAttendEvents | visibleHostedEvents).distinct())
            combinedAnon.append((anonymousAttendEvents | anonymousHostedEvents).distinct())
        
        anonymousEvents = Event.objects.none()
        visibleEvents = Event.objects.none()
        for i in range(len(combinedVisible)):
            anonymousEvents |= combinedAnon[i]
            visibleEvents |= combinedVisible[i]
    else:
        visibleHostEvents = Event.objects.filter(mainCalendar=thisCalendar, dtstart__month=month).exclude(status='TENTATIVE').all()
        visibleAttendEvents = Event.objects.filter(attendee=thisCalendar, dtstart__month=month).exclude(status='TENTATIVE').all()
        anonymousEvents = []
        visibleEvents = (visibleHostEvents | visibleAttendEvents).distinct()

    availRuleDict = AvailabilityArbiter(availability)
    ## We're going to store the events per day
    eventDict = {}
    anonDict = {}
    ## 31 days max, don't see any reason to taylor it specifically to the # of days in any
    ## given month.  
    for x in range(1, 32):
        eventDict[x] = []
    for x in range(1, 32):
        anonDict[x] = []
    for event in visibleEvents:
        eventDict[event.dtstart.day].append(event)
    for event in anonymousEvents:
        anonDict[event.dtstart.day].append(event)
    
    ## With our eventDict prepared, we can feed it and our availRuleDict into our customHTMLCalendar
    graphicCal = customHTMLCalendar(year, month, eventDict, anonDict, availRuleDict, username, calendar)
    
    ## TODO: JSONIFY the eventDict and create SPA calendar.  For now, we'll have a monthview and
    ## day view.
   
    return render(request, 'MMcalendar/calendar.html', {
        'calendar': graphicCal,
        'thisUser': thisUser,
        'thisCalendar': calendar,
        'theDate': date(year, month, 1)
    })

def multiCalendar_view(request, username):
    thisUser = User.objects.get(username=username)
    calendars = Calendar.objects.filter(owner=thisUser).all()
    return render(request, "MMcalendar/myCalendars.html", {
        'calendars': calendars,
        'thisUser': thisUser
    })

def dayDetails(request, username, calendar, year, month, day):
    ## We'll start with the planner side of the render, grabbing all pertinent information for our calendar
    thisUser = User.objects.get(username=username)
    thisCalendar = Calendar.objects.filter(owner=thisUser).get(name=calendar)
    userCalendars = Calendar.objects.filter(owner=request.user).all()
    availability = AvailabilityRule.objects.filter(calendar=thisCalendar).all()
    if request.user == thisUser:
        daysEventsOwner = Event.objects.filter(Q(mainCalendar=thisCalendar, dtstart__year=year, dtstart__month=month, dtstart__day=day)).exclude(status='TENTATIVE').all()
        daysEventsAttend = Event.objects.filter(Q(attendee=thisCalendar, dtstart__year=year, dtstart__month=month, dtstart__day=day)).exclude(status='TENTATIVE').all()
        daysEvents = daysEventsOwner | daysEventsAttend
        relation = -1
        anonDaysEvents = []
    else:

        ## try to find a relation, otherwise create one at public access.
        try:
            relation = Relationship.objects.get(vendor=thisUser, client=request.user)
        except:
            relation = Relationship.objects.create(level=0, vendor=thisUser, client=request.user)
            relation.save()

        ## check all of the requesting user's calendars to see if they attend this user's calendar
        query = Q()
        for calendar in userCalendars:
            query |= Q(attendee=calendar)
        ## Get events hosted on calendar that are not attended by request user.  Note: we only need dtstart, dtend for
        ## anonymous events  
        anonymousHostedEvents = Event.objects.filter(Q(mainCalendar=thisCalendar, dtstart__year=year, dtstart__month=month, dtstart__day=day)).exclude(status='TENTATIVE').exclude(query).all()
        ## all the visible events hosted on this calendar
        visibleQuery = Q(mainCalendar=thisCalendar, dtstart__year=year, dtstart__month=month, dtstart__day=day) & query
        hostedEvents = Event.objects.filter(visibleQuery).exclude(status='TENTATIVE').all()
        
        ## Also should get all events the calendar is subscribed to, as well.
        mainQuery = Q()
        for calendar in userCalendars:
            mainQuery |= Q(mainCalendar=calendar)
        anonymousSubscribedEvents = Event.objects.filter(Q(dtstart__year=year, dtstart__month=month, dtstart__day=day, attendee=thisCalendar)).exclude(status='TENTATIVE').exclude(mainQuery).all()
        subscribedQuery = Q(dtstart__year=year, dtstart__month=month, dtstart__day=day, attendee=thisCalendar) & query
        subscribedEvents = Event.objects.filter(subscribedQuery).exclude(status='TENTATIVE').all()
        
        ## Finally, we'll smush our querysets together, but since we're having all sorts of troubles with
        ## limiting our query sets, we have to pass them all.  TODO: Refine this. 
        anonDaysEvents = anonymousHostedEvents | anonymousSubscribedEvents 
        daysEvents = hostedEvents | subscribedEvents

    ## build an HTML scaffold
    ourDate = date(year=year, month=month, day=day)
    planner = dayPlannerScaffold(ourDate)
    ## Get a single day's rule
    weekdayCode = ourDate.weekday()
    previousDayCode = weekdayCode - 1
    weekDay = PYTHON_WEEKDAYS[weekdayCode]
    availabilityDict = AvailabilityArbiter(availability)
    ourRules = []
    ## sandwich our main rule in a list between adjacent days
    if weekdayCode == 0:
        ourRules.append(availabilityDict[PYTHON_WEEKDAYS[6]])
        ourRules.append(availabilityDict[weekDay])
    else:
        ourRules.append(availabilityDict[PYTHON_WEEKDAYS[previousDayCode]])
        ourRules.append(availabilityDict[weekDay])


    ## insert our data and mess around.
    formattedPlanner = applySchedule(planner, ourRules, daysEvents, anonDaysEvents, ourDate)

    ## We also need to grab the owner's Services to display them in a drop down, for visiting users, we
    ## grab all services at and below their relation required level.
    query = Q(organizer=thisUser)
    if relation != -1:
        for x in range(relation.level, -1, -1):
            thisQuery = Q(relationRequired=x) & query
        services = Service.objects.filter(thisQuery).all()
    else:
        services = Service.objects.filter(organizer=thisUser).all()

    ## Simplest way to find out how many days the previous month have is just to send a 
    ## generic datetime, then use django's template strings to render.  3rd day of the month to avoid any
    ## timezone insanity
    if month != 1:
        previousMonth = datetime(year=year,month=month-1,day=3,hour=0)
    else:
        previousMonth = datetime(year=year-1, month=12, day=3, hour=0)

    ## This is not the best way to pass whether we will go past the end of the month.
    endofMonth = False
    try:
        datetime(year=year,month=month,day=day+1)
    except:
        endofMonth = True

    return render(request, "MMcalendar/dayPlanner.html",{
        'planner': formattedPlanner,
        'services': services,
        'date': ourDate,
        'owner': thisUser,
        'calendar': thisCalendar,
        'previousMonth': previousMonth,
        'endofMonth': endofMonth
    })

def bookEvent(request, username, calendar, year, month, day):
    serviceName = request.POST['services']
    rawDtstart = request.POST['dtstart']
    description = request.POST['description']
    rawDuration = request.POST['duration']
    price = request.POST['price']

    thisUser = User.objects.get(username=username)
    thisCalendar = Calendar.objects.filter(owner=thisUser).get(name=calendar)
    requestingCalendar = Calendar.objects.get(owner=request.user)

    ## parse out the start time
    splitDtstart = rawDtstart.split('-')
    hour = int(splitDtstart[0])
    splitagain = splitDtstart[1].split('_')
    minute = int(splitagain[0])
    if splitagain[1] == 'pm':
        if hour != 12:
            hour = hour + 12
    else:
        if hour == 12:
            hour = hour - 12

    dtstart = timezone.make_aware(datetime(year=year, month=month, day=day, hour=hour, minute=minute))
    ## duration is passed as minutes.
    duration = timedelta(minutes=int(rawDuration))
    newEvent = Event.objects.create(
        summary=serviceName, 
        description=description, 
        duration=duration, 
        price=price, 
        mainCalendar=thisCalendar, 
        dtstart=dtstart
        )
    newEvent.attendee.set([requestingCalendar])
    newEvent.save()

    ## Send emails
    ## One to the owner of the calendar to confirm the appointment
    send_mail(
        f'{request.user.username} wants to schedule a {serviceName} with you!',
        f'{request.user.username} scheduled {serviceName} on {dtstart}.  Please click http://127.0.0.1:8000/user/confirm/{newEvent.uid}',
        'Donotreply@MarketMe.com',
        [f'{thisUser.email}'],
        fail_silently=False
    )
    ## One to the requester.
    send_mail(
        f'{serviceName} request sent to {thisUser.username}',
        f"Awaiting {thisUser.username}'s confirmation on {serviceName}.",
        'Donotreply@MarketMe.com',
        [f'{request.user.email}'],
        fail_silently=False 
    )
    return HttpResponseRedirect(reverse('day details', kwargs={'username':username, 'calendar':calendar, 'year':year, 'month':month, 'day':day}))

def confirmEvent(request, uid):
    thisEvent = Event.objects.get(uid=uid)
    requestingCalendars = Calendar.objects.filter(owner=request.user).all()
    authorized = False
    for calendar in requestingCalendars:
        if thisEvent.mainCalendar == calendar:
            authorized = True

    mailSet = set()
    for attendee in thisEvent.attendee.all():
        attendingUser = User.objects.get(username=attendee.owner.username)
        mailSet.add(attendingUser.email)
    mailSet.add(f'{request.user.email}')
    mailList = list(mailSet)
    ## our Unique constraint on start time should reject an event being confirmed at the same time
    ## slot as one already existing, so if we fails this we should inform the user that the event
    ## is already booked.
    try:
        if authorized == True:
            thisEvent.status = "CONFIRMED"
            thisEvent.save()
            send_mail(
                f'{thisEvent.summary} on {thisEvent.dtstart} has been confirmed',
                f'{request.user.username} has confirmed this event',
                'Donotreply@MarketMe.com',
                mailList,
                fail_silently=False
            )
            return HttpResponseRedirect(reverse('index'))
        else:
            return HttpResponse('You are not authorized to confirm this event')
    except:
        return HttpResponse('Error occurred, Event start is already occupied by a confirmed event')

## export calendar to .ics
def exportCalendar(request, username, calendar):
    ## Get calendar and all events, put them into dictionary form to iterate them into a MMiCal object
    thisCalendar = Calendar.objects.get(name=calendar, owner=request.user)
    hostedEvents = Event.objects.filter(mainCalendar=thisCalendar)
    attendingEvents = Event.objects.filter(attendee=thisCalendar)
    combinedEvents = hostedEvents | attendingEvents
    allEvents = combinedEvents.distinct().values()
    
    ## we need a calendar list (we've been designing with multiple calendars in mind, though some parts
    ## of the implementation are beyond the scope of this project)
    calendarList = []
    MMCalendar = classes.Calendar()
    ## PRODID:-//Google Inc//Google Calendar 70.9054//EN
    ##VERSION:2.0
    ##CALSCALE:GREGORIAN
    ##METHOD:PUBLISH
    MMCalendar.properties.append(classes.Property('VERSION', '2.0'))
    MMCalendar.properties.append(classes.Property('PRODID', '-//MARKETME/MARKETMECALENDAR 0.1//EN'))
    MMCalendar.properties.append(classes.Property('CALSCALE', 'GREGORIAN'))
    ##We're skipping adding timezone information because we should have everything timestamped to UTC

    ##Finally, we've got to read the events, then add them to calendar
    specialKeys = ['mainCalendar_id', 'attendee_id', 'lastModified', 'price', 'eventClass', 'duration', 'dtstart', 'dtend', 'created']
    for event in allEvents:
        icsEvent = classes.Event()
        attendees = []
        for key, value in event.items():
            stringValue = str(value)
            stringKey = key.upper()
            if key not in specialKeys:
                icsProp = classes.Property(stringKey, stringValue)
                icsEvent.properties.append(icsProp)
            else:
                if stringKey == 'MAINCALENDAR_ID':
                    userInfo = User.objects.get(id=int(stringValue))
                    icsProp = classes.Property('ORGANIZER', 'mailto:' + userInfo.email, ['CUTYPE=INDIVIDUAL', f'CN={userInfo.email}'])
                    icsEvent.properties.append(icsProp)
                elif stringKey == 'ATTENDEE_ID':
                    userInfo = User.objects.get(id=int(stringValue))
                    icsProp = classes.Property('ATTENDEE', 'mailto:' + userinfo.email, ['CUTYPE=INDIVIDUAL', 'ROLE=REQ-PARTICIPANT'])
                    icsEvent.properties.append(icsProp)
                elif stringKey == 'LASTMODIFIED':
                    convertedTime = value.astimezone(DTTZ.utc)
                    timeValue = convertedTime.strftime('%Y%m%dT%H%M%S')
                    icsProp = classes.Property('LAST-MODIFIED', timeValue)
                    icsEvent.properties.append(icsProp)
                elif stringKey == 'EVENTCLASS':
                    icsProp = classes.Property('CLASS', stringValue)
                    icsEvent.properties.append(icsProp)
                elif stringKey == 'DTSTART' or stringKey == 'DTEND' or stringKey == 'CREATED':
                    ## Unfortunately, Timezones have foiled me in this instance.  We can pass this as a niave time
                    ## and hopefully, django doesn't disagree with the user's computer on what timezone is this.
                    ## We'll add another part of timezone functionality to a stretch goal.
                    convertedTime = value.astimezone(DTTZ.utc)
                    timeValue = convertedTime.strftime('%Y%m%dT%H%M%S')
                    icsProp = classes.Property(stringKey, timeValue)
                    icsEvent.properties.append(icsProp)
                else:
                    pass
        now = datetime.now()
        icsEvent.properties.append(classes.Property('DTSTAMP', now.strftime('%Y%m%dT%H%M%SZ')))
        MMCalendar.events.append(icsEvent)
    calendarList.append(MMCalendar)

    formattedCal = MMiCal.foldtoICS(calendarList)
    tempUrlString = "C:/Users/Mgard/Desktop/workcrap/Webstuff/MarketMe/MMcalendar/temp/ " + f'{calendar}{username}.ics'

    if os.path.isfile(tempUrlString):
        with open(tempUrlString, 'w', encoding='UTF-8') as downloadable:
            print(formattedCal, file=downloadable)
        updatedFile = open(tempUrlString, 'r', encoding='UTF-8')
        response = HttpResponse(updatedFile, content_type='text/calendar') 
        response['Content-Disposition'] = f'attachment; filename="{calendar}{username}.ics"'
        return response
    else:
        newFile = open(tempUrlString, 'x', encoding='UTF-8')
        newFile.close()
        with open(tempUrlString, 'r+', encoding='UTF-8') as downloadable:
            print(formattedCal, file=downloadable)
        updatedFile = open(tempUrlString, 'r', encoding='UTF-8')
        response = HttpResponse(updatedFile, content_type='text/calendar') 
        response['Content-Disposition'] = f'attachment; filename="{calendar}{username}.ics"'
        return response

## Woof.  One thing to keep in mind is we'll want to control the client behavior on this,
## as both unavailable and active affect functionality.
def create_availability(request, calendar):
    if request.method == "POST":
        thisCal = Calendar.objects.get(Q(name=calendar, owner=request.user))
        if 'unavailable' in request.POST:
            newRule = AvailabilityRule.objects.create(
                name=request.POST['name'],
                calendar=thisCal,
                scope=request.POST['scope']
            )
        else:
            ## This feels tricky, but let's do it
            openHour = request.POST['begin'].split(':')
            closeHour = request.POST['end'].split(':')
            openTime = time(hour=int(openHour[0]), minute=int(openHour[1]))
            closeTime = time(hour=int(closeHour[0]), minute=int(closeHour[1]))
            userTZ = pytz.timezone(request.user.defaultTZ)
            today = date.today()
            if openTime > closeTime:
                dayDisplace = timedelta(days=1)
                nextDay = today + dayDisplace
                openPlaceholder = userTZ.localize(datetime.combine(today, openTime))
                closePlaceholder = userTZ.localize(datetime.combine(nextDay, closeTime))
            else:
                openPlaceholder = userTZ.localize(datetime.combine(today, openTime))
                closePlaceholder = userTZ.localize(datetime.combine(today, closeTime))
            print(openPlaceholder)
            print(closePlaceholder)
            newRule = AvailabilityRule.objects.create(
                name=request.POST['name'],
                begin=openPlaceholder,
                end=closePlaceholder,
                unavailable=False,
                calendar=thisCal,
                scope=request.POST['scope']
            )
        newRule.save()
        return HttpResponseRedirect(reverse('index'))
    else:
        form = AvailabilityForm()
        return render(request, 'MMUX/create.html', {
            'form': form,
            'formTitle': f'Create rule for {calendar}',
            'formAddress': f'/user/availability/{calendar}/new'
        })

def deleteAvailability(request, calendar, availability):
    thisCalendar = Calendar.objects.get(owner=request.user, name=calendar)
    thisRule = AvailabilityRule.objects.get(name=availability, calendar=thisCalendar)
    thisRule.delete()
    return HttpResponseRedirect(reverse('index'))