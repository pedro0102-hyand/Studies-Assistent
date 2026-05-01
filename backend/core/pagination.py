"""Paginação reutilizável para listagens da API."""

from rest_framework.pagination import PageNumberPagination


class StandardPageNumberPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class ConversationListPagination(StandardPageNumberPagination):
    page_size = 30


class MessageListPagination(StandardPageNumberPagination):
    page_size = 100


class DocumentListPagination(StandardPageNumberPagination):
    page_size = 25
