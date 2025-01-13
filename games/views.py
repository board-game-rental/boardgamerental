import base64
import csv
from datetime import date, timedelta
from io import BytesIO
from random import choice

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Min
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from .models import (Game, GameInstance, GameRental, GameReservation,
                     Notification)
from .tasks import send_notification


def games(request):
    p = Paginator(Game.objects.all().order_by("name"), 8)
    page = request.GET.get("page")
    game_list = p.get_page(page)
    low_stock_games = []
    if request.user.is_superuser:
        for game in Game.objects.all():
            available_count = GameInstance.objects.filter(
                game=game, is_available=True, is_reserved=False
            ).count()
            if available_count <= 3:
                low_stock_games.append(
                    {"game": game, "available_count": available_count}
                )
    context = {"game_list": game_list, "low_stock_games": low_stock_games}
    return render(request, "games/index.html", context)


def detail(request, game_name):
    game = Game.objects.get(name=game_name)
    user = request.user
    is_game_reserved = GameReservation.objects.filter(
        user=user.id, game_instance__game=game
    ).exists()
    if request.method == "POST":
        game_instance = GameInstance(game=game)
        game_instance.save()
    # zliczane sa tylko egzemplarze, ktore maja status dostepny
    game_instance_count = GameInstance.objects.filter(
        game=game, is_available=True, is_reserved=False
    ).count()
    game_reservation_count = GameInstance.objects.filter(
        game=game, is_available__in=[True, False], is_reserved=False
    ).count()
    available_games = Game.objects.filter(
        gameinstance__is_available=True, gameinstance__is_reserved=False
    ).distinct()
    if available_games.exists():
        random_game = choice(available_games)
    else:
        random_game = None
    context = {
        "game_name": game.name,
        "game_description": game.description,
        "game_instance_count": game_instance_count,
        "game_image": game.image.url,
        "game_reservation_count": game_reservation_count,
        "is_game_reserved": is_game_reserved,
        "random_game": random_game,
    }
    return render(request, "games/detail.html", context)


@login_required(login_url="/members/login")
def rental_info(request, game_name):
    user = request.user
    game = Game.objects.get(name=game_name)
    game_instance = GameInstance.objects.filter(
        game_id=game.id, is_available=True, is_reserved=False
    ).first()
    if game_instance is not None:
        current_date = date.today()
        return_date = get_next_monday(current_date)
        context = {
            "user": user,
            "game_name": game.name,
            "game_image": game.image.url,
            "game_id": game.id,
            "game_instance": game_instance.id,
            "current_date": current_date,
            "return_date": return_date,
        }
        return render(request, "games/rental_info.html", context)
    else:
        messages.error(
            request,
            "Brak dostępnych egzemplarzy, spróbuj ponownie później.",
            extra_tags="message_error",
        )
        return redirect("/")


@login_required(login_url="/members/login")
def rental_confirm(request, game_name):
    user = request.user
    game = Game.objects.get(name=game_name)
    game_instance = GameInstance.objects.filter(
        game_id=game.id, is_available=True, is_reserved=False
    ).first()
    rental_date = date.today()
    return_date = get_next_monday(rental_date)
    game_rental = GameRental(
        user=user,
        game_instance=game_instance,
        rental_date=rental_date,
        return_date=return_date,
    )
    if request.method == "POST":
        game_rental.save()
        game_instance.is_available = False
        game_instance.save()
        game.all_time_rentals += 1
        game.save()
        # KOD QR
        qr_data = f"ID wypożyczenia: {game_rental.id}\nGra: {game_instance.game.name}\nData zwrotu: {return_date}"
        qr_image = qrcode.make(qr_data)
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        game_rental.qr_code = qr_buffer.read()
        game_rental.save()
        messages.success(
            request,
            f"Wypożyczono pomyślnie, ID wypożyczenia: {game_rental.id}, data zwrotu: {return_date}",
            extra_tags="message_success",
        )
        return redirect("/")
    return redirect(rental_info, game_name=game_name)


@login_required(login_url="/members/login")
def user_rental(request):
    p = Paginator(GameRental.objects.filter(user=request.user).order_by("-id"), 2)
    page = request.GET.get("page")
    game_rental = p.get_page(page)

    def convert_image_to_base64(image):
        return base64.b64encode(image).decode("utf-8")

    for rental in game_rental:
        if rental.qr_code:
            rental.qr_code_base64 = convert_image_to_base64(rental.qr_code)
    return render(
        request,
        "games/user_rental.html",
        context={"game_rental": game_rental, "current_date": date.today()},
    )


# wypozyczenia od wszystkich uzytkownikow, widoczne tylko dla admina w celu potwierdzenia zwrotu
@login_required(login_url="/members/login")
def all_rentals(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    p = Paginator(GameRental.objects.all().order_by("id"), 2)
    page = request.GET.get("page")
    game_rental = p.get_page(page)
    return render(
        request, "games/all_rentals.html", context={"game_rental": game_rental}
    )


@login_required(login_url="/members/login")
def extend_rental(request, rental_id):
    game_rental = GameRental.objects.get(id=rental_id, user=request.user)
    if request.method == "POST":
        if game_rental.game_instance.is_reserved:
            messages.error(
                request,
                f"Nie możesz przedłużyć wypożyczenia tego egzemplarza, gdyż został on przez kogoś już zarezerwowany.",
                extra_tags="message_error",
            )
        elif not game_rental.is_extended:
            game_rental.return_date += timedelta(days=3)
            game_rental.is_extended = True
            game_rental.save()
            # KOD QR
            qr_data = f"ID wypożyczenia: {game_rental.id}\nGra: {game_rental.game_instance.game.name}\nData zwrotu: {game_rental.return_date}"
            qr_image = qrcode.make(qr_data)
            qr_buffer = BytesIO()
            qr_image.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            game_rental.qr_code = qr_buffer.read()
            game_rental.save()
            messages.success(
                request,
                f"Wypożyczenie o ID: {game_rental.id} zostało przedłużone do: {game_rental.return_date}",
                extra_tags="message_success",
            )
        else:
            messages.error(
                request,
                f"Wypożyczenie o ID: {game_rental.id} zostało juz przedłużone.",
                extra_tags="message_error",
            )
    page = request.GET.get("page", 1)
    return redirect(f"/user_rental?page={page}")


@login_required(login_url="/members/login")
def return_confirm(request, rental_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    game_rental = GameRental.objects.get(id=rental_id)
    game_instance = game_rental.game_instance
    if request.method == "POST":
        game_instance.is_available = True
        game_instance.save()
        game_rental.delete()
        reservation = GameReservation.objects.filter(
            game_instance=game_instance, 
            reservation_end_date__gte=now().date()
        ).first()
        if reservation:
            send_notification.delay(
                user_id=reservation.user.id,
                title="Twoja rezerwacja jest gotowa!",
                message=f"Gra {game_instance.game.name} jest teraz dostępna do wypożyczenia."
            )
        messages.success(
            request,
            f"Pomyślnie potwierdzono zwrot egzemplarza o ID: {game_instance.id}",
            extra_tags="message_success",
        )
        return redirect("all_rentals")
    # w przypadku otwarcia bezposrednio z linku wyswietlamy template z konkretnym egzemplarzem do potwierdzenia
    return render(
        request, "games/return_confirm.html", context={"game_rental": game_rental}
    )


@login_required(login_url="/members/login")
def notifications(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user).delete()
        messages.success(
            request,
            f"Wszystkie powiadomienia zostały usunięte.",
            extra_tags="message_success",
        )
        return redirect("notifications")
    p = Paginator(Notification.objects.filter(user=request.user).order_by("-id"), 10)
    page = request.GET.get("page")
    notifications = p.get_page(page)
    return render(
        request, "games/notifications.html", context={"notifications": notifications}
    )


@login_required(login_url="/members/login")
def notifications_detail(request, notification_id):
    notification = Notification.objects.get(user=request.user, id=notification_id)
    if request.method == "POST":
        notification.delete()
        messages.success(
            request, f"Powiadomienie zostało usunięte.", extra_tags="message_success"
        )
        return redirect(f"notifications")
    return render(
        request,
        "games/notifications_detail.html",
        context={
            "title": notification.title,
            "message": notification.message,
            "notification_id": notification.id,
        },
    )


@login_required(login_url="/members/login")
def reservation_info(request, game_name):
    user = request.user
    game = Game.objects.get(name=game_name)
    # przypadek, gdy sa dostepne egzemplarze
    game_instance = GameInstance.objects.filter(
        game_id=game.id, is_reserved=False, is_available=True
    ).first()
    is_game_reserved = GameReservation.objects.filter(
        user=user, game_instance__game=game
    ).exists()
    # sprawdzenie czy uzytkownik zarezerwowal juz dana gre, jesli tak to nie moze jej ponownie zarezerwowac
    if is_game_reserved:
        messages.error(
            request,
            "Ta gra została już przez ciebie zarezerwowana.",
            extra_tags="messages_error",
        )
        return redirect("/")
    if game_instance is not None:
        reservation_date = date.today()
        reservation_end_date = reservation_date + timedelta(days=3)
        context = {
            "user": user,
            "game_name": game.name,
            "game_image": game.image.url,
            "game_id": game.id,
            "game_instance": game_instance.id,
            "reservation_date": reservation_date,
            "reservation_end_date": reservation_end_date,
        }
        return render(request, "games/reservation_info.html", context)
    else:
        # przypadek, gdy nie ma dostepnych egzemplarzy, bierzemy wtedy egzemplarz z najblizsza data zwrotu
        nearest_return_date = GameRental.objects.filter(
            game_instance__game=game, game_instance__is_reserved=False
        ).aggregate(Min("return_date"))
        nearest_return_date_instance = GameRental.objects.filter(
            game_instance__game=game,
            game_instance__is_reserved=False,
            return_date=nearest_return_date["return_date__min"],
        ).first()
        if nearest_return_date_instance is not None:
            current_date = date.today()
            # rezerwacja jest mozliwa do wypozyczenia od poniedzialku, gdyz wtedy odbywaja sie zwroty wypozyczonych gier
            avaiable_rental_date = get_next_monday(current_date)
            reservation_date = current_date
            if nearest_return_date_instance.is_extended:
                avaiable_rental_date += timedelta(days=3)
            reservation_end_date = avaiable_rental_date + timedelta(days=3)
            game_instance = nearest_return_date_instance.game_instance
            messages.info(
                request,
                f"Uwaga! Gra nie została jeszcze zwrócona, wypożyczenie będzie możliwie dopiero od {avaiable_rental_date}.",
                extra_tags="message_info",
            )
            context = {
                "user": user,
                "game_name": game.name,
                "game_image": game.image.url,
                "game_id": game.id,
                "game_instance": game_instance.id,
                "reservation_date": reservation_date,
                "reservation_end_date": reservation_end_date,
            }
            return render(request, "games/reservation_info.html", context)
        else:
            messages.error(
                request,
                "Gra nie posiada żadnych egzemplarzy lub wszystkie są aktualnie zarezerwowane, spróbuj ponownie później.",
                extra_tags="message_error",
            )
            return redirect("/")


@login_required(login_url="/members/login")
def reservation_confirm(request, game_name):
    user = request.user
    game = Game.objects.get(name=game_name)
    # sprawdzenie czy uzytkownik ma juz rezerwacje na gre
    existing_reservation = GameReservation.objects.filter(
        user=user, game_instance__game=game
    ).first()
    if existing_reservation:
        messages.error(
            request,
            "Masz już aktywną rezerwację na tę grę i nie możesz jej ponownie zarezerwować.",
        )
        return redirect("/")
    # przypadek, gdy sa dostepne egzemplarze
    game_instance = GameInstance.objects.filter(
        game_id=game.id, is_reserved=False, is_available=True
    ).first()
    if game_instance is not None:
        reservation_date = date.today()
        reservation_end_date = reservation_date + timedelta(days=3)
        game_reservation = GameReservation(
            user=user,
            game_instance=game_instance,
            reservation_date=reservation_date,
            reservation_end_date=reservation_end_date,
        )
        if request.method == "POST":
            game_reservation.save()
            # game_instance.is_available = False
            game_instance.is_reserved = True
            game_instance.save()
            game.all_time_reservations += 1
            game.save()
            messages.success(
                request,
                mark_safe(
                    f"Zarezerwowano pomyślnie, ID rezerwacji: {game_reservation.id}<br>Pamiętaj, że czas na wypożyczenie zarezerwowanej gry wynosi tylko 3 dni, po tym czasie egzemplarz stanie się dostepny dla wszystkich!"
                ),
                extra_tags="message_success",
            )
            return redirect("/")
    else:
        # przypadek, gdy nie ma dostepnych egzemplarzy, bierzemy wtedy egzemplarz z najblizsza data zwrotu
        nearest_return_date = GameRental.objects.filter(
            game_instance__game=game, game_instance__is_reserved=False
        ).aggregate(Min("return_date"))
        nearest_return_date_instance = GameRental.objects.filter(
            game_instance__game=game,
            game_instance__is_reserved=False,
            return_date=nearest_return_date["return_date__min"],
        ).first()
        if nearest_return_date_instance is not None:
            current_date = date.today()
            # rezerwacja jest mozliwa do wypozyczenia od poniedzialku, gdyz wtedy odbywaja sie zwroty wypozyczonych gier
            available_rental_date = get_next_monday(current_date)
            reservation_date = current_date
            if nearest_return_date_instance.is_extended:
                available_rental_date += timedelta(days=3)
            reservation_end_date = available_rental_date + timedelta(days=3)
            game_instance = nearest_return_date_instance.game_instance
            game_reservation = GameReservation(
                user=user,
                game_instance=game_instance,
                reservation_date=reservation_date,
                reservation_end_date=reservation_end_date,
            )
            if request.method == "POST":
                game_reservation.save()
                game_instance.is_reserved = True
                game_instance.save()
                messages.success(
                    request,
                    mark_safe(
                        f"Zarezerwowano pomyślnie, ID rezerwacji: {game_reservation.id}<br>Pamiętaj, że czas na wypożyczenie zarezerwowanej gry wynosi tylko 3 dni, po tym czasie egzemplarz stanie się dostepny dla wszystkich! Czas twojej rezerwacji liczony będzie od {available_rental_date}, gdyż wypożyczona gra nie została jeszcze zwrócona."
                    ),
                    extra_tags="message_success",
                )
            return redirect("/")
    return redirect(reservation_info, game_name=game_name)


@login_required(login_url="/members/login")
def reservation_rental_info(request, reservation_id):
    user = request.user
    game_reservation = GameReservation.objects.get(user=user, id=reservation_id)
    game_instance = game_reservation.game_instance
    if game_instance.is_available:
        current_date = date.today()
        return_date = get_next_monday(current_date)
        context = {
            "user": user,
            "game_name": game_reservation.game_instance.game.name,
            "game_image": game_reservation.game_instance.game.image.url,
            "game_id": game_reservation.game_instance.game.id,
            "game_instance": game_reservation.game_instance.id,
            "current_date": current_date,
            "return_date": return_date,
            "reservation_id": reservation_id,
        }
        return render(request, "games/reservation_rental_info.html", context)
    messages.error(
        request,
        f"Gra nie została jeszcze zwrócona, spróbuj ponownie później.",
        extra_tags="messages_error",
    )
    return redirect("/")


@login_required(login_url="/members/login")
def reservation_rental_confirm(request, reservation_id):
    user = request.user
    game_reservation = GameReservation.objects.get(user=user, id=reservation_id)
    game_instance = game_reservation.game_instance
    if not game_instance.is_available:
        messages.error(
            request,
            f"Gra nie została jeszcze zwrócona, spróbuj ponownie później.",
            extra_tags="messages_error",
        )
        return redirect("/")
    rental_date = date.today()
    return_date = get_next_monday(rental_date)
    game_rental = GameRental(
        user=user,
        game_instance=game_instance,
        rental_date=rental_date,
        return_date=return_date,
    )
    if request.method == "POST":
        game_rental.save()
        game_instance.is_available = False
        game_instance.is_reserved = False
        game_reservation.delete()
        game_instance.save()
        game_instance.game.all_time_rentals += 1
        game_instance.game.save()
        # KOD QR
        qr_data = f"ID wypożyczenia: {game_rental.id}\nGra: {game_instance.game.name}\nData zwrotu: {return_date}"
        qr_image = qrcode.make(qr_data)
        qr_buffer = BytesIO()
        qr_image.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        game_rental.qr_code = qr_buffer.read()
        game_rental.save()
        messages.success(
            request,
            f"Wypożyczono pomyślnie, ID wypożyczenia: {game_rental.id}, data zwrotu: {return_date}",
            extra_tags="message_success",
        )
        return redirect("/")
    return redirect(reservation_rental_info, reservation_id=reservation_id)


@login_required(login_url="/members/login")
def user_reservation(request):
    user = request.user
    p = Paginator(GameReservation.objects.filter(user=user).order_by("-id"), 2)
    page = request.GET.get("page")
    game_reservation_page = p.get_page(page)
    if request.method == "POST":
        game_reservation_id = request.POST.get("reservation_id")
        game_reservation = GameReservation.objects.get(
            user=user, id=game_reservation_id
        )
        game_instance = game_reservation.game_instance
        game_instance.is_reserved = False
        game_instance.save()
        game_reservation.delete()
    return render(
        request,
        "games/user_reservation.html",
        context={
            "game_reservation": game_reservation_page,
            "current_date": date.today(),
        },
    )


@login_required(login_url="/members/login")
def rental_report(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="raport_wypozyczen.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Uzytkownik",
            "Egzemplarz gry",
            "Data wypozyczenia",
            "Data zwrotu",
            "Przedluzono",
        ]
    )
    rentals = GameRental.objects.all()
    for rental in rentals:
        writer.writerow(
            [
                rental.user.username,
                rental.game_instance,
                rental.rental_date,
                rental.return_date,
                rental.is_extended,
            ]
        )
    return response


@login_required(login_url="/members/login")
def reservation_report(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="raport_rezerwacji.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ["Uzytkownik", "Egzemplarz gry", "Data rezerwacji", "Data konca rezerwacji"]
    )
    reservations = GameReservation.objects.all()
    for reservation in reservations:
        writer.writerow(
            [
                reservation.user.username,
                reservation.game_instance,
                reservation.reservation_date,
                reservation.reservation_end_date,
            ]
        )
    return response


@login_required(login_url="/members/login")
def current_popular_games_report(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="raport_aktualnie_popularnych_gier.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["Gra", "Liczba wypozyczen", "Liczba rezerwacji", "Suma"])
    # zliczenie wypozyczen i rezerwacji dla kazdej gry
    games = Game.objects.all()
    report_data = []
    for game in games:
        rentals_count = GameRental.objects.filter(game_instance__game=game).count()
        reservations_count = GameReservation.objects.filter(
            game_instance__game=game
        ).count()
        total_count = rentals_count + reservations_count
        report_data.append((game.name, rentals_count, reservations_count, total_count))
    # najpopularniejsze gry na początku
    report_data.sort(key=lambda x: x[3], reverse=True)
    for game_name, rentals, reservations, total in report_data:
        writer.writerow([game_name, rentals, reservations, total])
    return response


@login_required(login_url="/members/login")
def all_time_popular_games_report(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        'attachment; filename="raport_popularnosci_gier_wszech_czasow.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(
        ["Gra", "Laczna liczba wypozyczen", "Laczna liczba rezerwacji", "Suma"]
    )
    games = Game.objects.all().order_by("-all_time_rentals", "-all_time_reservations")
    for game in games:
        total = game.all_time_rentals + game.all_time_reservations
        writer.writerow(
            [game.name, game.all_time_rentals, game.all_time_reservations, total]
        )
    return response


# zwrot zawsze w poniedzialek
def get_next_monday(date):
    days_ahead = 0 - date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = date + timedelta(days_ahead)
    return next_monday
