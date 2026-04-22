from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):

    model = Message
    extra = 0
    readonly_fields = ('role', 'content', 'sources', 'created_at')


@admin.register(Conversation) # Registra o modelo Conversation no admin

class ConversationAdmin(admin.ModelAdmin): # Define o admin para o modelo Conversation

    list_display = ('id', 'title', 'user', 'updated_at') # Define os campos que serão exibidos na lista de conversas
    list_filter = ('created_at',) # Define os filtros que serão exibidos na lista de conversas
    inlines = [MessageInline] # Define os inlines que serão exibidos na lista de conversas


@admin.register(Message) # Registra o modelo Message no admin   

class MessageAdmin(admin.ModelAdmin): # Define o admin para o modelo Message    

    list_display = ('id', 'conversation', 'role', 'created_at') # Define os campos que serão exibidos na lista de mensagens
    list_filter = ('role',) # Define os filtros que serão exibidos na lista de mensagens
