from django.urls import path

from .views import NextOfKinApiView, NextOfKinDetailApiView, UserProfileListView, UserProfileDetailsView

urlpatterns = [
    path('all/', UserProfileListView.as_view(), name='all_profiles'),
    path('my-profile/', UserProfileDetailsView.as_view(), name='user_profile_detail'),
    path('my-profile/next-of-kin/', NextOfKinApiView.as_view(), name='next_of_kin_list'),
    path('my-profile/next-of-kin/<uuid:pk>/', NextOfKinDetailApiView.as_view(), name='next_of_kin_detail'),
]
