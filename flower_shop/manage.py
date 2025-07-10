import os
import sys
from pathlib import Path

# Решение для импорта из корня проекта
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_shop.settings')
    try:

        # Инициализация Django ПЕРЕД импортом бота
        import django
        django.setup()  # <-- Это ключевая строка!

        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Добавьте эту часть
    if sys.argv[1] == 'runbot':
        from bot import start_bot
        start_bot()
    else:
        execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()