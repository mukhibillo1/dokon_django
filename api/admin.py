from django.contrib import admin
from .models import Mijoz, Qarz, ArxivMijoz


@admin.register(Mijoz)
class MijozAdmin(admin.ModelAdmin):
    list_display = ['ism', 'telefon', 'created_at']
    search_fields = ['ism', 'telefon']


@admin.register(ArxivMijoz)
class ArxivMijozAdmin(admin.ModelAdmin):
    list_display = ['ism', 'telefon', 'arxivlangan_vaqt']
    search_fields = ['ism', 'telefon']


@admin.register(Qarz)
class QarzAdmin(admin.ModelAdmin):
    list_display = ['mahsulot', 'summa', 'tolandi', 'arxivda', 'created_at']
    list_filter = ['tolandi', 'arxivda']
