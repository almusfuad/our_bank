#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
# sys.path.append(r"C:\Users\CS-D-42-16-104047\AppData\Local\Programs\Python\Python312\Lib\site-packages")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bank_management.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
