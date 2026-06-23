from django.db import models


class ArxivMijoz(models.Model):
    """O'chirilgan mijozning arxivdagi nusxasi"""
    asl_id = models.IntegerField()  # Asl mijoz ID si
    ism = models.CharField(max_length=255)
    telefon = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    arxivlangan_vaqt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[ARXIV] {self.ism}"


class Mijoz(models.Model):
    ism = models.CharField(max_length=255)
    telefon = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ism


class Qarz(models.Model):
    mijoz = models.ForeignKey(
        Mijoz, on_delete=models.SET_NULL,
        related_name='qarzlar', null=True, blank=True
    )
    # Arxivlangan mijoz uchun
    arxiv_mijoz = models.ForeignKey(
        ArxivMijoz, on_delete=models.CASCADE,
        related_name='qarzlar', null=True, blank=True
    )
    mahsulot = models.CharField(max_length=255)
    summa = models.FloatField()
    tolandi = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    arxivda = models.BooleanField(default=False)  # Arxivda ekanligini belgilaydi
