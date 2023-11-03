from rest_framework import permissions


class ProjectListPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        # Разрешаем доступ только аутентифицированным пользователям.
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Проверяем роль пользователя и метод запроса.
        if request.user.role != 'Employee' and request.method == 'PATCH' and request.method == 'PUT':
            # Разрешаем админам доступ к объектам для PUT и PATCH запросов.
            return True
        # По умолчанию запрещаем доступ.
        return False


class IsEmployeeWithStatusChangeOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Разрешить доступ только для методов PATCH (изменение)
        if request.method == 'PATCH':
            # Пользователи с ролью "Employee" могут изменять только поле 'task_status'
            if request.user.role == "Employee":
                fields_being_updated = request.data.keys()
                return 'task_status' in fields_being_updated and len(fields_being_updated) == 1
            # Пользователи с ролью "Teamlead" могут изменять поле 'stock_active'
            elif request.user.role == "Teamlead":
                fields_being_updated = request.data.keys()
                return 'stock_active' in fields_being_updated and len(fields_being_updated) == 1
        return False


class IsAuth(permissions.BasePermission):

    def has_permission(self, request, view):
        # Разрешаем доступ только аутентифицированным пользователям.
        return request.user.is_authenticated
