# MarketMe
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
authorization as well as fetching the user's main hub.  For the most part I utilize 
