from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard & Tasks
    path('', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/update/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/toggle/', views.task_toggle, name='task_toggle'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/clear-completed/', views.clear_completed, name='clear_completed'),

    # Subtasks
    path('tasks/<int:task_pk>/subtasks/create/', views.subtask_create, name='subtask_create'),
    path('subtasks/<int:pk>/toggle/', views.subtask_toggle, name='subtask_toggle'),
    path('subtasks/<int:pk>/delete/', views.subtask_delete, name='subtask_delete'),

    # Categories
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
