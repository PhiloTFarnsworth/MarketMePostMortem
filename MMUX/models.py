from django.db import models
from django.contrib.auth.models import AbstractUser
## We'll use the UX app to store our user model.
class User(AbstractUser):
    pass

