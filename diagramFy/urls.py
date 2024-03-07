from django.contrib import admin
from django.urls import path

from umlgenerator import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('uml-generator', views.umlGenerator)
]
