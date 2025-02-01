from django.urls import path
from .views import VirtualCardApiView, VirtualCardListCreateApiView, VirtualCardTopupApiView

urlpatterns = [
    path('virtual-cards/', VirtualCardListCreateApiView.as_view(), name='virtual_card_list_create'),
    path('virtual-cards/<uuid:pk>/', VirtualCardApiView.as_view(), name='virtual_card_detail'),
    path('virtual-cards/<uuid:pk>/top-up/', VirtualCardTopupApiView.as_view(), name='virtual_card_topup'),
]
