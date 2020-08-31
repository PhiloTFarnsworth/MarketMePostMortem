class Property:
    def __init__(self, name, value, paramList=[]):
        self.name = name
        self.value = value
        self.parameters = {}
        ## I considered making Parameters their own class, but since their keys are unique
        ## I think it's better just to have parameters as a dict within the property itself
        for param in paramList:
            paramValue = param.split("=")
            self.parameters[paramValue[0]] = paramValue[1]

    def __str__(self):
        propString = f"{self.name}"
        if len(self.parameters) > 0:
            for param, val in self.parameters.items():
                propString += ";" + param + '=' + val
        propString += ':' + f"{self.value}"
        return propString

class Timezone:
    def __init__(self):    
        self.properties = []
        self.standardProperties = []
        self.daylightProperties = []

    def __str__(self):
        timezoneString = 'BEGIN:VTIMEZONE\n'
        for prop in self.properties:
            timezoneString += str(prop) + "\n"
        if len(self.standardProperties) > 0:
            timezoneString += 'BEGIN:STANDARD\n'
            for prop in self.standardProperties:
                timezoneString +=str(prop) + "\n"
            timezoneString += 'END:STANDARD\n'
        if len(self.daylightProperties) > 0:
            timezoneString += 'BEGIN:DAYLIGHT\n'
            for prop in self.daylightProperties:
                timezoneString +=str(prop) + "\n"
            timezoneString += 'END:DAYLIGHT\n'
        timezoneString += 'END:VTIMEZONE\n'
        return timezoneString

class Event:
    def __init__(self):
        self.properties = [] ## Property()

    def __str__(self):
        eventString = 'BEGIN:VEVENT\n'
        for prop in self.properties:
            eventString += str(prop) + '\n'
        eventString += 'END:VEVENT\n'
        return eventString

class Calendar:
    def __init__(self):
        self.events = [] ## event()
        self.properties = []
        self.timezones = []

    def __str__(self):
        calString = 'BEGIN:VCALENDAR\n'
        for prop in self.properties:
            calString += str(prop) + "\n"
        for entry in self.timezones:
            calString += str(entry)
        for event in self.events:
            calString += str(event)
        calString += 'END:VCALENDAR\n'
        return calString
