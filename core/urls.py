from django.urls import path
from . import views
urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("predict/", views.predict_view, name="predict"),
]
