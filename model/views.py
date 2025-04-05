from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
import json
import sys
# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Now import utils using an absolute import
from model.utils import (
    get_chat_response, 
    process_document_for_rag, 
    scrape_wikipedia, 
    proofread_document,
    handle_uploaded_file
)

def index(request):
    """Main view for the QuadraNex-AI interface"""
    return render(request, 'index.html')

def json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)

@csrf_exempt
@require_http_methods(["POST"])
def chatbot_view(request):
    try:
        data = json.loads(request.body)
        user_query = data.get('message', '')
        
        if not user_query:
            return json_error('No message provided')
        
        response = get_chat_response(user_query)
        return JsonResponse({'response': response})
    except Exception as e:
        return json_error(f'Chat error: {str(e)}', status=500)

@csrf_exempt
@require_http_methods(["POST"])
def rag_view(request):
    try:
        uploaded_file = request.FILES.get('file')
        query = request.POST.get('query')
        
        if not uploaded_file or not query:
            return json_error('Both file and query are required')

        # Handle file upload
        file_info = handle_uploaded_file(uploaded_file)
        
        # Process the document with RAG - extract the path from the file_info dictionary
        response = process_document_for_rag(file_info['path'], query)
        
        return JsonResponse({'response': response})
    except Exception as e:
        return json_error(f'RAG processing error: {str(e)}', status=500)

@csrf_exempt
@require_http_methods(["POST"])
def wikipedia_view(request):
    try:
        data = json.loads(request.body)
        article_url = data.get('url', '')
        
        if not article_url:
            return json_error('No Wikipedia URL provided')
        
        if 'wikipedia.org' not in article_url:
            return json_error('Not a valid Wikipedia URL')
        
        result = scrape_wikipedia(article_url)
        
        if 'error' in result:
            return json_error(result['error'], status=500)
        
        return JsonResponse({
            'title': result['title'],
            'content': result['content'],
            'summary': result.get('summary', ''),
            'images': result.get('images', []),
            'headings': result.get('headings', [])
        })
    except Exception as e:
        return json_error(f'Wikipedia error: {str(e)}', status=500)

@csrf_exempt
@require_http_methods(["POST"])
def proofreader_view(request):
    try:
        uploaded_file = request.FILES.get('file')
        
        if not uploaded_file:
            return json_error('Document is required')
        
        file_info = handle_uploaded_file(uploaded_file)
        result = proofread_document(file_info['path'])
        
        return JsonResponse({'response': result if result else 'Document proofread successfully', 'error': ''})
    except Exception as e:
        return json_error(f'Proofreading error: {str(e)}', status=500)