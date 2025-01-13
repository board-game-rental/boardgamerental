from django.contrib.auth.models import User
from django.db import models


class Game(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.FileField()
    all_time_rentals = models.PositiveIntegerField(
        default=0
    )  # Łączna liczba wypożyczeń
    all_time_reservations = models.PositiveIntegerField(
        default=0
    )  # Łączna liczba rezerwacji

    def __str__(self):
        return self.name


class GameInstance(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    is_reserved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.game.name} [{self.id}]"


class GameRental(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game_instance = models.ForeignKey(GameInstance, on_delete=models.CASCADE)
    rental_date = models.DateField()
    return_date = models.DateField()
    is_extended = models.BooleanField(default=False)
    qr_code = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} | {self.game_instance} | {self.return_date}"


class GameReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game_instance = models.ForeignKey(GameInstance, on_delete=models.CASCADE)
    reservation_date = models.DateField()
    reservation_end_date = models.DateField()

    def __str__(self):
        return f"{self.user} | {self.game_instance} | {self.reservation_date}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}"
