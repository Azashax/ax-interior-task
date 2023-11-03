from rest_framework import serializers
from .models import MyUser
from project.models import Task, Project, Region


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'username', 'role', 'first_name', 'last_name', 'phone_number', 'link_telegram']
        ref_name = 'DjoserUser'


class UserTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'first_name', 'last_name']
        ref_name = 'DjoserUser1'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['name']


class ProjectTeamleadSerializer(serializers.ModelSerializer):
    region = RegionSerializer()

    class Meta:
        model = Project
        fields = ('id', 'project_name', 'region', 'built', 'exterior_status')
