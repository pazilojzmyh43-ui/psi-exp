from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Пси-Эксперт — администрирование'
admin.site.site_title = 'Пси-Эксперт'
admin.site.index_title = 'Данные центра'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
