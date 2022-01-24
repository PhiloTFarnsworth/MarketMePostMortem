from calendar import HTMLCalendar
from bs4 import BeautifulSoup
from datetime import date, datetime, date, time, timedelta
from django.utils import timezone

 ##TODO: BeautifulSoup up the standard python html calendar.
def customHTMLCalendar(year, month, events, anonEvents, availability, username, calendarname):
    baseCal = HTMLCalendar(0).formatmonth(year, month)
    soupedCal = BeautifulSoup(baseCal, features='html.parser')
    table = soupedCal.table
    table['class'] = "table"
    calendarDays = soupedCal.find_all('td')
    for day in calendarDays:
        contents = str(day.string)
        weekday = str(day['class'][0]).upper()
        ## Grab the table squares associated with days.
        if contents.isdigit():
            ## The contents secured, we clear them and prepare to replace with our own custom 
            ## content
            day.clear()
            ## We want to be able to easily check whether this day is past, present or future.  Fun fact, 
            ## in the original implementation we just checked the day, making every month contain the past
            ## present and future.  Very Billy Pilgrim.
            if date(year = year, month=month, day=int(contents)) < date.today():
                day['data-state'] = 'Past'
            elif date(year = year, month=month, day=int(contents)) == date.today():
                day['data-state'] = 'Present'
                day['class'] = 'bg-info'
            else:
                day['data-state'] = 'Future'
            ## Replace the day number with a header number.
            dayNumberTag = soupedCal.new_tag('h3')
            dayNumberLink = soupedCal.new_tag('a', href=f'/{username}/Calendars/{calendarname}/{year}/{month}/{contents}')
            dayNumberLink.append(f'{contents}')
            dayNumberTag.append(dayNumberLink)
            day.append(dayNumberTag)
            ## Give specific days an id.
            day['id'] = f'day{contents}'
            dayRule = availability[weekday]
            ## datetimes to a timedelta
            if len(dayRule) != 0:
                normalAvailHours = dayRule[1] - dayRule[0]
            else:
                normalAvailHours = timedelta(hours=0)
            ## Add a tag for regular available hours
            regularHourTag = soupedCal.new_tag('p')
            if normalAvailHours != timedelta(hours=0):
                begin = dayRule[0].strftime('%I:%M %p')
                end = dayRule[1].strftime('%I:%M %p')
                regularHourTag.append(f'Regular Hours: {begin}-{end}') 
            else:
                day['class'] = "table-warning"
                regularHourTag.append('Unavailable for day')
            day.append(regularHourTag)
            ##eventNumber = len(events[int(contents)])
            ## We'll check how many hours have already been reserved and what visible events
            ## we can show the user by iterating over all the events passed
            reservedHours = timedelta(hours=0)
            reservedHoursTag = soupedCal.new_tag('p')
            visibileEventTag = soupedCal.new_tag('dl')
            for event in events[int(contents)]:
                ## We stripped the anonymous events of this data, so for those
                ## with the data we'll just add their duration to the reserved hours pile
                reservedHours += event.duration
                summaryTag = soupedCal.new_tag('dt')
                summaryTag.append(f'{event.summary}')
                eventStartTag = soupedCal.new_tag('dd')
                durationTag = soupedCal.new_tag('dd')
                eventStart = event.dtstart.strftime('%I:%M %p')
                eventStartTag.append(f'{eventStart}')
                durationTag.append(f'{event.duration}')
                visibileEventTag.append(summaryTag)
                visibileEventTag.append(eventStartTag)
                visibileEventTag.append(durationTag)
            for event in anonEvents[int(contents)]:
                reservedHours += event.duration
            daysAvailHours = normalAvailHours - reservedHours 
            if daysAvailHours > timedelta(hours=0):
                reservedHoursTag.append(f'Hours Available: {daysAvailHours}')
            else:
                if day['class'] != "bg-info":
                    day['class'] = 'table-warning'
                reservedHoursTag.append('No Hours Available')
            ## Add that data to the day's table square
            day.append(reservedHoursTag)
            day.append(visibileEventTag)
    newCalendar = soupedCal.prettify()
    return newCalendar
            
## This might be a goofy idea, but I think we're going to build the dayplanner from scratch using BeautifulSoup.
## The pros of this approach is that I need a pretty simple repeating base template, iterated 24 times.  While
## we could probably create it in the Jinja engine, I feel like the ability to build the skeleton, then place our
## event objects will allow greater control.
def dayPlannerScaffold(date):
    dateString = date.strftime('%A %B %d, %Y')   
    start = BeautifulSoup('<div></div>', features='html.parser')
    baseDiv = start.div
    baseDiv['class'] = 'dayPlanner'
    for i in range(24):
        tag = 'am'
        if i == 0:
            x = 12
        elif i > 11:
            if i == 12:
                x = i
            else:
                x = i - 12
            tag = 'pm'
        else:
            x = i
        hour = start.new_tag('div')
        hour['class'] = 'hour'
        baseDiv.append(hour)
        hourHeader = start.new_tag('h3')
        hourHeader.string = f'{x}'
        hour.append(hourHeader)
        revealButton = start.new_tag('button')
        revealButton['class'] = 'hourRevealbtn'
        revealButton['id'] = f'h{x}{tag}reveal'
        revealButton.string = f'Show {x}{tag}'
        hour.append(revealButton)
        minuteContainer = start.new_tag('div')
        minuteContainer['class'] = 'minuteContainer'
        minuteContainer['id'] = f'h{x}{tag}container'
        hour.append(minuteContainer)
        collapseButton = start.new_tag('button')
        collapseButton.string = 'Collapse Hour'
        for y in range(0, 60, 15):
            minute = start.new_tag('div')
            minute['class'] = 'minute'
            if y == 0:
                minute['id'] = f'{x}-00_{tag}'
            else:    
                minute['id'] = f'{x}-{y}_{tag}'
            minuteHeader = start.new_tag('h4')
            if y == 0:
                minuteHeader.string = f'{x}:00 {tag}'
            else:
                minuteHeader.string = f'{x}:{y} {tag}'
            minute.append(minuteHeader)
            infoBox = start.new_tag('p')
            infoBox['class'] = 'minuteInfo'
            if y == 0:
                infoBox['id'] = f'{x}-00_{tag}.info'
            else:
                infoBox['id'] = f'{x}-{y}_{tag}.info'
            infoBox.string = 'Open'
            minute.append(infoBox)
            statusBox = start.new_tag('div')
            statusBox['class'] = 'minuteStatus'
            if y == 0:
                statusBox['id'] = f'{x}-00_{tag}.status'
            else:
                statusBox['id'] = f'{x}-{y}_{tag}.status'
            scheduleBtn = start.new_tag('button')
            scheduleBtn['class'] = 'scheduleBtn'
            scheduleBtn['id'] = f'{x}-{y}_{tag}.btn'
            scheduleBtn.string = 'Schedule a Service'
            scheduleDetails = start.new_tag('p')
            scheduleDetails['id'] = f'{x}-{y}_{tag}.details'
            scheduleDetails['class'] = 'scheduleDetails'
            scheduleDetails.string = 'This is an open timeslot'
            statusBox.append(scheduleDetails)
            statusBox.append(scheduleBtn)
            minute.append(statusBox)
            minuteContainer.append(minute)
        minuteContainer.append(collapseButton)
        collapseButton['hidden'] = True
    overflowMinutes = start.new_tag('p')
    overflowMinutes['id'] = 'overflowMinutes'
    overflowMinutes['style'] = 'display: none'
    baseDiv.append(overflowMinutes)
    scaffold = start.prettify()
    return scaffold

## Wanted to seperate this from the scaffold because the scaffold seems like it
## would be a decent option for an html day planner, just add CSS.
def applySchedule(html, availability, events, anonEvents, theDate):
    htmlScaffold = BeautifulSoup(html, features='html.parser')
    minuteIntervals = htmlScaffold.find_all('div', class_='minute') 

    ## We'll parse our passed availabilities and add them to this list.  It's been a little confusing,
    ## but our availability rule can be entered as any period of time beginning on a day, and we'll read
    ## it's value overflowing to the next day if the open hour < close hour.  so 11:30 pm -> 11 pm = 23.5 hours
    ## but 11pm -> 11:30pm = .5 hours.  Which means we could potentially have two values of discrete time periods
    ## to compare.
    openHours = []
    closeHours = []

    ## This space magic should read out our availability across timezones.
    iteration = 1
    for rule in availability:
        ## One problem, we've been passing empty tuples into availability when this should be impossible, so time for a 
        ## hack.  
        if rule == ():
            rule = (timezone.now(), timezone.now())
        
        displace = timedelta(days=iteration)
        ## so if our rule days match, put them on the same day, otherwise, we displace the close time forward
        ## This is a shrug attempt
        if rule[0].day == rule[1].day:
            thisOpen = rule[0].replace(year=theDate.year, month=theDate.month, day=theDate.day) - displace
            thisClose = rule[1].replace(year=theDate.year, month=theDate.month, day=theDate.day) - displace
        else:
            displaceForward = timedelta(days=1)
            thisOpen = rule[0].replace(year=theDate.year, month=theDate.month, day=theDate.day) - displace
            thisClose = rule[1].replace(year=theDate.year, month=theDate.month, day=theDate.day) - displace + displaceForward
        openHours.append(thisOpen)
        closeHours.append(thisClose)
        iteration = iteration - 1

    ## one special addition to our dayplanner, the amount of time thisClose goes past our date.time.  We need this for 
    ## timezone compatability.  If someone schedules a service that goes past midnight their time, this number will
    ## tell us if it's eligble in the span of the availability slot.
    
    nextDay = theDate + timedelta(days=1)
    zeroHour = time(hour=0)
    nextDayBegins = timezone.make_aware(datetime.combine(date=nextDay, time=zeroHour))
    if closeHours[1] > nextDayBegins:
        thisDelta = closeHours[1] - nextDayBegins 
        minuteSegments = (thisDelta.seconds/60)/15
    else:
        minuteSegments = 0
    overflowSegments = htmlScaffold.find('p', id='overflowMinutes') 
    overflowSegments.string = f'{minuteSegments}'

    for minute in minuteIntervals:
        ## :) we're going to see some splits here.
        unformattedTime = minute['id']
        splitHour = unformattedTime.split('-')
        splitMinute = splitHour[1].split('_')
        hour = int(splitHour[0])
        minuteNumber = int(splitMinute[0])
        if splitMinute[1] == 'pm':
            if hour != 12:
                hour += 12
        else:
            if hour == 12:
                hour -= 12
        IntervalTime = time(hour=hour, minute=minuteNumber)

        ## So herein lies the tricky part.  if we have available hours that are localized to the past the
        ## end or before the beginning of the day, we can't really display them.  we can obviously trim the
        ## hours at the end or before the beginning of the day, but how do format those hours trimed onto a different
        ## day?  One answer is to take the availability rules of the days adjacent.  We then test to see if we cross either
        ## time horizon.  If we do, then we check the adjacent rule in the opposite direction, to see if it has any overflow
        ## to add onto the day.  

        comparableDateTime = timezone.make_aware(datetime.combine(date=theDate, time=IntervalTime))
        
        ## We change the open slots that fall outside the available hours into red, unavailable slots.
        unavailablecount = 0
        for i in range(2):
            if comparableDateTime < openHours[i] or comparableDateTime >= closeHours[i]:
                unavailablecount += 1
        ## A time slot needs to be unavailable for both timeslots for it to be unavailable
        if unavailablecount == 2:
            unavailableTimeStatus = minute.find_all('div', class_='minuteStatus')
            for status in unavailableTimeStatus:
                status['style'] = 'background-color: Red'
                status.button.string = 'Unavailable'
                status.p.string = 'This timeslot is unavailable'
            unavailableTimeInfo = minute.find_all('p', class_='minuteInfo')
            for info in unavailableTimeInfo:
                info.string = 'Unavailable'
            
        ## Now we compare for events.
        for event in events:
            if comparableDateTime >= event.dtstart and comparableDateTime < event.dtend:
                reservedTimeStatus = minute.find_all('div', class_='minuteStatus')
                for status in reservedTimeStatus:
                    status['style'] = 'background-color: DodgerBlue'
                    status.button.string = 'Reserved'
                    status.p.string = f'{event.summary}'
                reservedTimeInfo = minute.find_all('p', class_='minuteInfo')
                for info in reservedTimeInfo:
                    info.string = 'Reserved'
        for event in anonEvents:
            if comparableDateTime >= event.dtstart and comparableDateTime < event.dtend:
                reservedTimeStatus = minute.find_all('div', class_='minuteStatus')
                for status in reservedTimeStatus:
                    status['style'] = 'background-color: Yellow'
                    status.button.string = 'Reserved'
                    status.p.string = 'This timeslot is reserved'
                reservedTimeInfo = minute.find_all('p', class_='minuteInfo')
                for info in reservedTimeInfo:
                    info.string = 'ReservedAnon'
        minute['style'] = 'display: none'
    formattedScaffold = htmlScaffold.prettify()
    return formattedScaffold

## Availability rule condenser.  Takes the queryset avalability rules, applies them to a dict with seven entries
## for each day, with the hours that are available as a tuple.
def AvailabilityArbiter(querySet):
    DaysofWeek = {}
    week = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    ruleCodes = ['EVD', 'WDY', 'WND']
    ruleCodes.extend(week)
    sameTime = timezone.now()
    unavailable = (sameTime, sameTime)
    for day in week:
        DaysofWeek[day] = ()
    ## On one hand, this is terrible, on the other, I don't think it's worth it to change my scope rule names to
    ## better match the python, as then I'd have to assign numbers for everyday/weekends.  So for now, readability
    ## wins out over terseness.
    for rule in querySet:
        if rule.scope == 'EVD':
            if rule.unavailable != True:
                for x in range(7):
                    DaysofWeek[week[x]] = (timezone.localtime(rule.begin), timezone.localtime(rule.end))
            else:
                for x in range(7):
                    DaysofWeek[week[x]] = unavailable
    for rule in querySet:    
        if rule.scope == 'WDY':
            if rule.unavailable != True:
                for x in range(5):
                    DaysofWeek[week[x]] = (timezone.localtime(rule.begin), timezone.localtime(rule.end))
            else:
                for x in range(5):
                    DaysofWeek[week[x]] = unavailable
        elif rule.scope == 'WND':
            if rule.unavailable != True:
                for x in range(5,7):
                    DaysofWeek[week[x]] = (timezone.localtime(rule.begin), timezone.localtime(rule.end))
            else:
                for x in range(5,7):
                    DaysofWeek[week[x]] = unavailable
    for rule in querySet:
        if rule.scope in week:
            if rule.unavailable != True:
                DaysofWeek[rule.scope] = (timezone.localtime(rule.begin), timezone.localtime(rule.end))
            else:
                DaysofWeek[rule.scope] = unavailable
    ## In case the user does not define a day of the week, we assume they are unavailable.
    ## For some reason we have run into errors where the arbiter doesn't replace empty tuples with
    ## the unavailable tuple. A true mystery wrapped in an enigma.
    for _, val in DaysofWeek.items():
        if val == ():
            val == unavailable
    return DaysofWeek

## We don't want to upload event information to people who don't have permission to see it,
## so we'll use this function to strip the information we don't need to send.  Must use the values
## queryset option
def eventCleaner(querySet):
    necessaryAttrs = ['dtstart', 'dtend']
    for event in querySet:
        for key, _ in event.items():
            if key not in necessaryAttrs:
                event[f'{key}'] = 'private'
    return querySet
    
def initStaticValue(staticClass, *argv):
    for arg in argv:
        value = staticClass.create(arg)
        value.save()
    return 0