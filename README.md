# Coderr – Marketplace API Backend

A Django REST Framework backend for a modular marketplace and service platform.

## Features

- Custom user model (email login, Profile-Extension)
- Full CRUD for offers, orders, and reviews
- Token-based authentication (DRF TokenAuth)
- RESTful, filter- & sortierbare API-Endpunkte (DjangoFilter, Ordering)
- Aggregated/statistical meta endpoints
- Modular app structure: offers, orders, users, reviews
- Clean code: PEP8, max. 14 lines/method, all functions documented
- Admin interface for all objects
- Full pytest-based test coverage

---

## Quickstart (Local Setup)

### 1. **Clone the Repository**
```bash
git clone <dein-repo-link>
cd coderr
```

### 2. **Create & Activate Virtual Environment**

**Windows (CMD/PowerShell):**

```bash
python -m venv env
env\Scripts\activate
```

**Mac/Linux:**

```bash
python3 -m venv env
source env/bin/activate
```

### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 4. **Database Setup (SQLite)**

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. **Create Superuser (for admin interface)**

```bash
python manage.py createsuperuser
```

### 6. **Run Development Server**

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) to access the Django admin interface.

---

## Project Structure

```
coderr/                 # Project root (manage.py, requirements.txt, README.md, .gitignore, etc.)
core/                   # Main project settings, urls, wsgi, asgi, etc.
users_app/              # User model, profiles, registration, login, api/
offers_app/             # Offer logic (models, views, api/, tests)
orders_app/             # Orders logic (models, views, api/, tests)
reviews_app/            # Reviews logic (models, views, api/, tests)
```

---

## Notes

* **No database files are included** in the repository (see .gitignore).

* After cloning, always run migrations!

* The backend is decoupled: frontend is NOT part of this repo.

* All environment variables, secrets, and `.env` files should be handled securely and are not included.

* All code is **PEP8-compliant and documented**.

* To run all tests:

  ```bash
  pytest
  ```

* See Django Deployment Checklist for secure production setup.

---

## API Overview (selected)

| Method | Endpoint        | Description                    |
| ------ | --------------- | ------------------------------ |
| GET    | /api/offers/    | List all offers                |
| POST   | /api/offers/    | Create offer                   |
| GET    | /api/orders/    | List all orders                |
| POST   | /api/orders/    | Create order                   |
| GET    | /api/reviews/   | List all reviews               |
| POST   | /api/reviews/   | Create review (customer only)  |
| GET    | /api/base-info/ | Platform stats (meta endpoint) |
| POST   | /api/register/  | User registration              |
| POST   | /api/login/     | User login                     |

*(Alle weiteren Endpunkte und Query-Parameter sind in der API-Dokumentation im Projekt zu finden.)*

---

## License

MIT

---

## Support

Fragen?
Issues direkt im GitHub-Repo eröffnen – oder über das interne Supportboard der Developer Akademie.

```

---