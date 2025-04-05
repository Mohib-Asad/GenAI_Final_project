"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),                # Root URL for the main page
    path('chat/carmen/', views.chatbot_view, name='chat_carmen'),
    path('rag/sirius/', views.rag_view, name='rag_sirius'),
    path('proofread/myne/', views.proofreader_view, name='proofread_myne'),
    path('scrape/ped/', views.wikipedia_view, name='scrape_ped'),
]