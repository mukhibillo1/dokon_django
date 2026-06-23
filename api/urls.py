from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_page, name='index'),
    path('api/mijozlar', views.mijozlar_list, name='mijozlar_list'),
    path('api/mijozlar/<int:pk>', views.mijoz_delete, name='mijoz_delete'),
    path('api/qarzlar/<int:mijoz_id>', views.qarzlar_list, name='qarzlar_list'),
    path('api/qarzlar/<int:pk>/tolandi', views.qarz_detail, name='qarz_tolandi'),
    path('api/qarzlar/<int:pk>/delete', views.qarz_delete, name='qarz_delete'),
    path('api/qarzlar/<int:mijoz_id>/tolangan-tozala', views.tolangan_tozala, name='tolangan_tozala'),
    path('api/statistika', views.statistika, name='statistika'),

    # Arxiv
    path('api/arxiv', views.umumiy_arxiv, name='umumiy_arxiv'),
    path('api/arxiv/<int:arxiv_id>/chiqar', views.arxivdan_chiqar, name='arxivdan_chiqar'),
    path('api/arxiv/<int:arxiv_id>/ochir', views.arxivdan_ochir, name='arxivdan_ochir'),
]
