from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def __create_user(self, *args, **kwargs):
        print(args, **kwargs)
        raise Exception('salom')

    def create_user(self, *args, **kwargs):
        return self.__create_user(*args, **kwargs)

    def create_superuser(self, *args, **kwargs):
        return self.__create_user(*args, **kwargs)


class User(AbstractUser):
    objects = UserManager()

    phone = models.CharField(max_length=15, unique=True)
    telegram_user_id = models.BigIntegerField(default=None, unique=True)
    current_page = models.IntegerField(default=0)
    USERNAME_FIELD = 'phone'


class Product(models.Model):
    button_title = models.CharField(max_length=20)
    subject = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField()