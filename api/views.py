from django.shortcuts import render
from django.db.models import Sum
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Mijoz, Qarz, ArxivMijoz


def index_page(req):
    return render(req, 'index.html')


# ===== STATISTIKA =====
@api_view(['GET'])
def statistika(request):
    jami_mijozlar = Mijoz.objects.count()
    jami_qarz = Qarz.objects.filter(tolandi=False, arxivda=False).aggregate(Sum('summa'))['summa__sum'] or 0
    jami_tolangan = Qarz.objects.filter(tolandi=True, arxivda=False).aggregate(Sum('summa'))['summa__sum'] or 0
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
        qarz = Qarz.objects.create(mijoz_id=mijoz_id, mahsulot=mahsulot, summa=float(summa))
        return Response({'id': qarz.id, 'mahsulot': qarz.mahsulot, 'summa': qarz.summa})


@api_view(['PATCH', 'DELETE'])
def qarz_detail(request, pk):
    try:
        qarz = Qarz.objects.get(pk=pk)
    except Qarz.DoesNotExist:
        return Response(status=404)

    if request.method == 'PATCH':
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


# ===== TO'LANGAN PULLARNI O'CHIRISH =====
@api_view(['DELETE'])
def tolangan_tozala(request, mijoz_id):
    """Bitta mijozning to'langan qarzlarini o'chirish"""
    Qarz.objects.filter(mijoz_id=mijoz_id, tolandi=True).delete()
    return Response({'muvaffaqiyat': True})


# ===== ARXIV =====
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

        # Arxiv yozuvini o'chir
        arxiv_mijoz.delete()

        return Response({'muvaffaqiyat': True, 'yangi_mijoz_id': yangi_mijoz.id})
    except ArxivMijoz.DoesNotExist:
        return Response(status=404)


@api_view(['DELETE'])
def arxivdan_ochir(request, arxiv_id):
    """Arxivdagi mijozni butunlay o'chirish"""
    try:
        ArxivMijoz.objects.get(pk=arxiv_id).delete()
        return Response({'muvaffaqiyat': True})
    except ArxivMijoz.DoesNotExist:
        return Response(status=404)
