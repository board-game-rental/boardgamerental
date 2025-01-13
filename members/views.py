from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import RegisterUserForm


def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            messages.error(request, "Wystąpił błąd, spróbuj ponownie.")
            return redirect("login")
    else:
        return render(request, "authenticate/login.html", {})


def logout_user(request):
    logout(request)
    messages.success(request, "Wylogowano pomyślnie.", extra_tags="message_success")
    return redirect("/")


def register_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(
                request, "Zarejestrowano pomyślnie.", extra_tags="message_success"
            )
            return redirect("/")
    else:
        form = RegisterUserForm()

    return render(
        request,
        "authenticate/register.html",
        {
            "form": form,
        },
    )
