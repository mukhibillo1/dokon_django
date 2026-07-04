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


class Tranzaksiya(models.Model):
    """
    Har bir mijoz uchun to'liq amallar tarixi (qachon qarz olgan, qachon pul bergan).
    - turi='qoshildi'  -> mijoz yangi qarz oldi (jadvalda '+' bilan ko'rsatiladi)
    - turi='tolov'     -> mijoz pul to'ladi (jadvalda '-' bilan ko'rsatiladi)
    Bu jadval mustaqil saqlanadi: mijoz arxivga o'tsa yoki qarz o'chirilsa ham
    tarix (va shunga bog'liq 'Yig'ilgan pullar' statistikasi) yo'qolmaydi.

    arxivlandi=True bo'lgan 'tolov' yozuvlari "Yig'ilgan Pullar" umumiy
    hisobidan (statistika) chiqarib tashlanadi, chunki ular allaqachon
    TolanganArxiv'ga bitta yozuv sifatida saqlab, hisobdan arxivlab qo'yilgan.
    Mijozning shaxsiy "To'lov va Qarz Tarixi"da esa bu yozuvlar baribir
    to'liq ko'rinishda qoladi — hech narsa o'chirilmaydi.
    """
    TURLAR = [
        ('qoshildi', "Qarzga qo'shildi"),
        ('tolov', "To'lov qilindi"),
    ]
    mijoz = models.ForeignKey(
        Mijoz, on_delete=models.SET_NULL,
        related_name='tranzaksiyalar', null=True, blank=True
    )
    arxiv_mijoz = models.ForeignKey(
        ArxivMijoz, on_delete=models.SET_NULL,
        related_name='tranzaksiyalar', null=True, blank=True
    )
    turi = models.CharField(max_length=10, choices=TURLAR)
    summa = models.FloatField()
    izoh = models.CharField(max_length=255, blank=True, default='')
    sana = models.DateTimeField(auto_now_add=True)
    arxivlandi = models.BooleanField(default=False)

    def __str__(self):
        belgi = '+' if self.turi == 'qoshildi' else '-'
        return f"{belgi}{self.summa} so'm - {self.izoh}"


class TolanganArxiv(models.Model):
    """
    "Yig'ilgan Pullar" statistikasi qo'lda arxivlanganda (masalan, do'kon
    egasi kassadan pulni haqiqatda olganida) shu yerga bitta yozuv sifatida
    saqlanadi: qachon (sana/vaqt) va qancha pul arxivlangani. Shundan keyin
    "Yig'ilgan Pullar" hisobi 0 dan qaytadan boshlanadi.

    `tafsilotlar` maydonida arxivlangan har bir to'lovning ro'yxati (mijoz
    ismi, summasi, sanasi) saqlanadi — arxiv panelida ustiga bosilganda
    aynan qaysi to'lovlar kiritilgani ko'rinishi uchun.
    """
    jami_summa = models.FloatField()
    tranzaksiyalar_soni = models.IntegerField(default=0)
    boshlanish_sana = models.DateTimeField(null=True, blank=True)
    tugash_sana = models.DateTimeField(null=True, blank=True)
    ochirilgan_vaqt = models.DateTimeField(auto_now_add=True)
    tafsilotlar = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Arxiv: {self.jami_summa} so'm"
