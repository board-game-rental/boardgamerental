<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/board-game-rental/boardgamerental">
    <img src="static/games/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Wypożyczalnia Gier Planszowych</h3>

  <p align="center">
    Wygodne wypożyczanie i rezerwowanie gier planszowych w kilka kliknięć
  </p>
</div>

<!-- ABOUT THE PROJECT -->
## O projekcie
<strong>Wypożyczalnia Gier Planszowych</strong> to platforma umożliwiająca użytkownikom wypożyczanie gier planszowych na określony czas. 
Użytkownicy mogą przeglądać dostępne gry, dokonywać ich rezerwacji, wypożyczać je, a także zarządzać swoimi wypożyczeniami. System obsługuje
rejestrację użytkowników, logowanie, oraz automatyczne powiadomienia o zbliżającym się terminie zwrotu gry.

### Główne technologie
Backend aplikacji został zbudowany z wykorzystaniem frameworka Django, który obsługuje logikę aplikacji i zarządzanie danymi. Do przechowywania danych używana jest relacyjna baza danych PostgreSQL,
która zapewnia wysoką wydajność i niezawodność. Za frontend odpowiada między innymi Bootstrap – popularny framework CSS umożliwiający tworzenie responsywnych i estetycznych interfejsów użytkownika.

[![Django][django]][django-url]
[![Bootstrap][bootstrap]][bootstrap-url]
[![PostgreSQL][postgresql]][postgresql-url]

### Demo strony

Działające demo strony jest dostępne pod adresem http://51.83.132.99:8000/.

W celu zalogowania na konto administratora należy użyć loginu `admin` oraz hasła `admin`.

<!-- GETTING STARTED -->
## Pierwsze kroki

### Warunki wstępne
Do uruchomienia projektu wymagane jest posiadanie zainstalowanego Dockera oraz Docker Compose. Obie rzeczy najłatwiej zainstalować dzięki [Docker Desktop](https://docs.docker.com/get-started/get-docker/).

### Uruchomienie projektu

1. Sklonuj repozytorium
   ```sh
   git clone https://github.com/board-game-rental/boardgamerental.git
   ```
1. Przejdź do folderu repozytorium
   ```sh
   cd boardgamerental/
   ```
2. Uruchom projekt za pomocą Docker Compose
   ```sh
   docker compose up -d
   ```
Po wykonaniu powyższych kroków strona powinna już działać i być dostępna pod adresem http://localhost:8000, niemniej jednak zalecane jest jeszcze wykonanie dodatkowych kroków po uruchomieniu aplikacji.

### Po uruchomieniu (zalecane)

1. Wejdź w tryb exec kontenera ze stroną
   ```sh
   docker exec -it boardgamerental-web-1 /bin/bash
   ```
2. Skopiuj pliki statyczne
   ```sh
   python manage.py collectstatic --noinput
   ```
3. Stwórz konto administratora
   ```sh
   python manage.py createsuperuser
   ```
Wykonanie powyższych kroków sprawi, że skopiowane zostaną pliki statyczne i strona będzie się wyświetlać poprawnie. Utworzenie konta administratora umożliwi zarządzanie stroną poprzez panel administracyjny.

[django]: https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green
[django-url]: https://www.djangoproject.com/
[bootstrap]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[bootstrap-url]: https://getbootstrap.com/
[postgresql]: https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white
[postgresql-url]: https://www.postgresql.org/
