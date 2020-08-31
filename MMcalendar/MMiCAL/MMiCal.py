import os
from math import floor, ceil
from classes import Event, Calendar, Property, Timezone

def foldtoICS(calendarList):
    """foldtoICS takes a list of calendar objects and returns an ICalendar friendly string."""
    ICSString = ''
    for cal in calendarList:
        ICSString += "BEGIN:VCALENDAR\n"
        for prop in cal.properties:
            ICSString += foldedProperty(prop)
        for entry in cal.timezones:
            ICSString += "BEGIN:VTIMEZONE\n"
            for prop in entry.properties:
                ICSString += foldedProperty(prop)
            if len(entry.standardProperties) > 0:
                ICSString += "BEGIN:STANDARD\n"
                for prop in entry.standardProperties:
                    ICSString += foldedProperty(prop)
                ICSString += "END:STANDARD\n"
            if len(entry.daylightProperties) > 0:
                ICSString += "BEGIN:DAYLIGHT\n"
                for prop in entry.daylightProperties:
                    ICSString += foldedProperty(prop)
                ICSString += "END:DAYLIGHT\n"
            ICSString += "END:VTIMEZONE\n"
        for event in cal.events:
            ICSString += "BEGIN:VEVENT\n"
            for prop in event.properties:
                ICSString += foldedProperty(prop)
            ICSString += "END:VEVENT\n"
        ICSString += "END:VCALENDAR\n"
    return ICSString


def foldedProperty(prop):
    """
        foldedProperty takes a full property and returns an iCalendar compliant
        folded string. 
    """
    prop.value = prepICSText(prop.value)
    checkString = ''
    if len(prop.parameters) > 0:
        checkString += f"{prop.name};"
        for param, val in prop.parameters.items():
            checkString += f"{param}={val};"
        checkString += f":{prop.value}\n"
    else:
        checkString += f"{prop.name}:{prop.value}\n"
    length = len(checkString)
    ICSstring = ''
    if length > 73:
        x = ceil(length/73)
        for i in range(x):
            if i == x-1:
                ICSstring += checkString[(i*73):length]
            else:
                ICSstring += checkString[(i*73):((i+1)*73)] + "\n "
    else: 
        ICSstring += checkString
    return ICSstring

def unfoldToCalendarList(stream):
    """
        unfoldToCalendarList takes an opened stream from an iCalendar file (See IETF REF 5545,7986)
        and returns a list of calendar objects, with all compatiable components returned as
        objects nested within said calendar objects.
    """    
    rawStringList = stream.read(-1).splitlines()
    rawLength = len(rawStringList)
    unfoldedStrings = []
    storageString = ''
    ## We're going to have to concanate several strings in a row at times, so need to keep
    ## track of string indexes already added to our new list of strings.
    indexToSkip = []
    ## so we'll go go from string to string, checking if the string ahead
    for i in range(rawLength):
        if i not in indexToSkip and rawStringList[i].startswith('X-') != True:
            storageString = rawStringList[i]
            checkFurther = checkNextString(rawStringList, i, storageString, rawLength)
            if checkFurther[0] == []:
                unfoldedStrings.append(storageString)
            else:
                unfoldedStrings.append(checkFurther[1])
                for item in checkFurther[0]:
                    indexToSkip.append(item)
    ## Since .ics files are built to hold multiple calendars, I think we store any import
    ## as a list.
    if unfoldedStrings[0] != "BEGIN:VCALENDAR":
        return print("Error: Line 1 does not contain 'BEGIN:VCALENDAR")
    calendarList = []
    ## need to keep track of our calendars
    calendarCount = 0
    ## and events per calendar
    eventCount = 0
    timezoneCount = 0
    PropOwnership = ""
    for phrase in unfoldedStrings:
        ## ignore empty lines
        if phrase == "":
            continue
        ## We send the most likely propVal split into checkEscapedColon,
        ## which will recursively check for dqoute escapes in parameter values.
        propVal = phrase.split(":", maxsplit=1)
        escapedPropParam = checkEscapedColon(phrase, propVal[0])
        escapedPropVal = phrase.replace(escapedPropParam + ":", '')
        ## Switch-a-palooza
        if escapedPropParam == "BEGIN":
            if escapedPropVal == "VCALENDAR":
                calendarList.append(Calendar())
                PropOwnership = "CALENDAR"
            elif escapedPropVal == "VEVENT":
                calendarList[calendarCount].events.append(Event())
                PropOwnership = "EVENT"
            elif escapedPropVal == "VTIMEZONE":
                calendarList[calendarCount].timezones.append(Timezone())
                PropOwnership = "TIMEZONE"
            elif escapedPropVal == "STANDARD":
                PropOwnership += ":STANDARD"
            elif escapedPropVal == "DAYLIGHT":
                PropOwnership += ":DAYLIGHT"
            else:
                PropOwnership = ''
        elif escapedPropParam == "END":
            ## if we end a calendar, increment calendarCount by 1, reset eventCount
            if escapedPropVal == "VCALENDAR":
                calendarCount += 1
                eventCount = 0
            elif escapedPropVal == "VEVENT":
                eventCount += 1
            elif escapedPropVal == "VTIMEZONE":
                timezoneCount += 1
            elif escapedPropVal == "STANDARD":
                PropOwnership = "TIMEZONE"
            elif escapedPropVal == "DAYLIGHT":
                PropOwnership == "TIMEZONE"
        else:
            cleanValue = cleanICSText(escapedPropVal)
            ## What monster would use a semi-colon within a parameter??  Well, now if they do I 
            # don't have to worry about it.
            propParams = checkEscapedSemiColon(escapedPropParam)
            propName = propParams[0]
            paramList = []
            if len(propParams) != 1:
                propParams.pop(0)
                ## Filter out X- params
                for param in propParams:
                    ## While I think it is not exactly what was envisioned in spec,
                    ## we get empty strings from our splits when we have a semicolon
                    ## before a colon.  While it's an error from decoding our own encoding,
                    ## I don't see a downside in adding this extra precaution, to stop
                    ## our decoder from grinding to a halt.
                    if param.startswith("X-") or len(param) < 1:
                        pass
                    else:
                        paramList.append(param)
            if PropOwnership == "CALENDAR":
                calendarList[calendarCount].properties.append(
                    Property(propName, cleanValue, paramList)
                    )
            elif PropOwnership == "EVENT":
                calendarList[calendarCount].events[eventCount].properties.append(
                    Property(propName, cleanValue, paramList)
                    )
            elif PropOwnership.startswith("TIMEZONE"):
                if PropOwnership.endswith("STANDARD"):
                    calendarList[calendarCount].timezones[timezoneCount].standardProperties.append(
                        Property(propName, cleanValue, paramList)
                    )
                elif PropOwnership.endswith("DAYLIGHT"):
                    calendarList[calendarCount].timezones[timezoneCount].daylightProperties.append(
                        Property(propName, cleanValue, paramList)
                    )
                else:
                    calendarList[calendarCount].timezones[timezoneCount].properties.append(
                        Property(propName, cleanValue, paramList)
                    )
    return calendarList

## A colon split is fine for 90% of of all properties, except for a small subset where a colon is escaped in a dqoute.
## so how do we detect this?  I think the best way is to do a count of dquotes we have in the property/param
## area after the split.  If we have an odd number of dqoutes, then we must be in the middle of an escaped 
## parameter, and we can instead split by colon and add the rightmost splits to each other until we have
## an even number of DQoutes.  
def checkEscapedColon(phrase, tentativeProperty, recursed=0):
    """
        checkEscapedColon checks for colons escaped by doubles quotes in a value of a parameter 
        when reading an ics phrase.  This Function takes a complete PROP;PARAM=VALUE;...:VALUE 
        'phrase', along with the initial 'tentativeProperty' of how the phrase should be split.  
        Recursed is to be left as default, is used as a counter to properly consider 
        progressively longer strings.  Returns the entire PROP;PARAM=VALUE;...: string.
    """
    correctString = ''
    if tentativeProperty.find('"') != -1:
        checkDQoutes = tentativeProperty.split('"')
        ## if checkDQoutes is an even number of strings we have an unclosed dqoute 
        if len(checkDQoutes) % 2 == 0:
            colonHunter = phrase.split(":")
            recursed += 1
            potentialPropVal = ''
            for i in range(recursed + 1):
                potentialPropVal += colonHunter[i] + ":"
            escaped = checkEscapedColon(phrase, potentialPropVal, recursed=recursed)
            if len(escaped.split('"')) % 2 == 1:
                correctString += escaped.rstrip(":")
        else:
            correctString += tentativeProperty
    else:
        correctString += tentativeProperty
    return correctString

## Personally, I'd rather just omit Alt-Reps, as they seem like a prime vector for malicious
## code if implemented, as well as being a privacy concern.  Kinda funny that they'd change 
## their recommendation for UUID in 7745 to make events more anonymous, while adding a field
## like Alt-Rep.  Anyway, we should check for semi-colons escaped in parameters.
def checkEscapedSemiColon(phrase):
    """
        checkEscapedSemiColon is another parsing function, similar to checkEscapedColon, except
        that it only needs to take a PROP;PARAM=VALUE;...: portion of an ics phrase.  Returns
        a list of of all items delimited by a semi colon that are not escaped.
    """
    paramList = phrase.split(";")
    paramLen = len(paramList)
    popList = []
    for i in range(paramLen):
        if i in popList:
            continue
        if paramList[i].find('"') != -1:
            ## much like before, we find a quotation mark, see if it is closed. 
            if len(paramList[i].split('"')) % 2 == 0:
                paramList[i] += ";" + paramList[i+1]
                paramList.pop(i+1)
                ## Best Bug:  Tried using len(popList) as I was appending, which 
                ## (duh) gives you the length of the list pre-append.  "+ 1" is truly
                ## the mvp of programming.
                popList.append(paramLen - (len(popList) + 1))
        else:
            ## cool, no quotes.
            pass
    return paramList

## Note: There is no checkEscapedComma, in part because our model assumed Parameters only have one value,
## and because of considerations for fields like alt-rep.

## checks the next string for folding, otherwise returns a list of indexs already
## associated with the new concanated string.
def checkNextString(StringList, index, storageString, rawlength):
    """
        checkNextString takes a parsed ICS string list, along with the current index being read,
        the string the user is writing to along with the rawlength of the string list.  returns
        a tuple containing the indexes we combined into the string, as well as an updated 
        storage string.
    """
    ## a list of indexs of strings concanated to make our storage string
    indexToSkip = []
    ## make sure the index we are checking isn't out of bounds, has a single whitespace
    ## to being
    if index + 1 < rawlength and StringList[index+1].startswith(" "):
        ## combine our strings, replace " " instead of lstrip to preserve spaces between
        ## words that coincide with folds.
        storageString += StringList[index+1].replace(" ", "", 1)
        indexToSkip.append(index+1)
        checkFurther = checkNextString(StringList, index+1, storageString, rawlength)
        ## did we change the string?
        if checkFurther[1] != storageString:
            for i in checkFurther[0]:
                indexToSkip.append(i)
            ## get the full string
            storageString = checkFurther[1]
    return indexToSkip, storageString

def cleanICSText(string):
    """
        cleanICSText takes a string with iCalendar TEXT escapes, and returns a python
        friendly string.
    """
    newstring = string.replace('\\\\', "\\").replace('\\;', ";").replace('\\,', ",")
    return newstring

def prepICSText(string):
    """prepICSText takes a python string and returns a properly escaped iCalendar TEXT"""
    newstring = string.replace('\\', "\\\\").replace('\\\\n','\\n').replace(';', '\\;').replace(',', "\\,")
    return newstring

def main():
    testfile = open('example.ics', 'r', encoding='UTF-8')
    calList = unfoldToCalendarList(testfile)    
    print(calList[0])
    print("<-------------------->")
    backtoICS = foldtoICS(calList)
    print(backtoICS)
    with open("new.ics", "w", encoding='UTF-8') as newfile:
        print(backtoICS, file=newfile)

if __name__ == "__main__":
    main()