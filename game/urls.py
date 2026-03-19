from django.urls import path
from . import views

urlpatterns = [
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
    path('offline/', views.offline, name='offline'),
    path('', views.home, name='home'),
    path('start/', views.start_game, name='start_game'),
    path('play/', views.play, name='play'),
    path('room/create/', views.create_room, name='create_room'),
    path('room/join/', views.join_room, name='join_room'),
    path('room/<str:code>/', views.room, name='room'),
    path('api/guess/', views.api_guess, name='api_guess'),
    path('api/save-score/', views.api_save_score, name='api_save_score'),
    path('api/new-round/', views.api_new_round, name='api_new_round'),
    path('api/set-ui-language/', views.api_set_ui_language, name='api_set_ui_language'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/room/<str:code>/state/', views.api_room_state, name='api_room_state'),
    path('api/room/<str:code>/ready/', views.api_room_ready, name='api_room_ready'),
    path('api/room/<str:code>/start/', views.api_room_start, name='api_room_start'),
    path('api/room/<str:code>/next-round/', views.api_room_next_round, name='api_room_next_round'),
    path('api/room/<str:code>/guess/', views.api_room_guess, name='api_room_guess'),
    path('api/room/<str:code>/leave/', views.api_room_leave, name='api_room_leave'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('history/', views.history, name='history'),
]
