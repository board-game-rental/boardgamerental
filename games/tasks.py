from datetime import date, datetime

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail

from .models import GameRental, GameReservation, Notification


def rental_notifications():
    # wszystkie wypozyczenia, zeby latwo mozna bylo to przetestowac
    rental_reminder = GameRental.objects.all()
    users = set(rental.user for rental in rental_reminder)
    notifications = {}
    for user in users:
        user_rentals = rental_reminder.filter(user=user)
        notif_list = []
        for rental in user_rentals:
            if date.today() > rental.return_date:
                # kara za spoznenie = ilosc dni po dacie zwrotu * 15 zł
                penalty = (date.today() - rental.return_date).days * 15
                notif_list.append(
                    f"{rental.game_instance.game.name} - Data zwrotu: {rental.return_date} - Kara za spóźnienie: {penalty} zł"
                )
            else:
                notif_list.append(
                    f"{rental.game_instance.game.name} - Data zwrotu: {rental.return_date}"
                )
        if notif_list:
            # klucz - nazwa uzytkownika, wartosc - wypozyczenia
            notifications[user] = "\n".join(notif_list)
    return notifications


@shared_task
def send_notification(user_id, title, message):
    Notification.objects.create(user_id=user_id, title=title, message=message)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return
    email_from = settings.EMAIL_HOST_USER
    recipient = [user.email]
    send_mail(
        subject=title,
        message=message,
        from_email=email_from,
        recipient_list=recipient,
    )


@shared_task
def send_email_reminder():
    notifications = rental_notifications()
    for user, notification in notifications.items():
        if notification:
            subject = "Przypomnienie o zwrocie wypożyczonych gier"
            message = f"Kończy się termin wypożyczenia gier, pamiętaj o ich zwrocie, w przeciwnym razie naliczane będą kary.\n\nLista gier:\n{notification}"
            email_from = settings.EMAIL_HOST_USER
            recipient = [user.email]
            send_mail(subject, message, email_from, recipient)


@shared_task
def send_notification_reminder():
    notifications = rental_notifications()
    for user, notification in notifications.items():
        if notification:
            title = f'Przypomnienie o zwrocie wypożyczonych gier - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            message = f"Kończy się termin wypożyczenia gier, pamiętaj o ich zwrocie, w przeciwnym razie naliczane będą kary.\n\nLista gier:\n{notification}"
            Notification.objects.create(user=user, title=title, message=message)


@shared_task
def remove_expired_reservations():
    today_date = date.today()
    expired_reservations = GameReservation.objects.filter(
        reservation_end_date__lt=today_date
    )
    for reservation in expired_reservations:
        title = (
            f"Koniec terminu rezerwacji - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        message = f"Informujemy, że termin rezerwacji gry {reservation.game_instance.game.name} dobiegł końca. Od tej chwili jest ona dostępna dla wszystkich."
        Notification.objects.create(user=reservation.user, title=title, message=message)
        game_instance = reservation.game_instance
        reservation.delete()
        game_instance.is_reserved = False
        game_instance.save()
