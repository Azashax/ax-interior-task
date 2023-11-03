from django.urls import path
from .views import MyTokenObtainPairView, CustomUserCreateView, UserPermissionsView, UserProfileView\
    , UserTaskProjectView, UserListView, UserDetailView, UserDetailTaskView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


urlpatterns = [

    path('create/', CustomUserCreateView.as_view({'post': 'create', 'get': 'list'}), name='user_create'),
    path('update/<int:pk>/', UserPermissionsView.as_view(), name='user-permissions'),

    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('project-task/', UserTaskProjectView.as_view(), name='user_project_task'),

    path('users-list/', UserListView.as_view(), name='UserListView'),
    path('users-list/<int:pk>/', UserDetailView.as_view(), name='UserDetailView_detail'),
    path('users-list/task/<int:pk>/', UserDetailTaskView.as_view(), name='UserDetailView_detail_id'),

    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
