from django.contrib import admin
from .models import Project, Region, Task
from import_export.admin import ImportExportModelAdmin


@admin.register(Region)
class RegionAdmin(ImportExportModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name', )


@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    list_display = ('id', 'project_name', 'project_type', 'project_teamlead_user', 'built',
                    'project_teg', 'exterior_status', 'project_status')
    search_fields = ('project_name', )


@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin):
    list_display = ('id', 'project_task_name', 'task_type', 'task_status', 'stock_active',
                    'task_employee_user', 'task_correcting_employee_user', 'description')
    search_fields = ('project_task_name', )
