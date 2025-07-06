from django.apps import AppConfig

class UsersAppConfig(AppConfig):
    name = "users_app"

    def ready(self):
        # Signal‑Registration
        import users_app.signals  # noqa: F401
