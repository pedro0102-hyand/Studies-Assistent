"""URL configuration for studies_assistant project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# URLs do projeto
urlpatterns = [

    path('admin/', admin.site.urls), # Administração do Django
    path('api/', include('core.urls')), # URLs do core

]

# Etapa 3.2 — servir ficheiros enviados em desenvolvimento (não usar isto em produção)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
