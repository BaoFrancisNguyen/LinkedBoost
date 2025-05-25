# app.py - LinkedBoost Application complète
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
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

# ===========================
# ROUTES PRINCIPALES
# ===========================

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

# ===========================
# ROUTES ADMIN
# ===========================

@app.route('/admin')
def admin_dashboard():
    """Dashboard d'administration principal"""
    return render_template('admin/dashboard.html')

@app.route('/admin/scraper')
def admin_scraper():
    """Interface d'administration du scraping"""
    return render_template('admin/scraper_dashboard.html')

@app.route('/admin/knowledge-base')
def admin_knowledge_base():
    """Interface de gestion de la base de connaissances"""
    return render_template('admin/knowledge_base.html')

# ===========================
# API GÉNÉRATION
# ===========================

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

# ===========================
# API GÉNÉRATION ENRICHIE
# ===========================

@app.route('/api/generate/enhanced', methods=['POST'])
def generate_enhanced_content():
    """Génération de contenu enrichie avec RAG"""
    try:
        data = request.get_json()
        content_type = data.get('type')  # 'message', 'cover_letter', 'email'
        
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

# ===========================
# API ADMIN
# ===========================

@app.route('/api/admin/scraping/status')
def get_scraping_status():
    """Statut détaillé du système de scraping"""
    try:
        # Import conditionnel pour éviter les erreurs si pas configuré
        try:
            from models.scraper import ScrapingOrchestrator
            orchestrator = ScrapingOrchestrator()
            scraping_stats = orchestrator.get_stats()
            scraping_available = True
        except ImportError:
            scraping_stats = {"error": "Scraping non configuré"}
            scraping_available = False
        
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            kb_stats = kb.get_stats()
            kb_available = True
        except ImportError:
            kb_stats = {"error": "Base de connaissances non configurée"}
            kb_available = False
        
        return jsonify({
            'success': True,
            'scraping': {
                'available': scraping_available,
                'stats': scraping_stats
            },
            'knowledge_base': {
                'available': kb_available,
                'stats': kb_stats
            },
            'ollama': {
                'available': ai_generator.is_available(),
                'model': ai_generator.model
            },
            'rag_enabled': getattr(ai_generator, 'rag_enabled', False)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/scraping/config', methods=['GET', 'POST'])
def scraping_config():
    """Configuration du scraping"""
    if request.method == 'GET':
        return jsonify({
            'sources': ['wttj', 'linkedin', 'indeed'],
            'active_sources': ['wttj'],
            'max_jobs': Config.MAX_JOBS_PER_SCRAPE,
            'interval_hours': Config.SCRAPING_INTERVAL_HOURS,
            'request_delay': Config.REQUEST_DELAY
        })
    
    if request.method == 'POST':
        data = request.get_json()
        # Ici vous pourriez sauvegarder la config
        # Pour l'instant, on retourne just un succès
        return jsonify({
            'success': True,
            'message': 'Configuration sauvegardée'
        })

@app.route('/api/admin/knowledge/stats')
def knowledge_stats():
    """Statistiques détaillées de la base de connaissances"""
    try:
        from models.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Statistiques générales
        stats = kb.get_stats()
        
        # Insights marché
        insights = loop.run_until_complete(kb.get_market_insights())
        
        return jsonify({
            'success': True,
            'stats': stats,
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Base de connaissances non disponible'
        })

@app.route('/api/admin/system/health')
def system_health():
    """Vérification de santé complète du système"""
    health = {
        'timestamp': datetime.now().isoformat(),
        'components': {}
    }
    
    # Test Ollama
    try:
        ollama_available = ai_generator.is_available()
        health['components']['ollama'] = {
            'status': 'healthy' if ollama_available else 'unhealthy',
            'model': ai_generator.model,
            'url': Config.OLLAMA_BASE_URL
        }
    except Exception as e:
        health['components']['ollama'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Test Base de données
    try:
        import sqlite3
        import os
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect('data/linkedboost.db')
        conn.execute('SELECT 1')
        conn.close()
        health['components']['database'] = {'status': 'healthy'}
    except Exception as e:
        health['components']['database'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Test Scraping
    try:
        from models.scraper import ScrapingOrchestrator
        health['components']['scraping'] = {'status': 'available'}
    except ImportError:
        health['components']['scraping'] = {
            'status': 'not_configured',
            'message': 'Modules de scraping non installés'
        }
    
    # Test RAG
    try:
        rag_status = getattr(ai_generator, 'rag_enabled', False)
        health['components']['rag'] = {
            'status': 'enabled' if rag_status else 'disabled'
        }
    except Exception as e:
        health['components']['rag'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Statut global
    all_healthy = all(
        comp.get('status') in ['healthy', 'enabled', 'available'] 
        for comp in health['components'].values()
    )
    
    health['overall_status'] = 'healthy' if all_healthy else 'degraded'
    
    return jsonify(health)

# ===========================
# API SCRAPING
# ===========================

@app.route('/api/scraping/start', methods=['POST'])
def start_scraping():
    """Lance le scraping des offres d'emploi"""
    try:
        # Import conditionnel
        try:
            from models.scraper import ScrapingOrchestrator
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Modules de scraping non installés. Consultez le guide d\'installation.'
            }), 500
        
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
        
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Base de connaissances non configurée'
            }), 500
        
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
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Base de connaissances non configurée'
            }), 500
        
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

# ===========================
# API STATUS ET UTILITAIRES
# ===========================

@app.route('/api/status')
def api_status():
    """Statut de l'API et d'Ollama"""
    try:
        # Tentative de récupération des stats de la base de connaissances
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            kb_stats = kb.get_stats()
            kb_available = True
        except:
            kb_stats = {}
            kb_available = False
        
        status = {
            'ollama_available': ai_generator.is_available(),
            'model': ai_generator.model,
            'rag_enabled': getattr(ai_generator, 'rag_enabled', False),
            'knowledge_base_available': kb_available,
            'features': {
                'message_generation': True,
                'cover_letter_generation': True,
                'email_generation': True,
                'profile_analysis': True,
                'enhanced_with_rag': getattr(ai_generator, 'rag_enabled', False),
                'scraping': kb_available,
                'market_insights': kb_available,
                'total_jobs': kb_stats.get('total_jobs', 0) if kb_available else 0
            }
        }
        
        # Ajout des stats de la base si disponible
        if kb_available:
            status['knowledge_base'] = kb_stats
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'ollama_available': False,
            'features': {}
        }), 500

# ===========================
# GESTION D'ERREURS
# ===========================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ===========================
# CONTEXTE GLOBAL
# ===========================

@app.context_processor
def inject_global_vars():
    """Injecte des variables globales dans tous les templates"""
    return {
        'admin_nav': [
            {'url': '/admin', 'title': 'Dashboard Admin', 'icon': 'fas fa-tachometer-alt'},
            {'url': '/admin/scraper', 'title': 'Scraping', 'icon': 'fas fa-robot'},
            {'url': '/admin/knowledge-base', 'title': 'Base de connaissances', 'icon': 'fas fa-brain'},
        ],
        'app_version': '1.0.0',
        'current_year': datetime.now().year
    }

# ===========================
# LANCEMENT DE L'APPLICATION
# ===========================

if __name__ == '__main__':
    # Création des dossiers nécessaires
    import os
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Vérification de la configuration au démarrage
    print("🚀 LinkedBoost - Démarrage de l'application")
    print(f"📡 Ollama disponible: {ai_generator.is_available()}")
    print(f"🤖 Modèle: {ai_generator.model}")
    print(f"🧠 RAG activé: {getattr(ai_generator, 'rag_enabled', False)}")
    
    # Vérification des modules optionnels
    try:
        from models.scraper import ScrapingOrchestrator
        print("✅ Module de scraping disponible")
    except ImportError:
        print("⚠️  Module de scraping non configuré")
    
    try:
        from models.knowledge_base import KnowledgeBase
        print("✅ Base de connaissances disponible")
    except ImportError:
        print("⚠️  Base de connaissances non configurée")
    
    if not ai_generator.is_available():
        print("⚠️  Ollama n'est pas disponible. Démarrez-le avec: ollama serve")
        print("💡 Modèles requis: ollama pull mistral:latest && ollama pull nomic-embed-text")
    
    print("🌐 Interface admin disponible sur: http://localhost:5000/admin")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)