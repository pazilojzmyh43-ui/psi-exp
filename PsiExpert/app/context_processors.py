from .company import COMPANY
from .models import Cart


def site_context(request):
    role = None
    cart_count = 0
    user = request.user
    if user.is_authenticated:
        profile = getattr(user, 'profile', None)
        role = profile.role if profile else None
        if role == 'client':
            cart = Cart.objects.filter(user=user).first()
            if cart:
                cart_count = cart.total_items()
    return {
        'company': COMPANY,
        'user_role': role,
        'cart_count': cart_count,
    }
