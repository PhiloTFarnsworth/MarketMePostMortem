from django.contrib import admin
from .models import User, Relationship, Theme, Profile

# Register your models here.
admin.site.register(User)
admin.site.register(Relationship)
admin.site.register(Theme)
admin.site.register(Profile)