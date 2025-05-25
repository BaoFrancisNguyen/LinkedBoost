# app.py - Routes mises à jour avec support d'annulation et WebSocket
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import uuid
from datetime import datetime
from models.ai_generator import LinkedBoostAI
from config import Config

# Import conditionnel pour les WebSockets et le scraping
try:
    from utils.websocket_logger import ScrapingProgressTracker, init_websocket_logging
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialisation SocketIO pour les logs temps réel
if WEBSOCKET_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*")
    init_websocket_logging(app, socketio)
else:
    socketio = None

# Initialisation du générateur IA
ai_generator = LinkedBoostAI()

# Store global pour les sessions de scraping
scraping_sessions = {}

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
# ROUTES PRINCIPALES (inchangées)
# ===========================

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
    return render_template('message_generator.html', 
                         profiles=example_data.get('profiles', []),
                         companies=example_data.get('companies', []))

@app.route('/generate/cover-letter')
def cover_letter_page():
    return render_template('cover_letter.html',
                         job_offers=example_data.get('job_offers', []),
                         profiles=example_data.get('profiles', []))

@app.route('/generate/email')
def email_generator_page():
    return render_template('email_generator.html',
                         profiles=example_data.get('profiles', []))

@app.route('/profile/analyze')
def profile_analyzer_page():
    return render_template('profile_analyzer.html')

# ===========================
# ROUTES ADMIN
# ===========================

@app.route('/admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/scraper')
def admin_scraper():
    return render_template('admin/scraper_dashboard.html')

@app.route('/admin/knowledge-base')
def admin_knowledge_base():
    return render_template('admin/knowledge_base.html')

# ===========================
# API GÉNÉRATION (inchangées)
# ===========================

@app.route('/api/generate/message', methods=['POST'])
def generate_linkedin_message():
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
# API SCRAPING AVEC ANNULATION
# ===========================

@app.route('/api/scraping/start', methods=['POST'])
def start_scraping():
    """Lance le scraping avec support d'annulation"""
    try:
        try:
            from models.scraper import ScrapingOrchestrator
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Modules de scraping non installés. Consultez le guide d\'installation.'
            }), 500
        
        data = request.get_json() or {}
        sources = data.get('sources', ['wttj'])
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        # Créer l'orchestrateur et la session
        orchestrator = ScrapingOrchestrator()
        orchestrator.start_scraping_session(session_id)
        
        # Créer le tracker de progression si WebSocket disponible
        progress_tracker = None
        if WEBSOCKET_AVAILABLE and socketio:
            progress_tracker = ScrapingProgressTracker(socketio, session_id)
        
        # Stocker la session pour permettre l'annulation
        scraping_sessions[session_id] = {
            'orchestrator': orchestrator,
            'progress_tracker': progress_tracker,
            'start_time': datetime.now(),
            'sources': sources
        }
        
        # Lancement asynchrone
        import asyncio
        import threading
        
        def run_scraping_thread():
            """Thread pour exécuter le scraping asynchrone"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                stats = loop.run_until_complete(
                    orchestrator.run_full_scrape(
                        sources=sources,
                        session_id=session_id,
                        progress_tracker=progress_tracker
                    )
                )
                
                # Nettoyer la session
                if session_id in scraping_sessions:
                    del scraping_sessions[session_id]
                
                # Notifier la fin via WebSocket
                if WEBSOCKET_AVAILABLE and socketio and progress_tracker:
                    socketio.emit('scraping_completed', {
                        'session_id': session_id,
                        'stats': stats
                    }, room=session_id, namespace='/scraping')
                
            except Exception as e:
                # Notifier l'erreur via WebSocket
                if WEBSOCKET_AVAILABLE and socketio:
                    socketio.emit('scraping_error', {
                        'session_id': session_id,
                        'error': str(e)
                    }, room=session_id, namespace='/scraping')
                
                # Nettoyer la session en cas d'erreur
                if session_id in scraping_sessions:
                    del scraping_sessions[session_id]
        
        # Démarrer le thread de scraping
        thread = threading.Thread(target=run_scraping_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f"Scraping démarré pour les sources : {', '.join(sources)}",
            'websocket_enabled': WEBSOCKET_AVAILABLE
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/cancel/<session_id>', methods=['POST'])
def cancel_scraping(session_id):
    """Annule une session de scraping"""
    try:
        if session_id in scraping_sessions:
            session_data = scraping_sessions[session_id]
            orchestrator = session_data['orchestrator']
            
            # Annuler la session
            success = orchestrator.cancel_scraping_session(session_id)
            
            if success:
                # Notifier l'annulation via WebSocket
                if WEBSOCKET_AVAILABLE and socketio:
                    socketio.emit('scraping_cancelled', {
                        'session_id': session_id,
                        'message': 'Scraping annulé par l\'utilisateur'
                    }, room=session_id, namespace='/scraping')
                
                return jsonify({
                    'success': True,
                    'message': 'Annulation demandée'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Impossible d\'annuler la session'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'Session de scraping non trouvée'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/status/<session_id>')
def get_scraping_status(session_id):
    """Récupère le statut d'une session de scraping"""
    try:
        if session_id in scraping_sessions:
            session_data = scraping_sessions[session_id]
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'active': True,
                'start_time': session_data['start_time'].isoformat(),
                'sources': session_data['sources'],
                'duration': (datetime.now() - session_data['start_time']).total_seconds()
            })
        else:
            return jsonify({
                'success': True,
                'session_id': session_id,
                'active': False,
                'message': 'Session terminée ou inexistante'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/sessions')
def list_scraping_sessions():
    """Liste toutes les sessions de scraping actives"""
    try:
        sessions = []
        for session_id, session_data in scraping_sessions.items():
            sessions.append({
                'session_id': session_id,
                'start_time': session_data['start_time'].isoformat(),
                'sources': session_data['sources'],
                'duration': (datetime.now() - session_data['start_time']).total_seconds()
            })
        
        return jsonify({
            'success': True,
            'active_sessions': len(sessions),
            'sessions': sessions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===========================
# API ADMIN (inchangées mais mises à jour)
# ===========================

@app.route('/api/admin/scraping/status')
def get_scraping_status_admin():
    """Statut détaillé du système de scraping"""
    try:
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
            'rag_enabled': getattr(ai_generator, 'rag_enabled', False),
            'websocket_enabled': WEBSOCKET_AVAILABLE,
            'active_scraping_sessions': len(scraping_sessions)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Autres routes API inchangées...
@app.route('/api/knowledge/search', methods=['POST'])
def search_knowledge():
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

@app.route('/api/status')
def api_status():
    try:
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
            'websocket_enabled': WEBSOCKET_AVAILABLE,
            'active_scraping_sessions': len(scraping_sessions),
            'features': {
                'message_generation': True,
                'cover_letter_generation': True,
                'email_generation': True,
                'profile_analysis': True,
                'enhanced_with_rag': getattr(ai_generator, 'rag_enabled', False),
                'scraping': kb_available,
                'market_insights': kb_available,
                'real_time_logs': WEBSOCKET_AVAILABLE,
                'cancellable_scraping': True,
                'total_jobs': kb_stats.get('total_jobs', 0) if kb_available else 0
            }
        }
        
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
# WEBSOCKET EVENTS
# ===========================

if WEBSOCKET_AVAILABLE:
    @socketio.on('connect', namespace='/scraping')
    def handle_connect():
        print(f"Client connecté pour scraping: {request.sid}")
    
    @socketio.on('disconnect', namespace='/scraping')  
    def handle_disconnect():
        print(f"Client déconnecté: {request.sid}")
    
    @socketio.on('start_scraping_session', namespace='/scraping')
    def handle_start_session(data):
        session_id = request.sid
        join_room(session_id)
        emit('session_started', {'session_id': session_id})
    
    @socketio.on('join_session', namespace='/scraping')
    def handle_join_session(data):
        session_id = data.get('session_id')
        if session_id:
            join_room(session_id)
            emit('joined_session', {'session_id': session_id})

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
    return {
        'admin_nav': [
            {'url': '/admin', 'title': 'Dashboard Admin', 'icon': 'fas fa-tachometer-alt'},
            {'url': '/admin/scraper', 'title': 'Scraping', 'icon': 'fas fa-robot'},
            {'url': '/admin/knowledge-base', 'title': 'Base de connaissances', 'icon': 'fas fa-brain'},
        ],
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'websocket_enabled': WEBSOCKET_AVAILABLE
    }

# ===========================
# LANCEMENT DE L'APPLICATION
# ===========================

if __name__ == '__main__':
    import os
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 LinkedBoost - Démarrage de l'application")
    print(f"📡 Ollama disponible: {ai_generator.is_available()}")
    print(f"🤖 Modèle: {ai_generator.model}")
    print(f"🧠 RAG activé: {getattr(ai_generator, 'rag_enabled', False)}")
    print(f"🔌 WebSocket activé: {WEBSOCKET_AVAILABLE}")
    
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
    print("📡 Logs temps réel: WebSocket activé" if WEBSOCKET_AVAILABLE else "📡 Logs temps réel: Indisponible")
    print("=" * 50)
    
    if WEBSOCKET_AVAILABLE and socketio:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)