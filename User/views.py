from rest_framework import permissions
from rest_framework.response import Response
from djoser.views import UserViewSet
from rest_framework import generics
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAdminUser
from .models import MyUser, Teams
from .serializers import UserSerializer, ProjectTeamleadSerializer, UserTeamSerializer
from project.serializers import ProjectSerializer, TaskSerializer
from project.models import Task, Project
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, IsAuthenticated
from rest_framework import generics, viewsets, mixins, status
from django.db.models import Q, Avg, F
from datetime import datetime


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['role'] = user.role

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = MyUser.objects.all()
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user_id = pk

        # Определите поля заданий, которые вы хотите отслеживать (task_with, task_without и так далее)
        task_fields = ['task_with', 'task_without', 'task_assemble', 'task_gltf', 'task_upload']

        # Используйте Q-объект для создания условий для фильтрации проектов
        conditions = Q()
        for task_field in task_fields:
            conditions |= Q(**{f"{task_field}__task_employee_user_id": user_id, f"{task_field}__task_status": "checked"})

        projects_with_checked_tasks = Project.objects.filter(conditions)

        data = []

        for project in projects_with_checked_tasks:
            project_data = {
                'id': project.id,
                'project_name': project.project_name,
                'region': project.region.name,
            }

            for task_field in task_fields:
                if getattr(project, task_field) and getattr(project, task_field).task_status == 'checked':
                    project_data[task_field] = 1
                else:
                    project_data[task_field] = 0

            data.append(project_data)

        return Response(data, status=status.HTTP_200_OK)


# class UserDetailTaskView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request, pk):
#
#         user_id = pk
#         print(pk)
#         # Определите поля заданий, которые вы хотите отслеживать (task_with, task_without, и так далее)
#         task_fields = ['task_with', 'task_without', 'task_assemble', 'task_gltf', 'task_upload']
#
#         projects_with_desired_user = Project.objects.filter(
#             Q(task_with__task_employee_user=user_id) |
#             Q(task_without__task_employee_user=user_id) |
#             Q(task_assemble__task_employee_user=user_id) |
#             Q(task_gltf__task_employee_user=user_id) |
#             Q(task_upload__task_employee_user=user_id)
#         )
#         projects_with_checked_tasks = []
#         for project in projects_with_desired_user:
#             if (project.task_with and project.task_with.task_status == 'checked') or \
#                     (project.task_without and project.task_without.task_status == 'checked') or \
#                     (project.task_assemble and project.task_assemble.task_status == 'checked') or \
#                     (project.task_gltf and project.task_gltf.task_status == 'checked') or \
#                     (project.task_upload and project.task_upload.task_status == 'checked'):
#                 projects_with_checked_tasks.append(project)
#
#         data = []
#
#         for project in projects_with_checked_tasks:
#             project_data = {
#                 'id': project.id,
#                 'project_name': project.project_name,
#                 'region': project.region.name,
#             }
#
#             for task_field in task_fields:
#                 task = getattr(project, task_field)
#                 if task and task.task_status == 'checked':
#                     project_data[task_field] = 1
#                 else:
#                     project_data[task_field] = 0
#
#             data.append(project_data)
#             print(data)
#         return Response(data, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        current_date = datetime.now()
        current_month = current_date.month
        # user = get_object_or_404(MyUser, id=pk)
        user = MyUser.objects.get(id=pk)
        # Фильтруем задачи для данного пользователя с статусом "checked"
        avg_point = Task.objects.filter(task_employee_user=user, task_status='checked')

        # Фильтруем задачи для текущего месяца и аннотируем средний балл за месяц
        avg_point_month = avg_point.filter(checked_time__month=current_month)

        # Получаем средний балл для всех задач и задач для текущего месяца
        avg_point_data = avg_point.aggregate(average_point=Avg(F('point')))
        month_avg_point_data = avg_point_month.aggregate(average_point=Avg(F('point')))

        avg_point_1 = round(avg_point_data['average_point'] or 0, 2)
        month_avg_point = round(month_avg_point_data['average_point'] or 0, 2)

        # Добавляем средний балл и другие данные в данные пользователя
        serializer = UserSerializer(user)
        data = serializer.data
        data['avg_point'] = avg_point_1
        data['month_point'] = month_avg_point
        data['count_task'] = avg_point.count()

        return Response(data, status=status.HTTP_200_OK)


class CustomUserCreateView(UserViewSet):

    def get(self, request):
        if request.user.role == "Admin":
            projects = MyUser.objects.all()
            serializer = UserSerializer(projects, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "у вась не достаточно прав"},
                            status=status.HTTP_403_FORBIDDEN)

    def create(self, request, *args, **kwargs):
        if self.request.user.role == 'Admin':
            username = request.data.get('username')
            password = request.data.get('password')  # Предполагается, что пароль передается в запросе
            user = MyUser.objects.create_user(username=username, password=password)
            # Добавьте остальные поля пользователя
            return Response({"detail": "Пользователь успешно создан."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": "Только Admin могут регистрировать новых пользователей."},
                            status=status.HTTP_403_FORBIDDEN)


class UserPermissionsView(generics.RetrieveUpdateAPIView):
    queryset = MyUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_date = datetime.now()
        current_month = current_date.month
        user = request.user
        serializer = UserSerializer(user)
        if user.role == "Employee":
            # Фильтруем задачи для данного пользователя с статусом "checked" и аннотируем средний балл
            avg_point = Task.objects.filter(task_employee_user=user, task_status='checked')

            # Фильтруем задачи для текущего месяца и аннотируем средний балл за месяц
            avg_point_month = avg_point.filter(checked_time__month=current_month)

            # Получаем средний балл для всех задач
            count_task = avg_point.count() or 0

            avg_point = avg_point.aggregate(average_point=Avg(F('point')))['average_point'] or 0
            month_avg_point = avg_point_month.aggregate(average_point=Avg(F('point')))['average_point'] or 0

            # Добавляем средний балл в данные пользователя
            data = serializer.data
            data['avg_point'] = round(avg_point, 2)
            data['month_point'] = round(month_avg_point, 2)
            data['count_task'] = count_task
            print(data)
            return Response(data, status=status.HTTP_200_OK)
        elif user.role == "Teamlead":
            user = request.user
            try:
                team = Teams.objects.get(teamlead=user)
            except Teams.DoesNotExist:
                raise NotFound("У вас нет группы")
            team_members = team.employees.values_list('id', flat=True)
            team_members1 = MyUser.objects.filter(id__in=team_members)
            user_serializer = UserTeamSerializer(team_members1, many=True)
            data = {
                "profile1": serializer.data,
                "teams1": user_serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)


class UserTaskProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == "Teamlead":
            projects = Project.objects.filter(project_teamlead_user=request.user)
            serializer = ProjectTeamleadSerializer(projects, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.user.role == "Employee":
            desired_user_id = request.user.id

            # Определите поля заданий, которые вы хотите отслеживать (task_with, task_without, и так далее)
            task_fields = ['task_with', 'task_without', 'task_assemble', 'task_gltf', 'task_upload']

            projects_with_desired_user = Project.objects.filter(
                Q(task_with__task_employee_user_id=desired_user_id) |
                Q(task_without__task_employee_user_id=desired_user_id) |
                Q(task_assemble__task_employee_user_id=desired_user_id) |
                Q(task_gltf__task_employee_user_id=desired_user_id) |
                Q(task_upload__task_employee_user_id=desired_user_id)
            )
            projects_with_checked_tasks = []
            for project in projects_with_desired_user:
                if (project.task_with and project.task_with.task_status == 'checked') or \
                       (project.task_without and project.task_without.task_status == 'checked') or \
                       (project.task_assemble and project.task_assemble.task_status == 'checked') or \
                       (project.task_gltf and project.task_gltf.task_status == 'checked') or \
                       (project.task_upload and project.task_upload.task_status == 'checked'):
                    projects_with_checked_tasks.append(project)

            data = []

            for project in projects_with_checked_tasks:
                project_data = {
                    'id': project.id,
                    'project_name': project.project_name,
                    'region': project.region.name,
                }

                for task_field in task_fields:
                    task = getattr(project, task_field)
                    if task and task.task_status == 'checked':
                        project_data[task_field] = 1
                    else:
                        project_data[task_field] = 0

                data.append(project_data)
                print(data)
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "У вас недостаточно прав"}, status=status.HTTP_403_FORBIDDEN)


class TeamsCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, format=None):
        serializer = TeamsSerializer(data=request.data)
        if serializer.is_valid():
            teamlead = serializer.validated_data.get('teamlead')
            if teamlead and Teams.objects.filter(teamlead=teamlead).exists():
                return Response({"error": "Teamlead already has a team."}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

