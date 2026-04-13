from django.urls import path
from . import views

urlpatterns = [

    # URL for uploading a document
    path(

        'documents/upload/',
        views.DocumentUploadView.as_view(),
        name='document_upload',

    ),

    path(
        # URL for listing documents
        'documents/',
        views.DocumentListView.as_view(),
        name='document_list',

    ),

]
