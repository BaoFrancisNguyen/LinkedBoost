# app.py - LinkedBoost avec Flask-SocketIO
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import logging
import asyncio
import threading
import uuid
from datetime import datetime
from models.ai_generator import LinkedBoostAI
from config import Config

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialisation de SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialisation du générateur IA
ai_generator = LinkedBoostAI()

# Stockage des sessions de scraping actives
active_scraping_sessions = {}

# Chargement des données d'exemple
def load_example_data():
    """Charge les données d'exemple depuis le fichier JSON"""
    try:
        with open('data/examples.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Fichier examples.json non trouvé")
        return {
            "profiles": [],
            "job_offers": [],
            "companies": []
        }

example_data = load_example_data()

# Routes Flask normales
@app.route('/')
def dashboard():
    """Dashboard principal de LinkedBoost"""
    stats = {
        'messages_generated': 150,
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

@app.route('/admin/scraper')
def scraper_dashboard():
    """Dashboard d'administration du scraping"""
    return render_template('admin/scraper_dashboard.html')

@app.route('/admin/knowledge')
def knowledge_base_page():
    """Page de gestion de la base de connaissances"""
    return render_template('admin/knowledge_base.html')

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
        logger.error(f"Erreur génération message: {e}")
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
        logger.error(f"Erreur génération lettre: {e}")
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
        logger.error(f"Erreur génération email: {e}")
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
        logger.error(f"Erreur analyse profil: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Statut de l'API et d'Ollama"""
    try:
        system_status = ai_generator.get_system_status()
        
        return jsonify({
            'ollama_available': ai_generator.is_available(),
            'model': ai_generator.model,
            'features': system_status.get('features', {}),
            'capabilities': system_status.get('capabilities', {}),
            'rag_enabled': system_status.get('rag_enabled', False)
        })
    except Exception as e:
        logger.error(f"Erreur statut API: {e}")
        return jsonify({
            'ollama_available': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/start', methods=['POST'])
def start_scraping():
    """Lance le scraping des offres d'emploi avec WebSocket"""
    try:
        # Import conditionnel
        try:
            from models.scraper import ScrapingOrchestrator
            scraping_available = True
        except ImportError as e:
            logger.warning(f"Scraping non disponible: {e}")
            scraping_available = False
        
        if not scraping_available:
            return jsonify({
                'success': False,
                'error': 'Modules de scraping non disponibles'
            }), 503
        
        data = request.get_json() or {}
        sources = data.get('sources', ['wttj'])
        max_jobs = data.get('max_jobs', 25)
        delay = data.get('delay', 1.0)
        session_id = data.get('session_id')
        
        logger.info(f"🚀 Démarrage scraping - Sources: {sources}, Max: {max_jobs}, Session: {session_id}")
        
        # Lancer le scraping dans un thread séparé
        def run_scraping_thread():
            try:
                orchestrator = ScrapingOrchestrator()
                
                # Créer une nouvelle boucle d'événements
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Lancer le scraping avec callbacks WebSocket
                    stats = loop.run_until_complete(
                        run_scraping_with_websocket(orchestrator, sources, session_id)
                    )
                    
                    # Envoyer le résultat final
                    socketio.emit('scraping_completed', {
                        'session_id': session_id,
                        'stats': stats,
                        'success': True
                    }, namespace='/scraping')
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"Erreur thread scraping: {e}")
                socketio.emit('scraping_error', {
                    'session_id': session_id,
                    'error': str(e)
                }, namespace='/scraping')
        
        # Démarrer le thread
        scraping_thread = threading.Thread(target=run_scraping_thread)
        scraping_thread.daemon = True
        scraping_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Scraping démarré',
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur démarrage scraping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

async def run_scraping_with_websocket(orchestrator, sources, session_id):
    """Lance le scraping avec émission WebSocket"""
    
    # Émission des logs pendant le scraping
    def emit_log(level, message):
        socketio.emit('scraping_log', {
            'session_id': session_id,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': message
        }, namespace='/scraping')
    
    def emit_progress(phase, progress, **kwargs):
        socketio.emit('scraping_progress', {
            'session_id': session_id,
            'phase': phase,
            'progress_percent': progress,
            **kwargs
        }, namespace='/scraping')
    
    try:
        emit_log('info', '🚀 Initialisation du scraping...')
        emit_progress('Initialisation...', 5)
        
        emit_log('info', '📡 Connexion aux sources...')
        emit_progress('Connexion aux sources...', 15)
        
        emit_log('info', f'🔍 Scraping de {len(sources)} sources...')
        emit_progress('Extraction des offres...', 30)
        
        # Lancer le scraping réel
        stats = await orchestrator.run_full_scrape(sources)
        
        emit_log('info', '🔄 Traitement des données...')
        emit_progress('Traitement des données...', 70)
        
        emit_log('info', '🧠 Génération des embeddings...')
        emit_progress('Génération des embeddings...', 85)
        
        emit_log('info', '💾 Sauvegarde en base...')
        emit_progress('Sauvegarde...', 95)
        
        emit_log('success', f'✅ Scraping terminé: {stats.get("total_jobs", 0)} offres')
        emit_progress('Terminé', 100, total_jobs=stats.get('total_jobs', 0))
        
        return stats
        
    except Exception as e:
        emit_log('error', f'❌ Erreur: {str(e)}')
        raise

@app.route('/api/knowledge/search', methods=['POST'])
def search_knowledge():
    """Recherche dans la base de connaissances"""
    try:
        try:
            from models.knowledge_base import KnowledgeBase
            kb_available = True
        except ImportError:
            kb_available = False
        
        if not kb_available:
            return jsonify({
                'success': False,
                'error': 'Base de connaissances non disponible'
            }), 503
        
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        limit = data.get('limit', 10)
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        kb = KnowledgeBase()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                kb.search_jobs(query, filters, limit)
            )
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Erreur recherche: {e}")
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
            kb_available = True
        except ImportError:
            kb_available = False
        
        if not kb_available:
            return jsonify({
                'success': True,
                'insights': {
                    'total_jobs': 0,
                    'message': 'Base de connaissances non disponible'
                }
            })
        
        kb = KnowledgeBase()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            insights = loop.run_until_complete(kb.get_market_insights())
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Erreur analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# WebSocket Events
@socketio.on('connect', namespace='/scraping')
def on_scraping_connect():
    logger.info("🔌 Client connecté au namespace /scraping")
    emit('connection_confirmed', {'status': 'connected'})

@socketio.on('disconnect', namespace='/scraping')
def on_scraping_disconnect():
    logger.info("🔌 Client déconnecté du namespace /scraping")

@socketio.on('start_scraping_session', namespace='/scraping')
def on_start_scraping_session(data):
    """Démarre une session de scraping"""
    session_id = str(uuid.uuid4())
    sources = data.get('sources', ['wttj'])
    
    active_scraping_sessions[session_id] = {
        'sources': sources,
        'started_at': datetime.now().isoformat(),
        'status': 'initialized'
    }
    
    logger.info(f"📡 Session de scraping créée: {session_id}")
    emit('session_started', {'session_id': session_id})

@socketio.on('stop_scraping', namespace='/scraping')
def on_stop_scraping(data):
    """Arrête une session de scraping"""
    session_id = data.get('session_id')
    
    if session_id in active_scraping_sessions:
        active_scraping_sessions[session_id]['status'] = 'cancelled'
        logger.info(f"⏹️ Session de scraping arrêtée: {session_id}")
        emit('scraping_cancelled', {'session_id': session_id})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/admin')
def admin_dashboard():
    """Page d'administration principale"""
    return render_template('admin/dashboard.html')

if __name__ == '__main__':
    # Vérification de la configuration au démarrage
    print("🚀 LinkedBoost - Démarrage de l'application")
    print(f"📡 Ollama disponible: {ai_generator.is_available()}")
    print(f"🤖 Modèle: {ai_generator.model}")
    print(f"🧠 RAG activé: {ai_generator.get_system_status().get('rag_enabled', False)}")
    print(f"🔌 WebSocket activé: True")
    
    if not ai_generator.is_available():
        print("⚠️  Ollama n'est pas disponible. Démarrez-le avec: ollama serve")
    
    # Vérification des modules optionnels
    optional_modules = []
    try:
        from models.scraper import ScrapingOrchestrator
        optional_modules.append("✅ Scraping")
    except ImportError:
        optional_modules.append("❌ Scraping (dépendances manquantes)")
    
    try:
        from models.knowledge_base import KnowledgeBase
        optional_modules.append("✅ Base de connaissances")
    except ImportError:
        optional_modules.append("❌ Base de connaissances (dépendances manquantes)")
    
    print("📦 Modules disponibles:")
    for module in optional_modules:
        print(f"   {module}")
    
    print("🌐 Démarrage du serveur sur http://localhost:5000")
    
    # Démarrage avec SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)