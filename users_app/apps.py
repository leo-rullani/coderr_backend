from django.apps import AppConfig

class UsersAppConfig(AppConfig):
    name = "users_app"

    def ready(self):
        # Signal‑Registration beim App‑Start
        import users_app.signals  # noqa: F401
