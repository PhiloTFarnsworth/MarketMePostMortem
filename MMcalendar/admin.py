from django.contrib import admin
from .models import Calendar, Event, Service, AvailabilityRule

# Register your models here.
admin.site.register(Calendar)
admin.site.register(Event)
admin.site.register(Service)
admin.site.register(AvailabilityRule)