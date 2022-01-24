from django.urls import path

from . import views
from MMcalendar import views as Calviews 
## Some thoughts on our view organization.  I feel that since the site is meant to be extremely
## user focused, we want to keep their urls to the point.  So to land on a user's profile, we want
## it to be marketme.com/username, to do so we're going to have to keep user off the list of available
## names, and we might want to reserve a few more for expansion.
urlpatterns = [
    path("", views.index, name="index"),
    path("user/login", views.login_view, name='login'),
    path('user/logout', views.logout_view, name='logout'),
    path('user/register', views.register, name='register'),
    path('user/settings', views.settings, name='settings'),
    path('user/profile_settings', views.profile_settings, name='profile settings'),
    path('user/createService', Calviews.create_service, name='create service'),
    path('user/myServices', Calviews.myServices, name='my services'),
    path('user/availability/<str:calendar>/new', Calviews.create_availability, name='create availability'),
    path('user/confirm/<str:uid>', Calviews.confirmEvent, name='confirm event'),
    path('user/export/<str:calendar>/<str:username>', Calviews.exportCalendar, name='export calendar'),
    path('user/availability/<str:calendar>/rules/<str:availability>', Calviews.deleteAvailability, name='delete availability'),
    path('<str:username>/Calendars/<str:calendar>/<int:year>/<int:month>/<int:day>/book', Calviews.bookEvent, name='book event'),
    path('<str:username>/myCalendars', Calviews.multiCalendar_view, name='multiCalendar'),
    path('<str:username>/Calendars/<str:calendar>/<int:year>/<int:month>', Calviews.calendar_view, name='single calendar'),
    path('<str:username>/Calendars/<str:calendar>/<int:year>/<int:month>/<int:day>', Calviews.dayDetails, name='day details'),
    path('user/profile/<str:username>', views.profile, name='profile'),
    path('user/relations/<str:username>/upgrade', views.relationUpgrade , name='relation upgrade'),
    path('user/relations/<str:username>/revoke', views.relationRevoke, name='relation revoke'),
    path('user/relations/<str:username>/restore', views.relationRestore, name='relation restore'),
    ]