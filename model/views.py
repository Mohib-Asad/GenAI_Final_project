from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
import json
import sys
# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Now import utils using an absolute import
from utils import (
    get_chat_response, 
    process_document_for_rag, 
    scrape_wikipedia, 
    proofread_document,
    handle_uploaded_file
)

def index(request):
    """Main view for the QuadraNex-AI interface"""
    return render(request, 'index.html')

@csrf_exempt
def chatbot_view(request):
    """View for the Simple ChatBot model"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_query = data.get('message', '')
            
            if not user_query:
                return JsonResponse({'error': 'No message provided'}, status=400)
                
            response = get_chat_response(user_query)
            return JsonResponse({'response': response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@csrf_exempt
def rag_view(request):
    """View for the RAG System model"""
    if request.method == 'POST':
        try:
            # Handle file upload
            uploaded_file = request.FILES.get('file')
            query = request.POST.get('query')
            
            if not uploaded_file or not query:
                return JsonResponse({
                    'error': 'Both file and query are required'
                }, status=400)
            
            # Save the uploaded file
            file_path = handle_uploaded_file(uploaded_file)
            
            # Process the document with RAG
            response = process_document_for_rag(file_path, query)
            
            return JsonResponse({'response': response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@csrf_exempt
def wikipedia_view(request):
    """View for the Wikipedia Scraper model"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article_url = data.get('url', '')
            
            if not article_url:
                return JsonResponse({'error': 'No Wikipedia URL provided'}, status=400)
                
            if 'wikipedia.org' not in article_url:
                return JsonResponse({'error': 'Not a valid Wikipedia URL'}, status=400)
                
            result = scrape_wikipedia(article_url)
            
            if 'error' in result:
                return JsonResponse({'error': result['error']}, status=500)
                
            return JsonResponse({
                'title': result['title'],
                'content': result['content'],
                'summary': result.get('summary', ''),
                'images': result.get('images', []),
                'headings': result.get('headings', [])
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

@csrf_exempt
def proofreader_view(request):
    """View for the Document Proofreader model"""
    if request.method == 'POST':
        try:
            # Handle file upload
            uploaded_file = request.FILES.get('file')
            
            if not uploaded_file:
                return JsonResponse({'error': 'Document is required'}, status=400)
            
            # Save the uploaded file
            file_path = handle_uploaded_file(uploaded_file)
            
            # Proofread the document
            result = proofread_document(file_path)
            
            return JsonResponse({'response': result})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST method is allowed'}, status=405)