import os
import json
import time
from groq import Groq
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Initialize Groq client
def get_groq_client():
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set. Please add it to your environment variables.")
    return Groq(api_key=api_key)

# Simple ChatBot utility
def get_chat_response(query, model_name="llama3-70b-8192"):
    try:
        client = get_groq_client()
        
        # Add a system prompt to improve response quality
        system_prompt = """You are Carmen, the friendly and knowledgeable AI assistant for QuadraNex-AI.
        You provide clear, accurate, and concise information with a helpful and conversational tone.
        Format your responses with proper HTML for better readability, including headings, lists, and highlighting of important information when appropriate.
        If you're unsure about something, acknowledge it rather than making up information.
        You can discuss a wide range of topics including technology, science, arts, history, and more.
        When providing explanations, use analogies and examples to make complex concepts easier to understand."""
        
        # Check if the query is asking for specific formatting
        formatting_keywords = ["format", "html", "style", "code", "markdown", "highlight"]
        should_format = any(keyword in query.lower() for keyword in formatting_keywords)
        
        # Add formatting instructions if needed
        if should_format:
            system_prompt += """
            When formatting code or technical content:
            - Use <pre><code> tags for code blocks
            - Use appropriate syntax highlighting when possible
            - Format lists with proper HTML tags
            - Use <em> and <strong> for emphasis
            """
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model=model_name,
            temperature=0.7,
            max_tokens=2048
        )
        
        chat_response = response.choices[0].message.content
        
        # Add basic formatting if not already present
        if "<" not in chat_response and ">" not in chat_response:
            # Convert markdown-style formatting to HTML
            chat_response = chat_response.replace("**", "<strong>").replace("**", "</strong>")
            chat_response = chat_response.replace("*", "<em>").replace("*", "</em>")
            
            # Format paragraphs
            paragraphs = chat_response.split("\n\n")
            formatted_paragraphs = [f"<p>{p}</p>" for p in paragraphs if p.strip()]
            chat_response = "\n".join(formatted_paragraphs)
        
        return chat_response
    except ValueError as e:
        # Handle missing API key
        return f"<div class='error-message'>Configuration Error: {str(e)}</div>"
    except Exception as e:
        # Handle other errors
        return f"<div class='error-message'>Sorry, I encountered an error: {str(e)}</div>"

# RAG System utility
def process_document_for_rag(file_path, query):
    try:
        client = get_groq_client()
        
        # Read the document content
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                document_content = file.read()
            
            # Get file extension to determine document type
            file_extension = os.path.splitext(file_path)[1].lower()
            document_type = "text"
            if file_extension in ['.md', '.markdown']:
                document_type = "markdown"
            elif file_extension in ['.tex']:
                document_type = "LaTeX"
            elif file_extension in ['.html', '.htm']:
                document_type = "HTML"
            elif file_extension in ['.pdf']:
                document_type = "PDF"
            
            # Create a system prompt for the RAG system
            system_prompt = """You are Sirius, an advanced AI document analysis assistant.
            Your task is to provide comprehensive and accurate answers to questions based on the document content.
            If the answer isn't in the document, acknowledge that rather than making up information.
            Format your responses with proper HTML for better readability, including headings, lists, and highlighting of important information.
            Include relevant quotes from the document to support your answers."""
            
            # Create a prompt for the RAG system
            rag_prompt = f"""
            Document Type: {document_type}
            
            Document Content:
            {document_content[:20000]}  # Increased content size limit
            
            User Question: {query}
            
            Please provide a comprehensive answer to the question based solely on the document content.
            Format your response with the following sections:
            1. Direct Answer: A concise answer to the question
            2. Supporting Evidence: Relevant quotes from the document that support your answer
            3. Additional Context: Any additional information from the document that might be helpful
            4. Related Information: Other relevant information from the document that relates to the question
            
            Use proper HTML formatting for better readability.
            """
            
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": rag_prompt}
                ],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=3000
            )
            
            rag_result = response.choices[0].message.content
            
            # Format the result with HTML for better display
            formatted_result = f"""
            <div class="rag-result">
                {rag_result}
            </div>
            """
            
            return formatted_result
        except Exception as e:
            return f"<div class='error-message'>Error processing document: {str(e)}</div>"
    except ValueError as e:
        # Handle missing API key
        return f"<div class='error-message'>Configuration Error: {str(e)}</div>"
    except Exception as e:
        # Handle other errors
        return f"<div class='error-message'>Sorry, I encountered an error: {str(e)}</div>"

# Wikipedia Scraper utility
def scrape_wikipedia(article_url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Setup Chrome WebDriver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Navigate to Wikipedia article
        driver.get(article_url)
        
        # Extract article title
        article_title = driver.find_element(By.ID, "firstHeading").text
        
        # Extract article content
        article_content = driver.find_element(By.ID, "bodyContent").text
        
        # Extract images
        image_elements = driver.find_elements(By.CSS_SELECTOR, ".image img")
        image_urls = [img.get_attribute("src") for img in image_elements[:5]]  # Limit to 5 images
        
        # Extract headings
        heading_elements = driver.find_elements(By.CSS_SELECTOR, "#bodyContent h2, #bodyContent h3")
        headings = [heading.text.replace("[edit]", "").strip() for heading in heading_elements]
        
        # Format content with headings as sections
        formatted_content = ""
        content_sections = driver.find_elements(By.CSS_SELECTOR, "#bodyContent > *")
        for section in content_sections:
            if section.tag_name in ["h2", "h3", "h4"]:
                section_title = section.text.replace("[edit]", "").strip()
                section_id = section_title.lower().replace(" ", "-")
                formatted_content += f'<h3 id="section-{section_id}">{section_title}</h3>\n'
            elif section.tag_name in ["p", "ul", "ol", "div"]:
                formatted_content += f'<div class="wiki-section-content">{section.get_attribute("innerHTML")}</div>\n'
        
        driver.quit()
        
        # Generate a summary using Groq API
        try:
            client = get_groq_client()
            
            summary_prompt = f"""
            Please provide a concise summary of this Wikipedia article about {article_title}.
            The summary should be about 3-4 paragraphs and highlight the most important information.
            Format the summary with HTML for better readability.
            
            Article content:
            {article_content[:5000]}
            """
            
            summary_response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes Wikipedia articles."},
                    {"role": "user", "content": summary_prompt}
                ],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=500
            )
            
            summary = summary_response.choices[0].message.content
        except Exception as e:
            summary = f"<p>Error generating summary: {str(e)}</p>"
        
        return {
            "title": article_title,
            "content": formatted_content,
            "summary": summary,
            "images": image_urls,
            "headings": headings
        }
    except Exception as e:
        return {"error": str(e)}

# Document Proofreader utility
def proofread_document(file_path):
    try:
        client = get_groq_client()
        
        # Read the document content
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                document_content = file.read()
            
            # Get file extension to determine document type
            file_extension = os.path.splitext(file_path)[1].lower()
            document_type = "text"
            if file_extension in ['.md', '.markdown']:
                document_type = "markdown"
            elif file_extension in ['.tex']:
                document_type = "LaTeX"
            elif file_extension in ['.html', '.htm']:
                document_type = "HTML"
            
            # Create a system prompt for the proofreading
            system_prompt = """You are Myne, an advanced AI document proofreader assistant.
            Your task is to provide comprehensive analysis and suggestions for improving the document.
            Focus on grammar, spelling, tone, style, clarity, and coherence.
            Provide your feedback in a structured HTML format with clear sections and highlighting of issues."""
            
            # Create a prompt for the proofreading
            proofread_prompt = f"""
            Please perform a detailed analysis of the following {document_type} document:
            
            {document_content[:15000]}  # Increased content size limit
            
            Provide your analysis in the following format:
            
            1. SUMMARY: A brief overview of the document and its main issues
            2. GRAMMAR & SPELLING: List all grammar and spelling errors with corrections
            3. STYLE & TONE: Analyze the writing style and tone, suggesting improvements
            4. STRUCTURE & COHERENCE: Evaluate the document's structure and flow
            5. READABILITY: Assess the document's readability and suggest improvements
            6. ENHANCED VERSION: Provide an improved version of the document
            
            Format your response in HTML with appropriate headings, lists, and highlighting of issues.
            """
            
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": proofread_prompt}
                ],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=3000
            )
            
            proofreading_result = response.choices[0].message.content
            
            # Format the result with HTML for better display
            formatted_result = f"""
            <div class="proofreading-result">
                {proofreading_result}
            </div>
            """
            
            return formatted_result
        except Exception as e:
            return f"<div class='error-message'>Error proofreading document: {str(e)}</div>"
    except ValueError as e:
        # Handle missing API key
        return f"<div class='error-message'>Configuration Error: {str(e)}</div>"
    except Exception as e:
        # Handle other errors
        return f"<div class='error-message'>Sorry, I encountered an error: {str(e)}</div>"

# File handling utility
def handle_uploaded_file(file):
    file_path = default_storage.save(f'uploads/{file.name}', ContentFile(file.read()))
    return os.path.join(settings.MEDIA_ROOT, file_path)