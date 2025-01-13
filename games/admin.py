from django.contrib import admin

from .models import (Game, GameInstance, GameRental, GameReservation,
                     Notification)

admin.site.register(Game)
admin.site.register(GameInstance)
admin.site.register(GameRental)
admin.site.register(Notification)
admin.site.register(GameReservation)
