from django.shortcuts import render
from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Mijoz, Qarz, ArxivMijoz, Tranzaksiya, TolanganArxiv


def index_page(req):
    return render(req, 'index.html')


# ===== STATISTIKA =====
@api_view(['GET'])
def statistika(request):
    jami_mijozlar = Mijoz.objects.count()
    # Hozirgi qoldiq qarz (hali to'lanmagan)
    jami_qarz = Qarz.objects.filter(tolandi=False, arxivda=False).aggregate(Sum('summa'))['summa__sum'] or 0
    # Yig'ilgan pullar - faqat HALI ARXIVLANMAGAN to'lovlar (Tranzaksiya tarixidan).
    # "🧹 Arxivlash" bosilganda bu yozuvlar arxivlandi=True bo'lib, hisob 0 dan qaytadan boshlanadi.
    jami_tolangan = Tranzaksiya.objects.filter(turi='tolov', arxivlandi=False).aggregate(Sum('summa'))['summa__sum'] or 0
    return Response({
        'jami_mijozlar': jami_mijozlar,
        'jami_qarz': jami_qarz,
        'jami_tolangan': jami_tolangan
    })


# ===== MIJOZLAR =====
@api_view(['GET', 'POST'])
def mijozlar_list(request):
    if request.method == 'GET':
        mijozlar = Mijoz.objects.all().order_by('-created_at')
        data = []
        for m in mijozlar:
            umumiy_qarz = m.qarzlar.filter(tolandi=False).aggregate(Sum('summa'))['summa__sum'] or 0
            qarz_soni = m.qarzlar.filter(tolandi=False).count()
            data.append({
                'id': m.id,
                'ism': m.ism,
                'telefon': m.telefon,
                'umumiy_qarz': umumiy_qarz,
                'qarz_soni': qarz_soni
            })
        return Response(data)

    elif request.method == 'POST':
        ism = request.data.get('ism')
        telefon = request.data.get('telefon')
        if not ism or not telefon:
            return Response({'xato': 'Ism va telefon majburiy!'}, status=400)
        mijoz = Mijoz.objects.create(ism=ism, telefon=telefon)
        return Response({'id': mijoz.id, 'ism': mijoz.ism, 'telefon': mijoz.telefon})


@api_view(['DELETE'])
def mijoz_delete(request, pk):
    """Mijozni o'chirish - lekin ma'lumotlari arxivga o'tadi"""
    try:
        mijoz = Mijoz.objects.get(pk=pk)

        # Arxivga nusxa saqla
        arxiv_mijoz = ArxivMijoz.objects.create(
            asl_id=mijoz.id,
            ism=mijoz.ism,
            telefon=mijoz.telefon,
            created_at=mijoz.created_at
        )

        # Uning barcha qarzlarini arxivga ko'chir
        for qarz in mijoz.qarzlar.all():
            qarz.arxiv_mijoz = arxiv_mijoz
            qarz.mijoz = None
            qarz.arxivda = True
            qarz.save()

        # Uning tarixini (tranzaksiyalarini) ham arxivga ko'chir
        for t in mijoz.tranzaksiyalar.all():
            t.arxiv_mijoz = arxiv_mijoz
            t.mijoz = None
            t.save()

        # Asl mijozni o'chir
        mijoz.delete()

        return Response({'muvaffaqiyat': True, 'arxiv_id': arxiv_mijoz.id})
    except Mijoz.DoesNotExist:
        return Response(status=404)


# ===== QARZLAR =====
@api_view(['GET', 'POST'])
def qarzlar_list(request, mijoz_id):
    if request.method == 'GET':
        qarzlar = Qarz.objects.filter(mijoz_id=mijoz_id).order_by('-created_at')
        data = [{
            'id': q.id, 'mijoz_id': q.mijoz_id, 'mahsulot': q.mahsulot,
            'summa': q.summa, 'tolandi': int(q.tolandi), 'created_at': q.created_at
        } for q in qarzlar]
        return Response(data)

    elif request.method == 'POST':
        mahsulot = request.data.get('mahsulot')
        summa = request.data.get('summa')
        if not mahsulot or not summa:
            return Response({'xato': 'Barcha maydonlar majburiy!'}, status=400)
        summa = float(summa)
        qarz = Qarz.objects.create(mijoz_id=mijoz_id, mahsulot=mahsulot, summa=summa)

        # Tarixga yozamiz: yangi qarz qo'shildi (+)
        Tranzaksiya.objects.create(
            mijoz_id=mijoz_id, turi='qoshildi', summa=summa, izoh=mahsulot
        )

        return Response({'id': qarz.id, 'mahsulot': qarz.mahsulot, 'summa': qarz.summa})


@api_view(['PATCH', 'DELETE'])
def qarz_detail(request, pk):
    """PATCH - qarzni to'liq to'landi deb belgilash (checkmark tugmasi)"""
    try:
        qarz = Qarz.objects.get(pk=pk)
    except Qarz.DoesNotExist:
        return Response(status=404)

    if request.method == 'PATCH':
        # Qolgan summa "to'lov" sifatida tarixga yoziladi (-)
        if qarz.summa > 0:
            Tranzaksiya.objects.create(
                mijoz=qarz.mijoz, arxiv_mijoz=qarz.arxiv_mijoz,
                turi='tolov', summa=qarz.summa, izoh=qarz.mahsulot
            )
        qarz.tolandi = True
        qarz.save()
        return Response({'muvaffaqiyat': True})
    elif request.method == 'DELETE':
        qarz.delete()
        return Response({'muvaffaqiyat': True})


@api_view(['DELETE'])
def qarz_delete(request, pk):
    try:
        Qarz.objects.get(pk=pk).delete()
        return Response({'muvaffaqiyat': True})
    except Qarz.DoesNotExist:
        return Response(status=404)


# ===== QISMAN TO'LOV QILISH (summadan ayiradi, tarixga '-' bilan yoziladi) =====
@api_view(['PATCH'])
def qarz_tolov(request, pk):
    """
    Mijoz qarzning bir qismini (yoki to'lig'ini) to'ladi.
    - Kiritilgan summa qarzdan ayiriladi.
    - Xuddi shu summa 'Tranzaksiya' tarixiga 'tolov' (-) sifatida yoziladi,
      sana va vaqti bilan birga saqlanadi.
    - Agar qolgan summa 0 yoki undan kam bo'lsa, qarz to'liq to'langan deb belgilanadi.
    """
    try:
        qarz = Qarz.objects.get(pk=pk)
    except Qarz.DoesNotExist:
        return Response(status=404)

    try:
        tolov_summa = float(request.data.get('summa', 0))
    except (TypeError, ValueError):
        return Response({'xato': "Noto'g'ri summa kiritildi!"}, status=400)

    if tolov_summa <= 0:
        return Response({'xato': "Summa 0 dan katta bo'lishi kerak!"}, status=400)

    qarz.summa -= tolov_summa
    if qarz.summa <= 0:
        qarz.summa = 0
        qarz.tolandi = True
    qarz.save()

    # Tarixga yozib qo'yamiz (sana avtomatik saqlanadi)
    Tranzaksiya.objects.create(
        mijoz=qarz.mijoz, arxiv_mijoz=qarz.arxiv_mijoz,
        turi='tolov', summa=tolov_summa, izoh=qarz.mahsulot
    )

    return Response({
        'muvaffaqiyat': True,
        'qolgan_summa': qarz.summa,
        'tolandi': qarz.tolandi
    })


# ===== YANA QARZ QO'SHISH (summaga qo'shadi, tarixga '+' bilan yoziladi) =====
@api_view(['PATCH'])
def qarz_qoshish(request, pk):
    """Mijoz yana qarzga narsa oldi - kiritilgan summa qarzga qo'shiladi va
    tarixga 'qoshildi' (+) sifatida yoziladi. Agar qarz avval to'langan bo'lsa
    ham, u qayta 'to'lanmagan' holatiga o'tadi."""
    try:
        qarz = Qarz.objects.get(pk=pk)
    except Qarz.DoesNotExist:
        return Response(status=404)

    try:
        qoshimcha_summa = float(request.data.get('summa', 0))
    except (TypeError, ValueError):
        return Response({'xato': "Noto'g'ri summa kiritildi!"}, status=400)

    if qoshimcha_summa <= 0:
        return Response({'xato': "Summa 0 dan katta bo'lishi kerak!"}, status=400)

    qarz.summa += qoshimcha_summa
    qarz.tolandi = False
    qarz.save()

    Tranzaksiya.objects.create(
        mijoz=qarz.mijoz, arxiv_mijoz=qarz.arxiv_mijoz,
        turi='qoshildi', summa=qoshimcha_summa, izoh=qarz.mahsulot
    )

    return Response({
        'muvaffaqiyat': True,
        'yangi_summa': qarz.summa
    })


# ===== MIJOZNING TARIXI (qachon qarz olgan, qachon to'lagan) =====
@api_view(['GET'])
def mijoz_tarix(request, mijoz_id):
    """Bitta mijozning barcha amallar tarixi, eng yangisidan boshlab.
    Bu yerda 'Yig'ilgan Pullar' arxivlanган-arxivlanmaganidan qat'iy nazar,
    mijozning HAMMA tarixi to'liq ko'rsatiladi - hech narsa yashirilmaydi."""
    tranzaksiyalar = Tranzaksiya.objects.filter(mijoz_id=mijoz_id).order_by('-sana')
    data = [{
        'id': t.id,
        'turi': t.turi,
        'summa': t.summa,
        'izoh': t.izoh,
        'sana': t.sana
    } for t in tranzaksiyalar]
    return Response(data)


# ===== TO'LANGAN PULLARNI O'CHIRISH (mijoz sahifasidagi 🧹 tugmasi) =====
@api_view(['DELETE'])
def tolangan_tozala(request, mijoz_id):
    """Bitta mijozning to'langan qarzlarini o'chirish
    (Tranzaksiya tarixi saqlanib qoladi, statistikaga ta'sir qilmaydi)"""
    Qarz.objects.filter(mijoz_id=mijoz_id, tolandi=True).delete()
    return Response({'muvaffaqiyat': True})


# ===== YIG'ILGAN PULLARNI ARXIVLASH (statistika kartasidagi 🧹 tugmasi) =====
@api_view(['POST'])
def tolangan_arxivla(request):
    """
    Hozirgi "Yig'ilgan Pullar" statistikasini (hali arxivlanmagan barcha
    'tolov' tranzaksiyalarini) bitta TolanganArxiv yozuviga jamlab saqlaydi,
    so'ngra ularni arxivlandi=True deb belgilaydi - shu bilan "Yig'ilgan
    Pullar" hisobi 0 dan qaytadan boshlanadi.

    Mijozlarning shaxsiy "To'lov va Qarz Tarixi"ga bu ta'sir qilmaydi -
    Tranzaksiya yozuvlari o'chirilmaydi, faqat belgilab qo'yiladi.
    """
    tranzaksiyalar = Tranzaksiya.objects.filter(
        turi='tolov', arxivlandi=False
    ).order_by('sana')

    if not tranzaksiyalar.exists():
        return Response({'xato': "Hozircha arxivlash uchun yig'ilgan pul yo'q!"}, status=400)

    jami = tranzaksiyalar.aggregate(Sum('summa'))['summa__sum'] or 0
    soni = tranzaksiyalar.count()
    birinchi = tranzaksiyalar.first()
    oxirgi = tranzaksiyalar.last()

    tafsilotlar = []
    for t in tranzaksiyalar:
        if t.mijoz:
            mijoz_ismi = t.mijoz.ism
        elif t.arxiv_mijoz:
            mijoz_ismi = t.arxiv_mijoz.ism
        else:
            mijoz_ismi = "Noma'lum mijoz"
        tafsilotlar.append({
            'mijoz': mijoz_ismi,
            'summa': t.summa,
            'izoh': t.izoh,
            'sana': t.sana.isoformat()
        })

    arxiv = TolanganArxiv.objects.create(
        jami_summa=jami,
        tranzaksiyalar_soni=soni,
        boshlanish_sana=birinchi.sana,
        tugash_sana=oxirgi.sana,
        tafsilotlar=tafsilotlar
    )

    tranzaksiyalar.update(arxivlandi=True)

    return Response({
        'muvaffaqiyat': True,
        'arxiv_id': arxiv.id,
        'jami_summa': jami
    })


@api_view(['GET'])
def tolangan_arxiv_royxati(request):
    """Barcha 'Yig'ilgan Pullar' arxiv yozuvlari, eng yangisidan boshlab"""
    arxivlar = TolanganArxiv.objects.all().order_by('-ochirilgan_vaqt')
    data = [{
        'id': a.id,
        'jami_summa': a.jami_summa,
        'tranzaksiyalar_soni': a.tranzaksiyalar_soni,
        'boshlanish_sana': a.boshlanish_sana,
        'tugash_sana': a.tugash_sana,
        'ochirilgan_vaqt': a.ochirilgan_vaqt,
        'tafsilotlar': a.tafsilotlar
    } for a in arxivlar]
    return Response(data)


@api_view(['DELETE'])
def tolangan_arxiv_ochir(request, arxiv_id):
    """'Yig'ilgan Pullar' arxividagi bitta yozuvni butunlay o'chirish.
    Bu faqat arxiv yozuvini (xulosa kartasini) o'chiradi - tegishli
    Tranzaksiya yozuvlari va mijozlarning shaxsiy tarixi o'zgarmaydi."""
    try:
        TolanganArxiv.objects.get(pk=arxiv_id).delete()
        return Response({'muvaffaqiyat': True})
    except TolanganArxiv.DoesNotExist:
        return Response(status=404)


# ===== ARXIV (MIJOZLAR) =====
@api_view(['GET'])
def umumiy_arxiv(request):
    """Arxivdagi mijozlar va ularning qarzlari"""
    arxiv_mijozlar = ArxivMijoz.objects.all().order_by('-arxivlangan_vaqt')
    data = []
    for am in arxiv_mijozlar:
        qarzlar = am.qarzlar.all()
        jami = sum(q.summa for q in qarzlar if not q.tolandi)
        jami_tolangan = sum(q.summa for q in qarzlar if q.tolandi)
        data.append({
            'id': am.id,
            'ism': am.ism,
            'telefon': am.telefon,
            'arxivlangan_vaqt': am.arxivlangan_vaqt,
            'jami_qarz': jami,
            'jami_tolangan': jami_tolangan,
            'qarzlar': [{
                'id': q.id,
                'mahsulot': q.mahsulot,
                'summa': q.summa,
                'tolandi': q.tolandi,
                'created_at': q.created_at
            } for q in qarzlar]
        })
    return Response(data)


@api_view(['POST'])
def arxivdan_chiqar(request, arxiv_id):
    """Arxivdagi mijozni qayta faol holatga qaytarish"""
    try:
        arxiv_mijoz = ArxivMijoz.objects.get(pk=arxiv_id)

        # Yangi faol mijoz yarat
        yangi_mijoz = Mijoz.objects.create(
            ism=arxiv_mijoz.ism,
            telefon=arxiv_mijoz.telefon,
            created_at=arxiv_mijoz.created_at
        )

        # Qarzlarini qaytarish
        for qarz in arxiv_mijoz.qarzlar.all():
            qarz.mijoz = yangi_mijoz
            qarz.arxiv_mijoz = None
            qarz.arxivda = False
            qarz.save()

        # Tarixini (tranzaksiyalarini) ham qaytarish
        for t in arxiv_mijoz.tranzaksiyalar.all():
            t.mijoz = yangi_mijoz
            t.arxiv_mijoz = None
            t.save()

        # Arxiv yozuvini o'chir
        arxiv_mijoz.delete()

        return Response({'muvaffaqiyat': True, 'yangi_mijoz_id': yangi_mijoz.id})
    except ArxivMijoz.DoesNotExist:
        return Response(status=404)


@api_view(['DELETE'])
def arxivdan_ochir(request, arxiv_id):
    """Arxivdagi mijozni butunlay o'chirish
    (Tranzaksiya tarixi saqlanib qoladi, statistikaga ta'sir qilmaydi)"""
    try:
        ArxivMijoz.objects.get(pk=arxiv_id).delete()
        return Response({'muvaffaqiyat': True})
    except ArxivMijoz.DoesNotExist:
        return Response(status=404)
