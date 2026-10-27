from django.apps import AppConfig

class UsersConfig(AppConfig): # Назва класу може відрізнятися
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Users' # Назва вашого додатку

