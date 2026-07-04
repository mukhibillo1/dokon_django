from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_page, name='index'),
    path('api/mijozlar', views.mijozlar_list, name='mijozlar_list'),
    path('api/mijozlar/<int:pk>', views.mijoz_delete, name='mijoz_delete'),
    path('api/mijozlar/<int:mijoz_id>/tarix', views.mijoz_tarix, name='mijoz_tarix'),
    path('api/qarzlar/<int:mijoz_id>', views.qarzlar_list, name='qarzlar_list'),
    path('api/qarzlar/<int:pk>/tolandi', views.qarz_detail, name='qarz_tolandi'),
    path('api/qarzlar/<int:pk>/delete', views.qarz_delete, name='qarz_delete'),
    path('api/qarzlar/<int:pk>/tolov', views.qarz_tolov, name='qarz_tolov'),
    path('api/qarzlar/<int:pk>/qoshish', views.qarz_qoshish, name='qarz_qoshish'),
    path('api/qarzlar/<int:mijoz_id>/tolangan-tozala', views.tolangan_tozala, name='tolangan_tozala'),
    path('api/statistika', views.statistika, name='statistika'),
    # Yig'ilgan pullarni arxivlash
    path('api/tolangan/arxivla', views.tolangan_arxivla, name='tolangan_arxivla'),
    path('api/tolangan/arxiv', views.tolangan_arxiv_royxati, name='tolangan_arxiv_royxati'),
    path('api/tolangan/arxiv/<int:arxiv_id>/ochir', views.tolangan_arxiv_ochir, name='tolangan_arxiv_ochir'),
    # Mijozlar arxivi
    path('api/arxiv', views.umumiy_arxiv, name='umumiy_arxiv'),
    path('api/arxiv/<int:arxiv_id>/chiqar', views.arxivdan_chiqar, name='arxivdan_chiqar'),
    path('api/arxiv/<int:arxiv_id>/ochir', views.arxivdan_ochir, name='arxivdan_ochir'),
]
