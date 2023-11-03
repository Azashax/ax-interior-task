from rest_framework import generics, viewsets, mixins, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Project, Task
from .serializers import ProjectSerializer, ProjectCreateSerializer, ProjectlistSerializer, TaskSerializer, \
    Task1Serializer, TaskInProgressSerializer, ProjectDetailUpdateSerializer, ProjectDetailUpdateSerializer1
from .permissions import ProjectListPermission, IsEmployeeWithStatusChangeOnly, IsAuth
from django.db.models import Case, When, Value, CharField, Q
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from User.models import Teams, MyUser
from rest_framework.exceptions import NotFound
from User.serializers import UserTeamSerializer, UserSerializer


class StockAPIUpdateEmployee(APIView):
    permission_classes = [IsAuthenticated, ] #IsEmployeeWithStatusChangeOnly

    def get(self, request, pk):
        task = get_object_or_404(Task, id=pk)
        user = self.request.user
        if task.task_employee_user == user and task.stock_active:
            serializer = TaskSerializer(task)
            return Response(serializer.data)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        task = get_object_or_404(Task, id=pk)
        serializer = TaskInProgressSerializer(task, data=request.data, partial=True)
        print(request.data)
        if serializer.is_valid():
            serializer.save()
            print(serializer.data)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StockEmployeeAPIList(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        user = self.request.user

        # Используйте Q-объект для объединения условий фильтрации
        tasks = Task.objects.filter(
            Q(time_point__isnull=False) &
            Q(point__isnull=False) &
            Q(stock_active=True) &
            Q(task_employee_user=user)
        ).select_related('task_employee_user')

        # Добавляем временное поле для сортировки, чтобы сначала шли "in progress", а затем остальные
        tasks = tasks.annotate(
            sorting_status=Case(
                When(task_status='in progress', then=Value('A')),
                default=Value('B'),
                output_field=CharField(),
            ),
        ).order_by('in_stock_active')

        earliest_task = tasks.first()

        if earliest_task:
            earliest_task.task_status = 'in progress'
            earliest_task.save()

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SecureTeamleadUpdateAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        task = get_object_or_404(Task, id=pk)
        serializer = Task1Serializer(task)
        return Response(serializer.data)

    def patch(self, request, pk):
        task = get_object_or_404(Task, id=pk)

        # Преобразование 'task_employee_user' в число, если это строка
        task_employee_user = request.data.get('task_employee_user')
        if task_employee_user is not None and not isinstance(task_employee_user, int):
            try:
                task_employee_user = int(task_employee_user)
            except ValueError:
                return Response({"task_employee_user": "Некорректное значение"}, status=status.HTTP_400_BAD_REQUEST)
        request.data['task_employee_user'] = task_employee_user
        serializer = Task1Serializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InProgressTeamleadAPIList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        try:
            team = Teams.objects.get(teamlead=user)
        except Teams.DoesNotExist:
            raise NotFound("У вас нет группы")

        team_members = team.employees.values_list('id', flat=True)

        users = MyUser.objects.filter(id__in=team_members)
        user_serializer = UserSerializer(users, many=True)

        data = user_serializer.data

        for user_data in data:
            tasks = Task.objects.filter(
                task_employee_user=user_data['id'],
                time_point__isnull=False,
                point__isnull=False,
                stock_active=True,
                task_status__in=["open", "correcting", "waiting", "in progress"],
            )
            tasks1 = tasks.annotate(
                sorting_status=Case(
                    When(task_status='in progress', then=Value('A')),
                    default=Value('B'),
                    output_field=CharField(),
                ),
            ).order_by('sorting_status')
            task_serializer = TaskInProgressSerializer(tasks1, many=True)
            user_data['array'] = task_serializer.data

        return Response(data, status=status.HTTP_200_OK)


class SecureTeamleadAPIList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        try:
            team = Teams.objects.get(teamlead=user)
        except Teams.DoesNotExist:
            raise NotFound("У вас нет группы")

        team_members = team.employees.values_list('id', flat=True)

        projects1 = Task.objects.filter(
            time_point__isnull=False,
            point__isnull=False,
            stock_active=False,
            task_status__in=["open", "correcting", "waiting"],
            task_employee_user__in=team_members
        )

        projects = Task.objects.filter(
            time_point__isnull=False,
            point__isnull=False,
            stock_active=False,
            task_status="open",
        )

        # secure = MyUser.objects.filter(role="Employee")
        serializer1 = TaskSerializer(projects1, many=True)
        serializer = TaskSerializer(projects, many=True)
        team_members1 = MyUser.objects.filter(id__in=team_members)
        user_serializer = UserTeamSerializer(team_members1, many=True)
        data = {
            "tasks_open": serializer.data,
            "tasks": serializer1.data,
            "team_members": user_serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)


class CompleteAPIList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        team = Teams.objects.filter(teamlead=user).first()
        if team:
            team_members = team.employees.values_list('id', flat=True)
            projects = Task.objects.filter(
                time_point__isnull=False,
                point__isnull=False,
                stock_active=False,
                task_status="complete",
                task_employee_user__in=team_members  # Фильтруйте задачи по списку идентификаторов пользователей
            )
            serializer = TaskSerializer(projects, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("У вас нет Группы", status=status.HTTP_403_FORBIDDEN)


class CompleteUpdateAPIList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        task = get_object_or_404(Task, id=pk)  # Используйте get_object_or_404
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    def patch(self, request, pk):
        task = get_object_or_404(Task, id=pk)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if serializer.validated_data.get('task_status') == "checked":
                user_id = serializer.data.get('task_employee_user')['id']
                try:
                    user = MyUser.objects.get(id=user_id)
                    task_points = task.point  # Define how task points are stored in your model
                    user.task_point += task_points  # Update user points based on the task points
                    user.save()  # Save the updated user points
                    print("User found:", user)
                    print("User's points updated to:", user.task_point)
                except MyUser.DoesNotExist:
                    print("User not found for id:", user_id)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectAPIUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        project = get_object_or_404(Project, id=pk)  # Используйте get_object_or_404
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    def patch(self, request, pk):
        project = get_object_or_404(Project, id=pk)
        for key in request.data.keys():
            parts = key.split("_")
            if len(parts) > 1:
                task_type = parts[1]

                task = Task.objects.get(project_task_name=project.project_name, task_type=task_type)
                serializer = Task1Serializer(task, data=request.data[key], partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response("Задачи успешно обновлены", status=status.HTTP_200_OK)


class ProjectDetailAPIUpdate(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        project = get_object_or_404(Project, id=pk)  # Используйте get_object_or_404
        serializer = ProjectDetailUpdateSerializer1(project)
        return Response(serializer.data)

    def patch(self, request, pk):
        project = get_object_or_404(Project, id=pk)
        serializer = ProjectDetailUpdateSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response("project успешно обновлены", status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# делаеть поиск "соответствуют любому из этих трех критериев поиска"
class ProjectAPIList(generics.ListAPIView):
    """Вывод списка проектов"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.role != "Employee":
            projects = Project.objects.all()
            search_query = request.query_params.get('project-name', None)
            if search_query:
                projects = projects.filter(
                    Q(project_name__istartswith=search_query)
                )
            projects_p = projects.annotate(
                sorting_status=Case(
                    When(project_teg='High priority', then=Value('A')),
                    When(project_teg='Priority', then=Value('B')),
                    default=Value('C'),
                    output_field=CharField(),
                ),
            ).order_by('sorting_status')
            serializer = ProjectlistSerializer(projects_p, many=True)

            return Response(serializer.data)
        else:
            return Response("У вас нет прав для выполнения этой операции", status=status.HTTP_403_FORBIDDEN)


class ProjectTeamLeadAPIList(generics.ListAPIView):
    """Вывод списка проектов"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.role != "Employee":

            projects = Project.objects.filter(
                Q(project_teamlead_user__isnull=True) &
                Q(project_teamlead_user=request.user))

            search_query = request.query_params.get('project-name', None)
            if search_query:
                projects.filter(
                    Q(project_name__istartswith=search_query)
                )

            serializer = ProjectlistSerializer(projects_p, many=True)

            return Response(serializer.data)
        else:
            return Response("У вас нет прав для выполнения этой операции", status=status.HTTP_403_FORBIDDEN)


class ProjectAPICreate(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if request.user.role != "Admin":
            return Response("У вас нет прав для выполнения этой операции", status=status.HTTP_403_FORBIDDEN)

        serializer = ProjectCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


