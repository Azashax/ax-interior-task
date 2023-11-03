from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from User.models import MyUser
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError

STATUS = (
    ('open', 'open'),
    ('in progress', 'in progress'),
    ('complete', 'complete'),
    ('checked', 'checked'),
    ('correcting', 'correcting'),
    ('waiting', 'waiting'),
)


class Project(models.Model):
    PROJECT_TYPE = (
        ('Tower', 'Tower'),
        ('Villa', 'Villa'),
    )
    BUILT = (
        ('finished', 'finished'),
        ('off plan', 'off plan'),
    )
    TEG = (
        ('None', 'None'),
        ('Priority', 'Priority'),
        ('High priority', 'High priority'),
    )
    EXTERIOR_STATUS = (
        ('open', 'open'),
        ('in progress', 'in progress'),
        ('checked', 'checked'),
    )
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE, default="Tower")
    project_teamlead_user = models.ForeignKey(
        MyUser,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Teamlead'},
        related_name='project_teamlead_user',
        null=True,
        blank=True
    )
    project_name = models.CharField(max_length=255)
    region = models.ForeignKey("Region", on_delete=models.CASCADE, related_name="region", blank=True, null=True)
    built = models.CharField(max_length=20, choices=BUILT, default=BUILT[0][0])
    project_status = models.CharField(max_length=20, choices=STATUS, default=STATUS[0][0])
    link_clickup = models.TextField()
    link_cet3 = models.TextField()
    project_teg = models.CharField(max_length=20, choices=TEG, default="None")
    exterior_status = models.CharField(max_length=20, choices=EXTERIOR_STATUS, default=STATUS[0][0])

    description = models.TextField(blank=True, null=True)

    task_with = models.OneToOneField("Task", on_delete=models.SET_NULL, related_name="task_with", blank=True, null=True)
    task_without = models.OneToOneField("Task", on_delete=models.SET_NULL, related_name="task_without", blank=True, null=True)
    task_assemble = models.OneToOneField("Task", on_delete=models.SET_NULL, related_name="task_assemble", blank=True, null=True)
    task_gltf = models.OneToOneField("Task", on_delete=models.SET_NULL, related_name="task_gltf", blank=True, null=True)
    task_upload = models.OneToOneField("Task", on_delete=models.SET_NULL, related_name="task_upload", blank=True, null=True)

    def __str__(self):
        return self.project_name

    def save(self, *args, **kwargs):
        if self.project_type == "Villa":
            self.task_assemble = None
        super().save(*args, **kwargs)


@receiver(post_save, sender=Project)
def create_tasks(sender, instance, created, **kwargs):
    if created:
        task_with = Task.objects.create(
            task_type='with',
            project_task_name=instance.project_name
        )
        instance.task_with = task_with

        task_gltf = Task.objects.create(
            task_type='gltf',
            project_task_name=instance.project_name,
            project_id=instance.id
        )
        instance.task_gltf = task_gltf

        task_without = Task.objects.create(
            task_type='without',
            project_task_name=instance.project_name,
            project_id=instance.id
        )
        instance.task_without = task_without

        task_upload = Task.objects.create(
            task_type='upload',
            project_task_name=instance.project_name,
            project_id=instance.id
        )
        instance.task_upload = task_upload

        if instance.project_type != "Villa":
            task_assemble = Task.objects.create(
                task_type='assemble',
                project_task_name=instance.project_name,
                project_id=instance.id
            )
            instance.task_assemble = task_assemble

        instance.save()


class Task(models.Model):
    TASK_TYPE = (
        ('with', 'with'),
        ('without', 'without'),
        ('gltf', 'gltf'),
        ('assemble', 'assemble'),
        ('upload', 'upload'),
    )
    task_employee_user = models.ForeignKey(
        MyUser,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Employee'},
        related_name='task_employee_user',
        null=True,
        blank=True
    )
    task_correcting_employee_user = models.ForeignKey(
        MyUser,
        verbose_name='Пользователь Correcting',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Employee'},
        related_name='task_correcting_employee_user',
        null=True,
        blank=True
    )
    project_task_name = models.CharField(max_length=100, null=True, blank=True)
    project_id = models.CharField(max_length=100, null=True, blank=True)
    task_status = models.CharField(max_length=20, choices=STATUS, default=STATUS[0][0])
    task_type = models.CharField(max_length=20, choices=TASK_TYPE)
    unique_bedroom = models.CharField(max_length=100, null=True, blank=True)
    copy_bedroom = models.CharField(max_length=100, null=True, blank=True)
    in_progress_time = models.DateTimeField(null=True, blank=True)
    in_stock_active = models.DateTimeField(null=True, blank=True)
    checked_time = models.DateTimeField(null=True, blank=True)
    point = models.FloatField(null=True, blank=True)
    time_point = models.CharField(null=True, blank=True)
    correcting_point = models.FloatField(null=True, blank=True)
    time_correcting_point = models.CharField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    stock_active = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.project_task_name} -> {self.task_type}'


@receiver(pre_save, sender=Task)
def update_checked_time(sender, instance, **kwargs):
    if instance.pk is not None:
        original_task = Task.objects.get(pk=instance.pk)

        if original_task.task_status != instance.task_status:
            if instance.task_status == 'checked':
                instance.checked_time = timezone.now()
        if original_task.stock_active != instance.stock_active and instance.stock_active:
            instance.in_stock_active = timezone.now()
        if instance.task_status == 'In progress' and not instance.in_progress_time:
            instance.in_progress_time = timezone.now()


class Region(models.Model):
    name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.name
