from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('', views.index, name='home'),
    path('index.html', views.index, name='index_html'),
    path('time', views.time_view, name='time'),
    path('sum', views.sum_view, name='sum'),
    path('new', views.new_user, name='new_user'),
    path('createUser', views.createUser, name='create_user'),
    path('accounts/', include('django.contrib.auth.urls')),  
    path('new_course', views.new_course, name='new_course'),
    path('new_lecture', views.new_lecture, name='new_lecture'),
    path('new_qr_upload', views.new_qr_upload, name='new_qr_upload'),
]
