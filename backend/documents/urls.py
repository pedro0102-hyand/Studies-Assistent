from django.urls import path

from . import views

urlpatterns = [
    path(
        'documents/upload/',
        views.DocumentUploadView.as_view(),
        name='document_upload',
    ),
]
