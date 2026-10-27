import os
import django
from django.core.management import call_command

# Налаштовуємо середовище Django на використання локальної бази
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyShop.settings')

# Тимчасово примусово перемикаємо на sqlite3 у налаштуваннях перед ініціалізацією
from django.conf import settings
settings.DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'db.sqlite3',
}

django.setup()

# Робимо дамп у файл datadump.json
with open('datadump.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', natural_foreign=True, natural_primary=True, exclude=['contenttypes', 'auth.Permission'], indent=4, stdout=f)

print("УСПІХ! Дані успішно експортовано у datadump.json")