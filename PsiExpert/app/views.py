from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import (
    CategoryForm,
    CheckoutForm,
    LoginForm,
    ManagerCreateForm,
    NewsForm,
    OrderEditForm,
    RegisterForm,
    ServiceForm,
    VideoForm,
)
from .models import (
    Cart,
    CartItem,
    Category,
    MaterialVideo,
    News,
    Order,
    OrderItem,
    Profile,
    Service,
)


def home(request):
    return render(request, 'app/home.html', {
        'news_list': News.objects.all()[:3],
        'categories': Category.objects.all(),
    })


def about(request):
    return render(request, 'app/about.html')


def news_list(request):
    return render(request, 'app/news_list.html', {'news_list': News.objects.all()})


def news_detail(request, pk):
    item = get_object_or_404(News, pk=pk)
    return render(request, 'app/news_detail.html', {'item': item})


def contacts(request):
    return render(request, 'app/contacts.html')


def catalog(request, slug=None):
    current = None
    categories = Category.objects.prefetch_related(
        Prefetch('services', queryset=Service.objects.order_by('name'))
    )
    if slug:
        current = get_object_or_404(Category, slug=slug)
        categories = categories.filter(pk=current.pk)
    return render(request, 'app/catalog.html', {
        'categories': categories,
        'current': current,
        'all_categories': Category.objects.all(),
    })


def service_detail(request, pk):
    service = get_object_or_404(Service.objects.select_related('category'), pk=pk)
    related = Service.objects.filter(category=service.category).exclude(pk=service.pk)[:4]
    return render(request, 'app/service_detail.html', {
        'service': service,
        'related': related,
    })


def materials(request):
    return render(request, 'app/materials.html', {'videos': MaterialVideo.objects.all()})


def _client_cart(user):
    cart, _created = Cart.objects.get_or_create(user=user)
    return cart


@require_POST
def cart_add(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if not request.user.is_authenticated:
        messages.info(request, 'Чтобы записаться, войдите или зарегистрируйтесь как клиент.')
        nxt = reverse('service_detail', args=[pk])
        return redirect(f"{reverse('login')}?next={nxt}")
    profile = getattr(request.user, 'profile', None)
    if profile is None or profile.role != Profile.ROLE_CLIENT:
        messages.error(request, 'Корзина записи доступна только клиенту.')
        return redirect('service_detail', pk=pk)
    if not service.available:
        messages.error(request, 'Эта услуга сейчас не открыта для записи.')
        return redirect('service_detail', pk=pk)
    cart = _client_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, service=service)
    if not created:
        item.quantity += 1
        item.save(update_fields=['quantity'])
    messages.success(request, f'«{service.name}» добавлена в корзину записи.')
    return redirect('cart')


@role_required(Profile.ROLE_CLIENT)
def cart_view(request):
    cart = _client_cart(request.user)
    items = cart.items.select_related('service', 'service__category')
    return render(request, 'app/cart.html', {'cart': cart, 'items': items})


@role_required(Profile.ROLE_CLIENT)
@require_POST
def cart_update(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    try:
        quantity = int(request.POST.get('quantity', '1'))
    except ValueError:
        quantity = 1
    if quantity <= 0:
        item.delete()
        messages.info(request, 'Позиция убрана из корзины.')
    else:
        item.quantity = min(quantity, 8)
        item.save(update_fields=['quantity'])
    return redirect('cart')


@role_required(Profile.ROLE_CLIENT)
@require_POST
def cart_remove(request, pk):
    item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    item.delete()
    messages.info(request, 'Позиция убрана из корзины.')
    return redirect('cart')


@role_required(Profile.ROLE_CLIENT)
def checkout(request):
    cart = _client_cart(request.user)
    items = list(cart.items.select_related('service'))
    if not items:
        messages.error(request, 'Корзина пуста.')
        return redirect('cart')
    profile = request.user.profile
    initial = {'phone': profile.phone} if profile.phone else {}
    form = CheckoutForm(request.POST or None, initial=None if request.method == 'POST' else initial)
    if request.method == 'POST' and form.is_valid():
        total = sum((item.line_total for item in items), Decimal('0'))
        order = Order.objects.create(
            user=request.user,
            total=total,
            phone=form.cleaned_data['phone'],
            contact=form.cleaned_data['contact'],
            comment=form.cleaned_data['comment'],
        )
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                service=item.service,
                service_name=item.service.name,
                quantity=item.quantity,
                price=item.service.price,
            )
            for item in items
        ])
        cart.items.all().delete()
        if not profile.phone:
            profile.phone = form.cleaned_data['phone']
            profile.save(update_fields=['phone'])
        messages.success(request, f'Запись №{order.pk} отправлена. Менеджер свяжется с вами.')
        return redirect('my_orders')
    return render(request, 'app/checkout.html', {'form': form, 'cart': cart, 'items': items})


@role_required(Profile.ROLE_CLIENT)
def my_orders(request):
    orders = request.user.orders.prefetch_related('items')
    return render(request, 'app/my_orders.html', {'orders': orders})


@role_required(Profile.ROLE_CLIENT)
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if not order.client_can_change():
        messages.error(request, 'Эту запись уже нельзя изменить.')
        return redirect('my_orders')
    form = OrderEditForm(request.POST or None, instance=order)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Запись №{order.pk} обновлена.')
        return redirect('my_orders')
    return render(request, 'app/order_form.html', {'form': form, 'order': order})


@role_required(Profile.ROLE_CLIENT)
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if not order.client_can_change():
        messages.error(request, 'Эту запись уже нельзя удалить.')
        return redirect('my_orders')
    if request.method == 'POST':
        number = order.pk
        order.delete()
        messages.info(request, f'Запись №{number} удалена.')
        return redirect('my_orders')
    return render(request, 'app/confirm_delete.html', {
        'title': f'Удалить запись №{order.pk}?',
        'object_label': order,
    })


@role_required(Profile.ROLE_MANAGER)
def manager_orders(request):
    orders = Order.objects.select_related('user').prefetch_related('items')
    return render(request, 'app/manager_orders.html', {
        'orders': orders,
        'statuses': Order.STATUS_CHOICES,
    })


@role_required(Profile.ROLE_MANAGER)
@require_POST
def manager_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status = request.POST.get('status')
    allowed = {code for code, _label in Order.STATUS_CHOICES}
    if status in allowed:
        order.status = status
        order.save(update_fields=['status'])
        messages.success(request, f'Статус записи №{order.pk} обновлён.')
    return redirect('manager_orders')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Учётная запись создана. Теперь можно записаться на консультацию.')
        return redirect('home')
    return render(request, 'app/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        nxt = request.POST.get('next') or request.GET.get('next') or ''
        if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
            return redirect(nxt)
        return redirect('home')
    return render(request, 'app/login.html', {'form': form, 'next': request.GET.get('next', '')})


@require_POST
def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из учётной записи.')
    return redirect('home')


def _panel_form(request, form_class, title, success, instance=None, template='app/panel/form.html'):
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, success)
        return None, form
    return render(request, template, {'form': form, 'title': title, 'instance': instance}), form


@role_required(Profile.ROLE_ADMIN)
def panel(request):
    return render(request, 'app/panel/dashboard.html', {
        'counts': {
            'categories': Category.objects.count(),
            'services': Service.objects.count(),
            'news': News.objects.count(),
            'videos': MaterialVideo.objects.count(),
            'users': User.objects.count(),
        }
    })


@role_required(Profile.ROLE_ADMIN)
def panel_categories(request):
    return render(request, 'app/panel/categories.html', {'categories': Category.objects.all()})


@role_required(Profile.ROLE_ADMIN)
def category_add(request):
    response, _form = _panel_form(request, CategoryForm, 'Новая категория', 'Категория сохранена.')
    return response or redirect('panel_categories')


@role_required(Profile.ROLE_ADMIN)
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    response, _form = _panel_form(request, CategoryForm, 'Изменить категорию', 'Категория обновлена.', category)
    return response or redirect('panel_categories')


@role_required(Profile.ROLE_ADMIN)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.services.exists():
        messages.error(request, 'Сначала уберите услуги из этой категории.')
        return redirect('panel_categories')
    if request.method == 'POST':
        category.delete()
        messages.info(request, 'Категория удалена.')
        return redirect('panel_categories')
    return render(request, 'app/confirm_delete.html', {
        'title': 'Удалить категорию?',
        'object_label': category.name,
    })


@role_required(Profile.ROLE_ADMIN)
def panel_services(request):
    services = Service.objects.select_related('category')
    return render(request, 'app/panel/services.html', {'services': services})


@role_required(Profile.ROLE_ADMIN)
def service_add(request):
    response, _form = _panel_form(request, ServiceForm, 'Новая услуга', 'Услуга сохранена.')
    return response or redirect('panel_services')


@role_required(Profile.ROLE_ADMIN)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    response, _form = _panel_form(request, ServiceForm, 'Изменить услугу', 'Услуга обновлена.', service)
    return response or redirect('panel_services')


@role_required(Profile.ROLE_ADMIN)
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.info(request, 'Услуга удалена. В уже созданных записях останутся название и цена.')
        return redirect('panel_services')
    return render(request, 'app/confirm_delete.html', {
        'title': 'Удалить услугу?',
        'object_label': service.name,
    })


@role_required(Profile.ROLE_ADMIN)
def panel_news(request):
    return render(request, 'app/panel/news.html', {'news_list': News.objects.all()})


@role_required(Profile.ROLE_ADMIN)
def news_add(request):
    response, _form = _panel_form(request, NewsForm, 'Новая новость', 'Новость сохранена.')
    return response or redirect('panel_news')


@role_required(Profile.ROLE_ADMIN)
def news_edit(request, pk):
    item = get_object_or_404(News, pk=pk)
    response, _form = _panel_form(request, NewsForm, 'Изменить новость', 'Новость обновлена.', item)
    return response or redirect('panel_news')


@role_required(Profile.ROLE_ADMIN)
def news_delete(request, pk):
    item = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.info(request, 'Новость удалена.')
        return redirect('panel_news')
    return render(request, 'app/confirm_delete.html', {
        'title': 'Удалить новость?',
        'object_label': item.title,
    })


@role_required(Profile.ROLE_ADMIN)
def panel_videos(request):
    return render(request, 'app/panel/videos.html', {'videos': MaterialVideo.objects.all()})


@role_required(Profile.ROLE_ADMIN)
def video_add(request):
    response, _form = _panel_form(request, VideoForm, 'Новый материал', 'Видео сохранено.')
    return response or redirect('panel_videos')


@role_required(Profile.ROLE_ADMIN)
def video_edit(request, pk):
    item = get_object_or_404(MaterialVideo, pk=pk)
    response, _form = _panel_form(request, VideoForm, 'Изменить материал', 'Видео обновлено.', item)
    return response or redirect('panel_videos')


@role_required(Profile.ROLE_ADMIN)
def video_delete(request, pk):
    item = get_object_or_404(MaterialVideo, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.info(request, 'Видео удалено.')
        return redirect('panel_videos')
    return render(request, 'app/confirm_delete.html', {
        'title': 'Удалить видео?',
        'object_label': item.title,
    })


@role_required(Profile.ROLE_ADMIN)
def panel_users(request):
    form = ManagerCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Менеджер зарегистрирован.')
        return redirect('panel_users')
    users = User.objects.select_related('profile').order_by('username')
    return render(request, 'app/panel/users.html', {'users': users, 'form': form})


@role_required(Profile.ROLE_ADMIN)
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else None
    if user == request.user or role == Profile.ROLE_ADMIN or user.is_superuser:
        messages.error(request, 'Администратора удалить нельзя.')
        return redirect('panel_users')
    if role not in (Profile.ROLE_CLIENT, Profile.ROLE_MANAGER):
        messages.error(request, 'Удалять можно только клиентов и менеджеров.')
        return redirect('panel_users')
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.info(request, f'Пользователь {username} удалён.')
        return redirect('panel_users')
    return render(request, 'app/confirm_delete.html', {
        'title': 'Удалить пользователя?',
        'object_label': f'{user.username} ({profile.get_role_display()})',
    })
