from django.urls import path
from . import views

urlpatterns = [
    path(
        'documents/upload/',
        views.DocumentUploadView.as_view(),
        name='document_upload',
    ),
    path(
        'documents/<int:pk>/',
        views.DocumentDeleteView.as_view(),
        name='document_delete',
    ),
    path(
        'documents/',
        views.DocumentListView.as_view(),
        name='document_list',
    ),
    path(
        'rag/ask/',
        views.RagAskView.as_view(),
        name='rag_ask',
    ),
    path(
        'rag/generate/',
        views.RagGenerateView.as_view(),
        name='rag_generate',
    ),
]
