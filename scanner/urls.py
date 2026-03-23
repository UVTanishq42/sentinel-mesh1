from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("scan-link/", views.scan_link, name="scan_link"),
    path("api/check-link/", views.api_check_link, name="api_check_link"),
    path("accounts/signup/", views.signup, name="signup"),
]

