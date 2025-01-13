"""
URL configuration for boardgamerental project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.games, name="games"),
    path("detail/<str:game_name>", views.detail, name="detail"),
    path("rental_info/<str:game_name>", views.rental_info, name="rental_info"),
    path(
        "rental_confirm/<str:game_name>/", views.rental_confirm, name="rental_confirm"
    ),
    path("user_rental", views.user_rental, name="user_rental"),
    path("extend_rental/<int:rental_id>/", views.extend_rental, name="extend_rental"),
    path(
        "return_confirm/<int:rental_id>/", views.return_confirm, name="return_confirm"
    ),
    path("all_rentals/", views.all_rentals, name="all_rentals"),
    path("notifications", views.notifications, name="notifications"),
    path(
        "notifications/<int:notification_id>",
        views.notifications_detail,
        name="notifications_detail",
    ),
    path(
        "reservation_info/<str:game_name>",
        views.reservation_info,
        name="reservation_info",
    ),
    path(
        "reservation_confirm/<str:game_name>",
        views.reservation_confirm,
        name="reservation_confirm",
    ),
    path("user_reservation", views.user_reservation, name="user_reservation"),
    path(
        "reservation_rental_info/<int:reservation_id>",
        views.reservation_rental_info,
        name="reservation_rental_info",
    ),
    path(
        "reservation_rental_confirm/<int:reservation_id>",
        views.reservation_rental_confirm,
        name="reservation_rental_confirm",
    ),
    path("rental_report/", views.rental_report, name="rental_report"),
    path("reservation_report/", views.reservation_report, name="reservation_report"),
    path(
        "current_popular_games_report/",
        views.current_popular_games_report,
        name="current_popular_games_report",
    ),
    path(
        "all_time_popular_games_report/",
        views.all_time_popular_games_report,
        name="all_time_popular_games_report",
    ),
]
