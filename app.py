# app.py - LinkedBoost Assistant IA pour LinkedIn - Version complète

from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
import json
import os
import asyncio
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports des modules locaux
from models.ai_generator import LinkedBoostAI
from config import Config

# Initialisation de l'application Flask
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialisation du générateur IA
ai_generator = LinkedBoostAI()

# Instance globale de l'orchestrateur de scraping
scraping_orchestrator = None

def get_scraping_orchestrator():
    """Récupère ou crée l'instance de l'orchestrateur de scraping"""
    global scraping_orchestrator
    if scraping_orchestrator is None:
        try:
            from models.scraper import ScrapingOrchestrator
            scraping_orchestrator = ScrapingOrchestrator()
            logger.info("🔧 Orchestrateur de scraping initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation scraping: {e}")
            scraping_orchestrator = None
    return scraping_orchestrator

# Chargement des données d'exemple
def load_example_data():
    """Charge les données d'exemple depuis le fichier JSON"""
    try:
        with open('data/examples.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("⚠️ Fichier examples.json non trouvé, utilisation de données par défaut")
        return {
            "profiles": [
                {
                    "name": "Jean Dupont",
                    "position": "Développeur Full Stack",
                    "company": "TechCorp",
                    "skills": ["JavaScript", "React", "Node.js", "Python"]
                }
            ],
            "job_offers": [
                {
                    "title": "Développeur Python Senior",
                    "company": "DataFlow",
                    "location": "Paris",
                    "description": "Nous recherchons un développeur Python expérimenté..."
                }
            ],
            "companies": [
                {
                    "name": "TechCorp",
                    "industry": "Technologie",
                    "size": "500-1000 employés"
                }
            ]
        }

example_data = load_example_data()

# ==========================================
# ROUTES PRINCIPALES
# ==========================================

@app.route('/')
def dashboard():
    """Dashboard principal de LinkedBoost"""
    try:
        stats = {
            'messages_generated': 150,
            'cover_letters_generated': 45,
            'emails_generated': 78,
            'success_rate': 85
        }
        
        # Ajouter les stats de scraping si disponible
        orchestrator = get_scraping_orchestrator()
        if orchestrator:
            scraping_stats = orchestrator.get_stats()
            stats['jobs_scraped'] = scraping_stats.get('total_jobs', 0)
        
        return render_template('index.html', 
                             stats=stats, 
                             ollama_status=ai_generator.is_available())
    except Exception as e:
        logger.error(f"Erreur dashboard principal: {e}")
        return render_template('500.html'), 500

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

# ==========================================
# ROUTES ADMINISTRATION
# ==========================================

@app.route('/admin')
def admin_dashboard():
    """Dashboard d'administration"""
    return render_template('admin/dashboard.html')

@app.route('/admin/scraper')
def scraper_dashboard():
    """Dashboard de scraping"""
    return render_template('admin/scraper_dashboard.html')

@app.route('/admin/knowledge')
def knowledge_base_page():
    """Page de la base de connaissances"""
    return render_template('admin/knowledge_base.html')

# ==========================================
# API GÉNÉRATION DE CONTENU
# ==========================================

@app.route('/api/generate/message', methods=['POST'])
def generate_linkedin_message():
    """API pour générer des messages LinkedIn personnalisés"""
    try:
        data = request.get_json()
        
        required_fields = ['message_type', 'recipient_name', 'context']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Champs requis manquants'}), 400
        
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
    try:
        data = request.get_json()
        
        required_fields = ['job_title', 'company_name', 'applicant_name']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Champs requis manquants'}), 400
        
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
    try:
        data = request.get_json()
        
        required_fields = ['email_type', 'recipient_name', 'subject_context']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Champs requis manquants'}), 400
        
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
    try:
        data = request.get_json()
        
        if 'profile_text' not in data:
            return jsonify({'error': 'Texte du profil requis'}), 400
        
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

# ==========================================
# API SCRAPING
# ==========================================

@app.route('/api/scraping/start', methods=['POST'])
def start_scraping():
    """Lance le scraping des offres d'emploi"""
    try:
        data = request.get_json() or {}
        sources = data.get('sources', ['wttj'])
        max_jobs = data.get('max_jobs', 50)
        
        orchestrator = get_scraping_orchestrator()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'Orchestrateur de scraping non disponible'
            }), 500
        
        # Ajouter un log de démarrage
        orchestrator.add_log(f"🚀 Démarrage scraping: sources={sources}, max_jobs={max_jobs}")
        
        # Lancement asynchrone
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            stats = loop.run_until_complete(orchestrator.run_full_scrape(sources))
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f"Scraping terminé : {stats.get('total_jobs', 0)} offres collectées"
        })
        
    except Exception as e:
        logger.error(f"Erreur scraping: {e}")
        # Ajouter l'erreur aux logs si possible
        try:
            orchestrator = get_scraping_orchestrator()
            if orchestrator:
                orchestrator.add_log(f"❌ Erreur scraping : {str(e)}", 'error')
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/logs', methods=['GET'])
def get_scraping_logs():
    """Récupère les logs de scraping pour le frontend"""
    try:
        orchestrator = get_scraping_orchestrator()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'Orchestrateur non disponible'
            }), 500
        
        logs = orchestrator.get_logs()
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/logs', methods=['DELETE'])
def clear_scraping_logs():
    """Efface les logs de scraping"""
    try:
        orchestrator = get_scraping_orchestrator()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'Orchestrateur non disponible'
            }), 500
        
        orchestrator.clear_logs()
        
        return jsonify({
            'success': True,
            'message': 'Logs effacés'
        })
        
    except Exception as e:
        logger.error(f"Erreur effacement logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/status', methods=['GET'])
def get_scraping_status():
    """Statut en temps réel du scraping"""
    try:
        orchestrator = get_scraping_orchestrator()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'Orchestrateur non disponible'
            }), 500
        
        stats = orchestrator.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erreur statut scraping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/config', methods=['POST'])
def save_scraping_config():
    """Sauvegarde la configuration de scraping"""
    try:
        config = request.get_json()
        
        # Créer le dossier de données si nécessaire
        os.makedirs('./data', exist_ok=True)
        
        # Sauvegarder la configuration
        with open('./data/scraping_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': 'Configuration sauvegardée'
        })
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scraping/config', methods=['GET'])
def get_scraping_config():
    """Récupère la configuration de scraping"""
    try:
        try:
            with open('./data/scraping_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            # Configuration par défaut
            config = {
                'sources': {
                    'wttj': True,
                    'linkedin': False,
                    'indeed': False
                },
                'maxJobs': 50,
                'delay': 2.0
            }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==========================================
# API ADMIN
# ==========================================

@app.route('/api/admin/scraping/status')
def admin_scraping_status():
    """Statut du scraping pour l'admin"""
    try:
        orchestrator = get_scraping_orchestrator()
        if not orchestrator:
            return jsonify({
                'success': False,
                'error': 'Orchestrateur non disponible'
            }), 500
        
        stats = orchestrator.get_stats()
        
        return jsonify({
            'success': True,
            'status': 'active' if stats.get('ai_features_enabled') else 'basic',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erreur statut admin scraping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/system/health')
def admin_system_health():
    """Santé du système"""
    try:
        # Vérifications du système
        checks = {
            'ollama': ai_generator.is_available(),
            'database': True,  # SQLite toujours disponible
            'scraping': get_scraping_orchestrator() is not None,
            'embeddings': False,
            'knowledge_base': False
        }
        
        # Test de la base de connaissances
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            kb_stats = kb.get_stats()
            checks['knowledge_base'] = True
            checks['embeddings'] = kb_stats.get('embeddings_enabled', False)
        except Exception as e:
            logger.debug(f"KB non disponible: {e}")
            checks['knowledge_base'] = False
        
        # Déterminer le statut global
        critical_services = ['ollama', 'database']
        all_critical_healthy = all(checks[service] for service in critical_services)
        
        status = 'healthy' if all_critical_healthy else 'degraded'
        
        health_info = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
            'uptime': 'Runtime',
            'version': '1.0.0'
        }
        
        status_code = 200 if status == 'healthy' else 503
        return jsonify(health_info), status_code
        
    except Exception as e:
        logger.error(f"Erreur santé système: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ==========================================
# API BASE DE CONNAISSANCES
# ==========================================

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
        logger.error(f"Erreur recherche KB: {e}")
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
        logger.error(f"Erreur analytics marché: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==========================================
# API GÉNÉRATION ENRICHIE (RAG)
# ==========================================

@app.route('/api/generate/enhanced', methods=['POST'])
def generate_enhanced_content():
    """Génération de contenu enrichie avec RAG"""
    try:
        data = request.get_json()
        content_type = data.get('type')  # 'message', 'cover_letter', 'email'
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
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
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logger.error(f"Erreur génération enrichie: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==========================================
# API STATUS GLOBALE
# ==========================================

@app.route('/api/status')
def api_status():
    """Statut global de l'API et des services"""
    try:
        # Statut de base
        status = {
            'ollama_available': ai_generator.is_available(),
            'model': ai_generator.model,
            'features': {
                'message_generation': True,
                'cover_letter_generation': True,
                'email_generation': True,
                'profile_analysis': True,
                'scraping': True,
                'knowledge_base': True
            }
        }
        
        # Ajouter les stats de scraping si disponible
        try:
            orchestrator = get_scraping_orchestrator()
            if orchestrator:
                scraping_stats = orchestrator.get_stats()
                status['scraping'] = {
                    'available': True,
                    'stats': scraping_stats,
                    'ai_features_enabled': scraping_stats.get('ai_features_enabled', False)
                }
            else:
                status['scraping'] = {
                    'available': False,
                    'error': 'Orchestrateur non initialisé'
                }
        except Exception as e:
            status['scraping'] = {
                'available': False,
                'error': str(e)
            }
        
        # Ajouter les stats de la base de connaissances si disponible
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            kb_stats = kb.get_stats()
            status['knowledge_base'] = {
                'available': True,
                'stats': kb_stats
            }
        except Exception as e:
            status['knowledge_base'] = {
                'available': False,
                'error': str(e)
            }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erreur statut API: {e}")
        return jsonify({
            'error': str(e),
            'ollama_available': False
        }), 500

# ==========================================
# ROUTES SOCKET.IO PLACEHOLDER
# ==========================================

@app.route('/socket.io/')
@app.route('/socket.io/<path:subpath>')
def socket_io_handler(subpath=''):
    """Gestionnaire pour toutes les requêtes Socket.IO"""
    # Log des tentatives de connexion pour debug
    logger.debug(f"Socket.IO request: {request.path} - {request.args}")
    
    # Réponse JSON indiquant que Socket.IO n'est pas configuré
    response = {
        'error': 'Socket.IO not configured',
        'message': 'This version uses REST API for real-time updates',
        'alternatives': {
            'logs': '/api/scraping/logs',
            'status': '/api/scraping/status',
            'health': '/api/admin/system/health'
        },
        'polling_recommended': True,
        'path_requested': request.path
    }
    
    # Retourner 404 pour que le client comprenne que Socket.IO n'est pas disponible
    return jsonify(response), 404

# Gérer spécifiquement les requêtes POST Socket.IO
@app.route('/socket.io/', methods=['POST'])
@app.route('/socket.io/<path:subpath>', methods=['POST'])
def socket_io_post_handler(subpath=''):
    """Gestionnaire POST pour Socket.IO"""
    return jsonify({
        'error': 'Socket.IO POST not supported',
        'message': 'Use REST API endpoints instead'
    }), 404

# ==========================================
# ROUTES DE TEST
# ==========================================

@app.route('/api/test/admin')
def test_admin_routes():
    """Route de test pour vérifier que les routes admin fonctionnent"""
    try:
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # Test 1: Santé système
        try:
            health_check = {
                'ollama': ai_generator.is_available(),
                'database': True
            }
            test_results['tests']['health'] = {'status': 'ok', 'checks': health_check}
        except Exception as e:
            test_results['tests']['health'] = {'status': 'error', 'error': str(e)}
        
        # Test 2: Scraping status
        try:
            orchestrator = get_scraping_orchestrator()
            if orchestrator:
                scraping_stats = orchestrator.get_stats()
                test_results['tests']['scraping'] = {'status': 'ok', 'available': True}
            else:
                test_results['tests']['scraping'] = {'status': 'warning', 'message': 'Orchestrateur non initialisé'}
        except Exception as e:
            test_results['tests']['scraping'] = {'status': 'error', 'error': str(e)}
        
        # Test 3: Base de connaissances
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            kb_stats = kb.get_stats()
            test_results['tests']['knowledge_base'] = {'status': 'ok', 'stats': kb_stats}
        except Exception as e:
            test_results['tests']['knowledge_base'] = {'status': 'error', 'error': str(e)}
        
        return jsonify({
            'success': True,
            'message': 'Tests des routes admin terminés',
            'results': test_results
        })
        
    except Exception as e:
        logger.error(f"Erreur tests admin: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==========================================
# GESTION D'ERREURS
# ==========================================

@app.errorhandler(404)
def not_found(error):
    """Page 404 personnalisée"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Page 500 personnalisée"""
    logger.error(f"Erreur interne: {error}")
    return render_template('500.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Gestionnaire d'exceptions global"""
    logger.error(f"Exception non gérée: {e}")
    return jsonify({
        'error': 'Erreur interne du serveur',
        'message': 'Une erreur inattendue s\'est produite'
    }), 500

# ==========================================
# DÉMARRAGE DE L'APPLICATION
# ==========================================

def print_startup_info():
    """Affiche les informations de démarrage"""
    print("=" * 60)
    print("🚀 LinkedBoost - Assistant IA pour LinkedIn")
    print("=" * 60)
    print(f"📡 Ollama disponible: {ai_generator.is_available()}")
    print(f"🤖 Modèle: {ai_generator.model}")
    
    # Vérification des fonctionnalités avancées
    try:
        orchestrator = get_scraping_orchestrator()
        if orchestrator:
            print(f"🧠 Fonctionnalités avancées: {orchestrator.ai_features_enabled}")
            print(f"📊 RAG activé: {orchestrator.ai_features_enabled}")
            print(f"🕷️ Scraping activé: True")
        else:
            print("🧠 Fonctionnalités avancées: False")
            print("📊 RAG activé: False") 
            print("🕷️ Scraping activé: False")
        print(f"⏰ Planificateur: False")  # À implémenter plus tard
    except Exception as e:
        print(f"⚠️ Fonctionnalités avancées: Erreur - {e}")
    
    print("=" * 60)
    print("🌐 Application démarrée sur http://localhost:5000")
    print("📚 Documentation API: http://localhost:5000/api/status")
    print("🔧 Administration: http://localhost:5000/admin")
    print("🕷️ Scraping: http://localhost:5000/admin/scraper")
    print("🧠 Base de connaissances: http://localhost:5000/admin/knowledge")
    print("=" * 60)
    
    if not ai_generator.is_available():
        print("⚠️  Ollama n'est pas disponible. Démarrez-le avec: ollama serve")
        print("💡 Ou téléchargez-le depuis: https://ollama.ai")

if __name__ == '__main__':
    # Affichage des informations de démarrage
    print_startup_info()
    
    # Créer les dossiers nécessaires
    os.makedirs('./data', exist_ok=True)
    os.makedirs('./data/reports', exist_ok=True)
    os.makedirs('./data/scraped', exist_ok=True)
    
    # Lancement de l'application
    app.run(debug=True, host='0.0.0.0', port=5000)