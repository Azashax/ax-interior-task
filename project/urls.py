from django.urls import path, include, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework.routers import DefaultRouter
from .views import *


urlpatterns = [
    path('projects/', ProjectAPIList.as_view()),
    path('project/create/', ProjectAPICreate.as_view()),
    path('project/<int:pk>/', ProjectAPIUpdate.as_view()),
    path('project/update/<int:pk>/', ProjectDetailAPIUpdate.as_view()),

    path('project/team-lead/list/', ProjectTeamLeadAPIList.as_view()),

    path('complete/', CompleteAPIList.as_view()),
    path('complete/<int:pk>/', CompleteUpdateAPIList.as_view()),

    path('stock/employee/', StockEmployeeAPIList.as_view()),
    path('stock/employee/<int:pk>/', StockAPIUpdateEmployee.as_view()),

    path('secure/', SecureTeamleadAPIList.as_view()),
    path('secure/<int:pk>/', SecureTeamleadUpdateAPI.as_view()),

    path('in-progress/', InProgressTeamleadAPIList.as_view()),

    # path('stock/create/', StockAPICreate.as_view()),
    # path('stock/<int:pk>/', StockAPIUpdate.as_view()),

]
