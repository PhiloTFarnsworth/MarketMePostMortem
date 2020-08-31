## Alright, this is a fairly ambitious area of the project, as we're going to attempt to build .ical files
## from our event models.  Doing so will allow users to export their events into calendars that they can
## load into many different calendar applications.  Going further, with that functionality we could also
## build a python interpreter to read imported calendars and insert them into our web application.  
## The relative dearth of ICalendar RFC 5545 compliant python applications suggests it could be a worthwhile
## use of time.

## first consideration is folding of data.  For long strings you need to add a return plus a single whitespace
## to be read by .ical.  75 characters seems to be the suggested limit.

## Selective enforcement of multiple values for a parameter with the comma is something to keep in mind, 
## especially when it comes to reading foriegn calendars in.

## Gloss over Binary as we SHOULD not use it in this situation, according to 5545

## So it looks like every property can have meta data descriptors added to it.  So, as I understand:
#  PROPERTY; PARAMETER1="escape characters but not doublequotes"; PARAMETER2=boringvalue: Property-Value
#  So we read PROPERTYs based on a the new line, but if it has a single whitespace before it,
#  then it is folded data and not a new PROPERTY.

PARAMETERS = {}
PARAMETERS['ALTREP'] = 'A URI representation of property value (i.e. an html representation of a description). Dqoutes.'
PARAMETERS['CN'] = 'A "Common Name" for a calendar user'
PARAMETERS['CUTYPE'] = 'Type of calendar user (individual, group, resource, room, unknown)'
PARAMETERS['DELEGATED-FROM'] = 'A link to the cal-address of the delegator of an event. Dqoutes.'
PARAMETERS['DELEGATED-TO'] = 'A link to the cal-address to the delegated of an event. DQoutes.'
PARAMETERS['DIR'] = 'A URI to a directory. Dqoutes.'
PARAMETERS['DISPLAY'] = 'values: "BADGE", "GRAPHIC", "FULLSIZE", "THUMBNAIL"'
PARAMETERS['EMAIL'] = 'Alt email/identifier'
PARAMETERS['ENCODING'] = 'Default is UTF-8, must specify Base64 for binary encoded information'
PARAMETERS['FEATURE'] = 'values: "AUDIO", "CHAT", "FEED", "MODERATOR", "PHONE", "SCREEN", "VIDEO"'
PARAMETERS['FMTTYPE'] = 'Used to clarify format of uploads. (i.e. FMTTYPE=application/msword:ftp:e.com/this.doc)'
PARAMETERS['FBTTYPE'] = 'Free/Busy time representation, used along with optional FREEBUSY property'
PARAMETERS['LABEL'] = 'label for CONFERENCE'
PARAMETERS['LANGUAGE'] = 'Specifies language of items, otherwise no language is assumed'
PARAMETERS['MEMBER'] = 'Defines membership for attendees, as in "BigGroup@a.com":DrBig@Group.com. Dqoutes, Comma Seperated' ## ??? Mailing lists?
PARAMETERS['PARTSTAT'] = 'Defines participation for each attendee. For Events, "ACCEPTED","TENTATIVE","DECLINED" valid values.'
PARAMETERS['RANGE'] = 'Used with Recurrance to signify recurrance.  Only valid as "THISANDFUTURE"'
PARAMETERS['RELATED'] = 'Used with Trigger to prompt Alarms, "START" and "END" valid.'
PARAMETERS['RELTYPE'] = 'Used with RELATED-TO to clarify relation, "PARENT", "SIBLING", "CHILD"'
PARAMETERS['ROLE'] = 'Defines role of calendar user, such as "CHAIR", "OPT-", "NON-", and default "REQ-PARTICIPANT"'
PARAMETERS['RSVP'] = '"TRUE" or "FALSE" for expected RSVP from organizer to attendee'
PARAMETERS['SENT-BY'] = 'Specifies cal-address of user acting on behalf of another user. Dqoutes.'
PARAMETERS['TZID'] = 'Specifies Timezone in items specifically defined in local time that is not UTC.  Only used on Time/Datetime Properties'
PARAMETERS['VALUE'] = 'Explicitly specifies values for properties that are not the default value of a property'


## our Data type line-up:
DATATYPES = {}
DATATYPES['BINARY'] = 'most often BASE64 encoded information.'
DATATYPES['BOOLEAN'] = '"TRUE"/"FALSE" case-insensitive text.'
DATATYPES['CAL-ADDRESS'] = 'URI, most often a mailto:email@email.com'
DATATYPES['DATE'] = '4-2-2 so Apr 1, 2008 = 20080401 Year-month-day'
DATATYPES['DATETIME'] = '3 forms, with DateTtimeZ for UTC, no Z for local time and TZID with local time'
DATATYPES['DURATION'] = 'for items that have duration instead of set time, either in P[days]DT[hours]H[minutes]M[seconds]S or P[weeks]W'
DATATYPES['FLOAT'] = 'Float'
DATATYPES['INTEGER'] = 'integer'
DATATYPES['PERIOD'] = 'DATE[start]/DATE[end] or DURATION'
DATATYPES['RECUR'] = 'https://icalendar.org/iCalendar-RFC-5545/3-3-10-recurrence-rule.html'
DATATYPES['FREQ'] = 'required, but only once "Hourly", "Daily", "Weekly", "Monthly", "Yearly"'
DATATYPES['TEXT'] = 'TEXT'
DATATYPES['TIME'] = 'HHMMSS(Z) see datetime for more details.'
DATATYPES['URI'] = 'link to a resource, always double quoted.'
DATATYPES['UTC-OFFSET'] = '+/- HHMM(SS) Time.'

## While noting Calendar properties, we'll also have to code a way to produce a calstream.
CALPROPERTY = {}
CALPROPERTY['PRODID'] = 'REQUIRED Product Idenfication'
CALPROPERTY['VERSION'] = 'REQUIRED Indicates version of ical spec.  2.0 is 5545'
CALPROPERTY['CALSCALE'] = 'OPTIONAL default:GREGORIAN'
CALPROPERTY['METHOD'] = 'OPTIONAL, must match MIME content type otherwise will be read-only'
CALPROPERTY['NAME'] = 'OPTIONAL; types: TEXT; params: LANGUAGE, ALTREP'
CALPROPERTY['LAST-MODIFIED'] = 'OPTIONAL ONCE; types: DATE-TIME;'
CALPROPERTY['URL'] = 'OPTIONAL ONCE; types: URI;'
CALPROPERTY['SOURCE'] = 'OPTIONAL ONCE; types: URI;'
CALPROPERTY['REFRESH-INTERVAL'] = 'OPTIONAL ONCE; types: DURATION; params: VALUE'

EVENTPROPERTY = {}
EVENTPROPERTY['DTSTAMP'] = 'REQUIRED ONCE; types: DATE-TIME;'
EVENTPROPERTY['UID'] = 'REQUIRED ONCE; types: TEXT;' ## Just use UUID4
EVENTPROPERTY['DTSTART'] = 'REQUIRED if METHOD not defined ONCE; types: DATE-TIME, DATE; params: VALUE, TZID'
EVENTPROPERTY['CLASS'] = 'OPTIONAL ONCE; types: TEXT; values:"PUBLIC","PRIVATE","CONFIDENTIAL"; default: PUBLIC'
EVENTPROPERTY['CREATED'] = 'OPTIONAL ONCE; types: DATE-TIME;'
EVENTPROPERTY['DESCRIPTION'] = 'OPTIONAL; types: TEXT; params: LANGUAGE, ALTREP' ## ONCE per LANGUAGE
EVENTPROPERTY['GEO'] = 'OPTIONAL ONCE; types: FLOAT; values:"FLOAT;FLOAT"'
EVENTPROPERTY['LAST-MODIFIED'] = 'OPTIONAL ONCE; types: DATE-TIME;'
EVENTPROPERTY['LOCATION'] = 'OPTIONAL ONCE; types: TEXT; params: LANGUAGE, ALTREP'
EVENTPROPERTY['ORGANIZER'] = 'OPTIONAL ONCE; types: CAL-ADDRESS; params: CN, DIR, SENT-BY, LANGUAGE;'
EVENTPROPERTY['PRIORITY'] = 'OPTIONAL ONCE; types: INTEGER; values:"0-9"' ## 1 highest, 0 undefined.
EVENTPROPERTY['SEQUENCE'] = 'OPTIONAL ONCE; types: INTEGER;'
EVENTPROPERTY['STATUS'] = 'OPTIONAL ONCE; types: TEXT; values:"TENTATIVE", "CONFIRMED","CANCELLED";'
EVENTPROPERTY['SUMMARY'] = 'OPTIONAL ONCE; types: TEXT; params: LANGUAGE, ALTREP'
EVENTPROPERTY['TRANSP'] = 'OPTIONAL ONCE; types: TEXT; values:"OPAQUE","TRANSPARENT"'
EVENTPROPERTY['URL'] = 'OPTIONAL ONCE; types: URI;'
EVENTPROPERTY['RECURRENCE-ID'] = 'OPTIONAL ONCE; types: ???; params: VALUE, TZID, RANGE; values:"Reference to another event"'
EVENTPROPERTY['RRULE'] = 'OPTIONAL ONCE; types: RECUR;'
EVENTPROPERTY['DTEND'] = 'OPTIONAL ONCE Mutually exclusive with DURATION; types: DATE-TIME, DATE; params: VALUE, TZID'
EVENTPROPERTY['DURATION'] = 'OPTIONAL ONCE Mutually exclusive with DTEND; types: DURATION;'
EVENTPROPERTY['ATTACH'] = 'OPTIONAL; types: URI, BINARY; params: ENCODING, VALUE, FMTTYPE;'
EVENTPROPERTY['ATTENDEE'] = 'OPTIONAL; types: CAL-ADDRESS; params: CUTYPE, MEMBER, ROLE, PARTSTAT, RSVP, DELEGATED-TO, DELEGATED-FROM, SENT-BY, CN, DIR, LANGUAGE;'
EVENTPROPERTY['CATEGORIES'] = 'OPTIONAL; types: text; params: LANGUAGE'
EVENTPROPERTY['COMMENT'] = 'OPTIONAL; types: TEXT; params: LANGUAGE, ALTREP'
EVENTPROPERTY['CONTACT'] = 'OPTIONAL; types: TEXT; params: LANGUAGE, ALTREP'
EVENTPROPERTY['EXDATE'] = 'OPTIONAL; types: DATE-TIME, DATE; params: VALUE, TZID;'
EVENTPROPERTY['REQUEST-STATUS'] = 'OPTIONAL; types: TEXT; params: LANGUAGE;'
EVENTPROPERTY['RELATED-TO'] = 'OPTIONAL; types: TEXT; params: RELTYPE; value="UID";'
EVENTPROPERTY['RESOURCES'] = 'OPTIONAL; types: TEXT; params: LANGUAGE, ALTREP'
EVENTPROPERTY['RDATE'] = 'OPTIONAL; types: DATE-TIME, DATE, PERIOD; params: VALUE, TZID'
EVENTPROPERTY['COLOR'] = 'OPTIONAL ONCE; types: TEXT; value="CSS3 color name"'
EVENTPROPERTY['IMAGE'] = 'OPTIONAL; types: URI, BINARY; params: FMTTYPE, ALTREP, DISPLAY'
EVENTPROPERTY['CONFERENCE'] = 'OPTIONAL; types: URI; params: VALUE, FEATURE, LABEL, LANGUAGE'
EVENTPROPERTY['X-PROP'] = 'OPTIONAL'
EVENTPROPERTY['IANA-PROP'] = 'OPTIONAL'

VTIMEZONEPROPERTY = {}
VTIMEZONEPROPERTY['TZID'] = 'REQUIRED; types: TEXT;'
VTIMEZONEPROPERTY['LAST-MOD'] = 'OPTIONAL ONCE'
VTIMEZONEPROPERTY['TZURL'] = 'OPTIONAL ONCE; types: URI;'
VTIMEZONEPROPERTY['STANDARDC'] = 'OPTIONAL One of this or DAYLIGHTC must occur'
VTIMEZONEPROPERTY['DAYLIGHTC'] = 'OPTIONAL One of this or STANDARDC must occur'

TZPROP = {}
TZPROP['DTSTART'] = 'REQUIRED ONCE'
TZPROP['TZOFFSETTO'] = 'REQUIRED ONCE; types: UTF-OFFSET'
TZPROP['TZOFFSETFROM'] = 'REQUIRED ONCE; types: UTF-OFFSET;'
TZPROP['RRULE'] = 'OPTIONAL ONCE'
TZPROP['COMMENT'] = 'OPTIONAL; types: TEXT'
TZPROP['RDATE'] = 'OPTIONAL'
TZPROP['TZNAME'] = 'OPTIONAL; types: TEXT; params: LANGUAGE'

def initStaticValue(staticClass, *argv):
    for arg in argv:
        staticClass.create(arg)
        staticClass.save()
    return 0