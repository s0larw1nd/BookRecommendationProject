from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name="home"),
    path('book/<str:pk>/', views.BookView.as_view(), name="book"),
    path('user/<str:pk>/', views.UserView.as_view(), name="user"),
    path('author/<str:pk>/', views.AuthorView.as_view(), name="author"),
    path('publisher/<str:pk>/', views.PublisherView.as_view(), name="publisher"),
    path('login/', views.Login.as_view(), name="login"),
    path('logout/', views.Logout.as_view(), name="logout"),
    path('register/', views.Register.as_view(), name="register"),
    path('delete-rating/<str:pk>/', views.DeleteRating.as_view(), name="delete-rating"),
]