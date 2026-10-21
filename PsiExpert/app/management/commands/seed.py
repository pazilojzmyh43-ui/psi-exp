from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Category, MaterialVideo, News, Order, OrderItem, Profile, Service

ROOT = Path(__file__).resolve().parents[3]
IMAGES = ROOT / 'seed_media' / 'images'
VIDEOS = ROOT / 'seed_media' / 'videos'


class Command(BaseCommand):
    help = 'Заполняет базу центра «Пси-Эксперт» демонстрационными данными.'

    def handle(self, *args, **options):
        self._users()
        categories = self._categories()
        self._services(categories)
        self._news()
        self._videos()
        self._sample_order()
        self.stdout.write(self.style.SUCCESS('База «Пси-Эксперт» заполнена.'))

    def _users(self):
        specs = [
            ('admin', 'PsiAdmin!26', 'Анна', 'Соколова', Profile.ROLE_ADMIN, True),
            ('manager', 'PsiManager!26', 'Мария', 'Лебедева', Profile.ROLE_MANAGER, False),
            ('client', 'PsiClient!26', 'Иван', 'Морозов', Profile.ROLE_CLIENT, False),
        ]
        for username, password, first, last, role, is_super in specs:
            user, created = User.objects.get_or_create(username=username, defaults={
                'first_name': first,
                'last_name': last,
                'is_staff': is_super,
                'is_superuser': is_super,
            })
            if created:
                user.set_password(password)
            user.first_name = first
            user.last_name = last
            user.is_staff = is_super
            user.is_superuser = is_super
            user.save()
            profile = user.profile
            profile.role = role
            if username == 'client':
                profile.phone = '+7 (911) 200-10-10'
            profile.save()

    def _categories(self):
        rows = [
            ('Индивидуальная терапия', 1,
             'Личная работа со взрослыми: тревога, депрессия, кризис, отношения и самооценка.'),
            ('Специальные методы', 2,
             'КПТ, EMDR, ImTT, интегративный подход и психодиагностика.'),
            ('Форматы консультаций', 3,
             'Как можно встретиться: бесплатное знакомство, очно, онлайн, курсом или срочно.'),
        ]
        result = {}
        for name, position, description in rows:
            category, _created = Category.objects.get_or_create(
                name_key=name.casefold(),
                defaults={'name': name, 'slug': '', 'description': description, 'position': position},
            )
            category.name = name
            category.description = description
            category.position = position
            if not category.slug:
                from app.forms import slugify_ru
                category.slug = slugify_ru(name)
            category.save()
            result[name] = category
        return result

    def _services(self, categories):
        rows = [
            ('Индивидуальная терапия', 'Тревога и панические состояния', '3500', '60 минут', 'Интегративный подход', 'banner1.jpg', True,
             'Разбираем, как тревога запускается и чем её можно останавливать в обычной жизни. Работаем со взрослыми от 18 лет.'),
            ('Индивидуальная терапия', 'Депрессия и выгорание', '3500', '60 минут', 'КПТ', 'banner3.jpg', True,
             'Когда сил нет даже на простые дела. Смотрим на мысли, режим и то, что можно вернуть маленькими шагами.'),
            ('Индивидуальная терапия', 'Кризисная поддержка', '4000', '75 минут', 'Кризисная психология', 'banner2.jpg', True,
             'Острая ситуация, потеря опоры, решение, которое нельзя откладывать. Сессия короче курса и ближе к «здесь и сейчас».'),
            ('Индивидуальная терапия', 'Отношения и личные границы', '3500', '60 минут', 'Интегративный подход', 'banner1.jpg', True,
             'Пары не ведём совместно: работаем с одним взрослым — про близость, отказы, обиду и свои границы.'),
            ('Индивидуальная терапия', 'Самооценка', '3500', '60 минут', 'КПТ', 'banner3.jpg', True,
             'Внутренний критик, стыд и сравнение с другими. Ищем, откуда берётся оценка себя и чем её заменить.'),
            ('Специальные методы', 'Когнитивно-поведенческая терапия', '3500', '60 минут', 'КПТ', 'cbt_logo.png', True,
             'Классическая КПТ: связь мыслей, чувств и поведения. Подходит для тревоги, сниженного настроения и избегания.'),
            ('Специальные методы', 'EMDR (ДПДГ)', '4500', '75 минут', 'EMDR', 'emdr_logo.png', True,
             'Десенсибилизация и переработка травматичных воспоминаний с помощью движений глаз. Только после знакомства с запросом.'),
            ('Специальные методы', 'ImTT — трансформация образа', '4500', '75 минут', 'ImTT', 'imtt_logo.png', True,
             'Терапия трансформацией образа Роберта Миллера. Сессия длиннее обычной: 1 час 15 минут.'),
            ('Специальные методы', 'Интегративный подход', '3500', '60 минут', 'Интегративный подход', 'banner2.jpg', True,
             'Сочетаем то, что подходит запросу, а не тянем человека в один метод. Супервизия и личная терапия у специалиста есть.'),
            ('Специальные методы', 'Психодиагностика', '5000', 'по договорённости', 'Диагностика', 'banner3.jpg', True,
             'Схема и стоимость зависят от запроса. Итог — понятное описание, а не набор терминов.'),
            ('Форматы консультаций', 'Предварительная консультация', '0', '20 минут', 'Знакомство', 'banner2.jpg', True,
             'Бесплатно. Знакомимся и обсуждаем запрос: подходим ли мы друг другу. Онлайн.'),
            ('Форматы консультаций', 'Очная сессия в Пскове', '3500', '60 минут', 'Кабинет', 'banner1.jpg', True,
             'Встреча в кабинете. Точный адрес сообщаем после записи, чтобы не светить его в открытом доступе.'),
            ('Форматы консультаций', 'Онлайн-сессия', '3500', '60 минут', 'Видеосвязь', 'banner2.jpg', True,
             'Консультация из любого города. Ссылка на созвон приходит после подтверждения времени.'),
            ('Форматы консультаций', 'Курс из 8 встреч', '26000', '8 × 60 минут', 'Курс', 'banner3.jpg', True,
             'Если запрос не разовый. Курс дешевле восьми отдельных сессий, ритм — обычно раз в неделю.'),
            ('Форматы консультаций', 'Кризисная сессия в ближайшие сутки', '5000', '75 минут', 'Срочно', 'banner1.jpg', True,
             'Если нельзя ждать обычного окна записи. Это не служба спасения: при угрозе жизни звоните 112 или 8-800-2000-122.'),
        ]
        for category_name, name, price, duration, method, filename, available, description in rows:
            service, _created = Service.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[category_name],
                    'price': Decimal(price),
                    'duration': duration,
                    'method': method,
                    'available': available,
                    'description': description,
                },
            )
            service.category = categories[category_name]
            service.price = Decimal(price)
            service.duration = duration
            service.method = method
            service.available = available
            service.description = description
            service.save()
            path = IMAGES / filename
            if path.exists() and not service.image:
                with path.open('rb') as handle:
                    service.image.save(filename, File(handle), save=True)

    def _news(self):
        today = timezone.now()
        rows = [
            ('Как устроена первая встреча', 2,
             'Предварительная консультация длится 20 минут и ничего не стоит. На ней можно сказать запрос своими словами: '
             'не нужно формулировать «диагноз». Если формат не подойдёт, на этом и остановимся.'),
            ('С чем центр не работает', 9,
             'Индивидуально и только со взрослыми от 18 лет. Не берём детей и подростков, зависимости и психиатрические диагнозы. '
             'Лучше сразу сказать об этом, чем потерять время.'),
            ('Онлайн остаётся основным форматом', 16,
             'Большая часть сессий проходит по видеосвязи. Очный кабинет в Пскове открываем по записи, адрес отправляем лично.'),
            ('Супервизия и повышение квалификации', 24,
             'Специалист центра проходит личную терапию, групповую и индивидуальную супервизии и разбирает работу на интервизиях. '
             'Это обычная часть профессии, а не исключение.'),
            ('Конфиденциальность', 40,
             'Содержание сессий не обсуждается с третьими лицами. Исключение одно: прямая угроза жизни. '
             'Контакты на сайте нужны только для записи, а не для рассылки.'),
        ]
        for title, days, text in rows:
            News.objects.update_or_create(
                title=title,
                defaults={'text': text, 'published_at': today - timedelta(days=days)},
            )

    def _videos(self):
        rows = [
            ('Тренировка для вас', 'video1.mp4',
             'Короткое упражнение, которое можно сделать самостоятельно. Это не замена консультации.'),
            ('Конфликт', 'video2.mp4',
             'О том, как конфликт разворачивается и где в нём обычно теряется контакт. Материал для взрослых.'),
        ]
        for title, filename, description in rows:
            video, _created = MaterialVideo.objects.get_or_create(
                title=title,
                defaults={'description': description},
            )
            video.description = description
            path = VIDEOS / filename
            if path.exists() and not video.video:
                with path.open('rb') as handle:
                    video.video.save(filename, File(handle), save=True)
            else:
                video.save()

    def _sample_order(self):
        if Order.objects.exists():
            return
        client = User.objects.get(username='client')
        intro = Service.objects.get(name='Предварительная консультация')
        anxiety = Service.objects.get(name='Тревога и панические состояния')
        order = Order.objects.create(
            user=client,
            total=intro.price + anxiety.price,
            phone='+7 (911) 200-10-10',
            contact='Telegram, после 18:00',
            comment='Хочу начать со знакомства и одной сессии про тревогу.',
            status=Order.STATUS_NEW,
        )
        OrderItem.objects.create(order=order, service=intro, service_name=intro.name, quantity=1, price=intro.price)
        OrderItem.objects.create(order=order, service=anxiety, service_name=anxiety.name, quantity=1, price=anxiety.price)
