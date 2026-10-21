from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Category, MaterialVideo, News, Order, Service

RU = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def slugify_ru(value):
    chars = []
    for ch in (value or '').strip().lower():
        if ch in RU:
            chars.append(RU[ch])
        elif ch.isascii() and ch.isalnum():
            chars.append(ch.lower())
        else:
            chars.append('-')
    slug = ''.join(chars)
    while '--' in slug:
        slug = slug.replace('--', '-')
    return slug.strip('-') or 'category'


def style_fields(form):
    for field in form.fields.values():
        widget = field.widget
        if widget.__class__.__name__ == 'CheckboxInput':
            widget.attrs.setdefault('class', 'check')
            continue
        css = widget.attrs.get('class', '')
        widget.attrs['class'] = (css + ' field').strip()


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'position']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_name(self):
        name = ' '.join((self.cleaned_data.get('name') or '').split())
        if not name:
            raise forms.ValidationError('Укажите название категории.')
        clash = Category.objects.filter(name_key=name.casefold())
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('Категория с таким названием уже существует.')
        return name

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.name = self.cleaned_data['name']
        obj.name_key = obj.name.casefold()
        if not obj.slug:
            base = slugify_ru(obj.name)
            slug = base
            number = 2
            while Category.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
                slug = f'{base}-{number}'
                number += 1
            obj.slug = slug
        if commit:
            obj.save()
        return obj


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'name', 'price', 'duration', 'method', 'description', 'image', 'available']
        widgets = {'description': forms.Textarea(attrs={'rows': 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError('Стоимость не может быть отрицательной.')
        return price


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'text', 'published_at']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 8}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class VideoForm(forms.ModelForm):
    class Meta:
        model = MaterialVideo
        fields = ['title', 'description', 'video']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label='Имя', max_length=150)
    last_name = forms.CharField(label='Фамилия', max_length=150, required=False)
    email = forms.EmailField(label='Почта', required=False)
    phone = forms.CharField(label='Телефон', max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повтор пароля'
        style_fields(self)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email') or ''
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data.get('phone') or ''
            profile.role = profile.ROLE_CLIENT
            profile.save()
        return user


class ManagerCreateForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150)
    first_name = forms.CharField(label='Имя', max_length=150)
    last_name = forms.CharField(label='Фамилия', max_length=150, required=False)
    email = forms.EmailField(label='Почта', required=False)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже есть.')
        return username

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data.get('first_name') or '',
            last_name=self.cleaned_data.get('last_name') or '',
            email=self.cleaned_data.get('email') or '',
        )
        user.profile.role = user.profile.ROLE_MANAGER
        user.profile.save(update_fields=['role'])
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Логин'
        self.fields['password'].label = 'Пароль'
        style_fields(self)


class CheckoutForm(forms.Form):
    phone = forms.CharField(label='Телефон', max_length=20)
    contact = forms.CharField(
        label='Как удобно связаться',
        max_length=200,
        help_text='Например: Telegram, WhatsApp или звонок, и удобное время.',
    )
    comment = forms.CharField(label='Комментарий к запросу', required=False, widget=forms.Textarea(attrs={'rows': 4}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)


class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['phone', 'contact', 'comment']
        widgets = {'comment': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
