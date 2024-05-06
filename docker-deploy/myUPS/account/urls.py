from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('user_login/', views.user_login, name="user_login"),
    path('logout/', views.logout_view, name='logout'),

    path('register/', views.register, name="register"),
    path('get_status/', views.get_status, name="get_status"),
    path('show_packages/', views.show_packages, name="show_packages"),
    path('modify_dest/<int:package_id>/', views.modify_dest, name='modify_dest'),
    path('user_home/', views.user_home, name='user_home'),
    path('get_status/', views.get_status, name='get_status'),
    path('product_details/<int:package_id>/', views.product_details, name="product_details"),
    path('delivery_map/<int:package_id>/', views.delivery_map, name="delivery_map"),
]

