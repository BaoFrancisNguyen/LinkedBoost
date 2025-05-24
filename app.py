# app.py - LinkedBoost Application principale
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from models.ai_generator import LinkedBoostAI
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialisation du générateur IA
ai_generator = LinkedBoostAI()

# Chargement des données d'exemple
def load_example_data():
    """Charge les données d'exemple depuis le fichier JSON"""
    try:
        with open('data/examples.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "profiles": [],
            "job_offers": [],
            "companies": []
        }

example_data = load_example_data()

@app.route('/')
def dashboard():
    """Dashboard principal de LinkedBoost"""
    stats = {
        'messages_generated': 150,  # Données statiques pour le moment
        'cover_letters_generated': 45,
        'emails_generated': 78,
        'success_rate': 85
    }
    return render_template('index.html', stats=stats, ollama_status=ai_generator.is_available())

@app.route('/generate/message')
def message_generator_page():
    """Page génération de messages LinkedIn"""
    return render_template('message_generator.html', 
                         profiles=example_data.get('profiles', []),
                         companies=example_data.get('companies', []))

@app.route('/generate/cover-letter')
def cover_letter_page():
    """Page génération de lettres de motivation"""
    return render_template('cover_letter.html',
                         job_offers=example_data.get('job_offers', []),
                         profiles=example_data.get('profiles', []))

@app.route('/generate/email')
def email_generator_page():
    """Page génération d'emails"""
    return render_template('email_generator.html',
                         profiles=example_data.get('profiles', []))

@app.route('/profile/analyze')
def profile_analyzer_page():
    """Page d'analyse de profil LinkedIn"""
    return render_template('profile_analyzer.html')

# API Endpoints
@app.route('/api/generate/message', methods=['POST'])
def generate_linkedin_message():
    """API pour générer des messages LinkedIn personnalisés"""
    data = request.get_json()
    
    required_fields = ['message_type', 'recipient_name', 'context']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Champs requis manquants'}), 400
    
    try:
        message = ai_generator.generate_linkedin_message(
            message_type=data['message_type'],
            recipient_name=data['recipient_name'],
            recipient_company=data.get('recipient_company', ''),
            recipient_position=data.get('recipient_position', ''),
            context=data['context'],
            sender_name=data.get('sender_name', 'Utilisateur'),
            common_connections=data.get('common_connections', []),
            personalization_notes=data.get('personalization_notes', '')
        )
        
        return jsonify({
            'success': True,
            'message': message,
            'type': data['message_type']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/cover-letter', methods=['POST'])
def generate_cover_letter():
    """API pour générer des lettres de motivation"""
    data = request.get_json()
    
    required_fields = ['job_title', 'company_name', 'applicant_name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Champs requis manquants'}), 400
    
    try:
        cover_letter = ai_generator.generate_cover_letter(
            job_title=data['job_title'],
            company_name=data['company_name'],
            job_description=data.get('job_description', ''),
            applicant_name=data['applicant_name'],
            applicant_experience=data.get('applicant_experience', ''),
            applicant_skills=data.get('applicant_skills', []),
            tone=data.get('tone', 'professional')
        )
        
        return jsonify({
            'success': True,
            'cover_letter': cover_letter,
            'job_title': data['job_title'],
            'company_name': data['company_name']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/email', methods=['POST'])
def generate_email():
    """API pour générer des emails de networking"""
    data = request.get_json()
    
    required_fields = ['email_type', 'recipient_name', 'subject_context']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Champs requis manquants'}), 400
    
    try:
        email = ai_generator.generate_networking_email(
            email_type=data['email_type'],
            recipient_name=data['recipient_name'],
            recipient_company=data.get('recipient_company', ''),
            subject_context=data['subject_context'],
            sender_name=data.get('sender_name', 'Utilisateur'),
            meeting_purpose=data.get('meeting_purpose', ''),
            background_info=data.get('background_info', '')
        )
        
        return jsonify({
            'success': True,
            'email': email,
            'type': data['email_type']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/profile', methods=['POST'])
def analyze_profile():
    """API pour analyser un profil LinkedIn"""
    data = request.get_json()
    
    if 'profile_text' not in data:
        return jsonify({'error': 'Texte du profil requis'}), 400
    
    try:
        analysis = ai_generator.analyze_linkedin_profile(
            profile_text=data['profile_text'],
            target_role=data.get('target_role', ''),
            industry=data.get('industry', '')
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Statut de l'API et d'Ollama"""
    return jsonify({
        'ollama_available': ai_generator.is_available(),
        'model': ai_generator.model,
        'features': {
            'message_generation': True,
            'cover_letter_generation': True,
            'email_generation': True,
            'profile_analysis': True
        }
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Vérification de la configuration au démarrage
    print("🚀 LinkedBoost - Démarrage de l'application")
    print(f"📡 Ollama disponible: {ai_generator.is_available()}")
    print(f"🤖 Modèle: {ai_generator.model}")
    
    if not ai_generator.is_available():
        print("⚠️  Ollama n'est pas disponible. Démarrez-le avec: ollama serve")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

# Nouvelles routes API dans app.py (à ajouter)
@app.route('/api/scraping/start', methods=['POST'])
def start_scraping():
    """Lance le scraping des offres d'emploi"""
    try:
        from models.scraper import ScrapingOrchestrator
        
        data = request.get_json() or {}
        sources = data.get('sources', ['wttj'])  # Par défaut WTTJ
        
        orchestrator = ScrapingOrchestrator()
        
        # Lancement asynchrone (en production, utiliser Celery)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        stats = loop.run_until_complete(orchestrator.run_full_scrape(sources))
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f"Scraping terminé : {stats.get('total_jobs', 0)} offres collectées"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/knowledge/search', methods=['POST'])
def search_knowledge():
    """Recherche dans la base de connaissances"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        from models.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            kb.search_jobs(query, filters, limit)
        )
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analytics/market', methods=['GET'])
def get_market_analytics():
    """Retourne les analytics du marché de l'emploi"""
    try:
        from models.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        insights = loop.run_until_complete(kb.get_market_insights())
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/enhanced', methods=['POST'])
def generate_enhanced_content():
    """Génération de contenu enrichie avec RAG"""
    try:
        data = request.get_json()
        content_type = data.get('type')  # 'message', 'cover_letter', 'email'
        
        ai_generator = LinkedBoostAI()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if content_type == 'message':
            result = loop.run_until_complete(
                ai_generator.generate_linkedin_message_enhanced(**data)
            )
        elif content_type == 'cover_letter':
            result = loop.run_until_complete(
                ai_generator.generate_cover_letter_enhanced(**data)
            )
        else:
            return jsonify({'error': 'Type de contenu non supporté'}), 400
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500