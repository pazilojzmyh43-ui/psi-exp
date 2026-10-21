#!/usr/bin/env python
"""Точка входа Django. В Visual Studio 2022 этот файл указан как StartupFile."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PsiExpert.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Не удалось импортировать Django. Установите зависимости: pip install -r requirements.txt'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
