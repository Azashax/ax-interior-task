from rest_framework import serializers
import User.views
from .models import Project, Task, Region
from User.serializers import UserSerializer
from User.models import MyUser


class TaskSerializer(serializers.ModelSerializer):
    task_employee_user = UserSerializer()

    class Meta:
        model = Task
        fields = '__all__'


class TaskInProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'project_task_name', 'project_id', 'task_status', 'task_type', 'time_point', 'point', 'task_employee_user',
                  'stock_active', 'description']


class Task1Serializer(serializers.ModelSerializer):

    class Meta:
        model = Task
        fields = '__all__'


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['project_type', 'project_name', 'region', 'project_teg']
        ref_name = 'Project_add'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class ProjectlistSerializer(serializers.ModelSerializer):
    region = RegionSerializer()

    class Meta:
        model = Project
        fields = '__all__'
        ref_name = 'Projects'


class ProjectListGetSerializer(serializers.ModelSerializer):
    region = RegionSerializer()
    project_teamlead_user = UserSerializer()

    class Meta:
        model = Project
        fields = '__all__'
        ref_name = 'Projects'


class ProjectEmployeeSerializer(serializers.ModelSerializer):
    task_with = TaskInProgressSerializer()
    task_without = TaskInProgressSerializer()
    task_assemble = TaskInProgressSerializer()
    task_gltf = TaskInProgressSerializer()
    task_upload = TaskInProgressSerializer()
    region = RegionSerializer()
    # project_teamlead_user = UserSerializer()

    class Meta:
        model = Project
        fields = '__all__'
        ref_name = 'Project'


class ProjectDetailUpdateSerializer1(serializers.ModelSerializer):
    region = RegionSerializer()
    project_teamlead_user = UserSerializer()
    class Meta:
        model = Project
        fields = '__all__'
        ref_name = 'Project'


class ProjectDetailUpdateSerializer(serializers.ModelSerializer):
    region = RegionSerializer()

    class Meta:
        model = Project
        fields = '__all__'
        ref_name = 'Project'


def create_or_update_task(self, instance, task_data, task_type):
    task_instance, created = Task.objects.get_or_create(project=instance, task_type=task_type)
    task_serializer = TaskSerializer(instance=task_instance, data=task_data)
    if task_serializer.is_valid():
        task_serializer.save()


class ProjectSerializer(serializers.ModelSerializer):
    task_with = TaskSerializer()
    task_without = TaskSerializer()
    task_assemble = TaskSerializer()
    task_gltf = TaskSerializer()
    task_upload = TaskSerializer()
    region = RegionSerializer()
    project_teamlead_user = UserSerializer()

    class Meta:
        model = Project
        fields = '__all__'
        ref_name = 'Project'

    def create(self, validated_data):
        project = Project.objects.create(**validated_data)

        # Создание или обновление задач для всех типов
        for task_type in ['with', 'without', 'assemble', 'gltf', 'upload']:
            task_data = validated_data.pop(f'task_{task_type}', {})
            self.create_or_update_task(project, task_data, task_type)

        project.save()
        return project

    def update(self, instance, validated_data):
        instance = super(ProjectSerializer, self).update(instance, validated_data)

        # Создание или обновление задач для всех типов
        for task_type in ['with', 'without', 'assemble', 'gltf', 'upload']:
            task_data = validated_data.pop(f'task_{task_type}', {})
            self.create_or_update_task(instance, task_data, task_type)

        instance.save()
        return instance




