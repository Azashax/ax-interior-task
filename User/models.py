from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class MyUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class MyUser(AbstractBaseUser, PermissionsMixin):
    ROLES = (
        ('Admin', 'Admin'),
        ('Teamlead', 'Teamlead'),
        ('Manager', 'Manager'),
        ('QA', 'QA'),
        ('Employee', 'Employee'),
    )
    first_name = models.CharField(verbose_name="First Name", max_length=255)
    last_name = models.CharField(verbose_name="Last Name", max_length=255)
    username = models.CharField(verbose_name="Username", max_length=255, unique=True)
    role = models.CharField(max_length=20, choices=ROLES, default="Employee")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    link_telegram = models.CharField(max_length=1000, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    task_point = models.FloatField(default=0)
    correcting_point = models.FloatField(default=0)
    objects = MyUserManager()

    USERNAME_FIELD = 'username'


class Teams(models.Model):
    name = models.CharField(max_length=255)
    teamlead = models.OneToOneField(MyUser, on_delete=models.CASCADE, null=True, blank=True, related_name='teamlead', limit_choices_to={'role': 'Teamlead'})
    employees = models.ManyToManyField(MyUser, blank=True, related_name='employee', limit_choices_to={'role': 'Employee'})
