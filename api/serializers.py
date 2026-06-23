from rest_framework import serializers
from .models import Mijoz, Qarz, ArxivMijoz


class QarzSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qarz
        fields = ['id', 'mahsulot', 'summa', 'tolandi', 'created_at']


class MijozSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mijoz
        fields = ['id', 'ism', 'telefon', 'created_at']


class ArxivMijozSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArxivMijoz
        fields = ['id', 'ism', 'telefon', 'created_at', 'arxivlangan_vaqt']
