# 'MarketMe' - A Post Mortem
## A Productivity Suite for Freelancers

MarketMe was a very ambitious Python Django Project, with the idea of creating a home page for Freelancers
to organize their calendar, contacts and social media presence on a single site.  Freelancers would have a calendar
in which they could offer services over slots of time, and other users could book a service and pay for it on site.
Freelancers would also be able to schedule content to be posted to their social media pages, and MarketMe would
track engagement that led back to their MarketMe pages.  Finally, Freelancers that provided services like interactive
workshops or lectures would be able to host their content on site, gated by whether the user had subscribed to that service.

Those lofty goals were not realized, but as a whole there are some interesting things I was able to do, and more importantly
learn, as I pursued the above design.  It is important to note that the code shared here is really mid-development and quite
rough.  Had the design progressed further, there are plenty of areas where I feel that I could've simplified the implementation, 
even if there are some inherent flaws with the design as whole.  

### MMUX - MarketMe User Experience
Owing to the very large design goals, I made an effort to try and build out services from the ground up.  MMUX controls user 
authorization as well as fetching the user's dashboard.  The design is a little muddled, as some items that are designed to be accessed
from the dashboard should likely be associated with other services, such as relationship management, but is otherwise functional for what
a user service might look like at a prototype stage.  The front end is very light on javascript and opts for django's template rendering
to create views, along with django forms that use our models to generate the register and log in forms.  

### MMCalendar

#### Calendar
The meat of this project lies in the calendar, where users can select services and reserve timeslots with another user.  The implementation
as it stands at the moment is not entirely durable, but the general actions on can perform on a calendar are present, with the calendar owner
able to create availability rules, and other users can see those rules and select timeslots within those bounds to request a timeslot.  An email
with a confirmation is generated and the calendar owner can confirm it from the email or on their dashboard at MarketMe.  The most important part
of the design, and probably the part that is most durable, is the model we have defined for events, services and the general user calendar.  Based
on my reading of RFC 5455 'iCalendar' spec, the model itself is designed to be compatible with any well-defined iCal file.

#### MMiCal
To help conform to the 'iCalendar' spec, as well as to import any .ics files from any other source, I built a small package to allow me to
'unfold' an .ics file into a python dictionary, as well as to 'fold' a dictionary into a compliant .ics file.  While it's not exactly production
grade, the process of building a parser to the 'iCalendar' spec was a very interesting way to learn the ins and outs of the specification and was
informative in building the models for the MMCalendar service.  

### Post Mortem
While there are a few good ideas within the MarketMe design, the breadth of the design and the inexperience of the developer were major
impediments to creating a service that would live up to the design.  While there are a few steps taken to try and parcel up the tasks,
in some areas I feel this was counter productive and added extra complexity when it would've been more prudent to trim the design and 
specifically focus on doing one thing well and growing from there.  That being said, MarketMe was a learning experience and in that
vein I consider it a successful one.  

### Development Screenshots
#### Dashboard
![Dashboard](Dashboard.png)

#### Calendar
![Calendar](Calendar.png)


