from django.urls import path, include
from core import views
from knox import views as knox_views

urlpatterns = [
	path('api/', views.GenesisRest.as_view()),
	path('api/media/', views.MediaRest.as_view()),
	path('blog/', views.GenesisAPI.as_view()),
	path('auth/knox/', include('knox.urls')),
	path('auth/login/', views.GenesisAPI.as_view()),
	path('auth/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
	path('auth/register/',  views.GenesisAPI.as_view()),
]
