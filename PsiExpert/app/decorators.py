from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

ROLE_LABELS = {
    'client': 'клиента',
    'manager': 'менеджера',
    'admin': 'администратора',
}


def role_required(*roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            if profile is None or profile.role not in roles:
                need = ', '.join(ROLE_LABELS.get(role, role) for role in roles)
                messages.error(request, f'Страница доступна только для {need}.')
                return redirect('home')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
