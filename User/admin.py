from django.contrib import admin
from .models import MyUser, Teams
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin


@admin.register(MyUser)
class CustomUserAdmin(UserAdmin, ImportExportModelAdmin):
    model = MyUser
    list_display = ('id', 'username', 'role', 'first_name', 'last_name', 'is_active')
    fieldsets = (
        ('User', {'fields': ('username', 'password', 'role', 'task_point')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'link_telegram',
                                      'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
    )


@admin.register(Teams)
class TeamsAdmin(ImportExportModelAdmin):
    model = Teams
    list_display = ('id', 'name')



