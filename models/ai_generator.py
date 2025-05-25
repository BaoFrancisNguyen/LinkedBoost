# models/ai_generator.py - Version corrigée
import requests
import json
from typing import Dict, List, Optional
from config import Config
import logging

logger = logging.getLogger(__name__)

# Import conditionnel de la base de connaissances
try:
    from models.knowledge_base import KnowledgeBase
    RAG_AVAILABLE = True
    logger.info("✅ RAG activé - Base de connaissances disponible")
except ImportError as e:
    RAG_AVAILABLE = False
    logger.warning(f"⚠️ RAG désactivé - Dépendances manquantes: {e}")
    logger.info("💡 Pour activer le RAG: vérifiez les dépendances dans requirements.txt")

class LinkedBoostAI:
    """Générateur IA pour LinkedBoost avec support RAG optionnel"""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
        self.timeout = 60
        
        # Initialisation conditionnelle du RAG
        self.knowledge_base = None
        self.rag_enabled = False
        
        if RAG_AVAILABLE:
            try:
                self.knowledge_base = KnowledgeBase()
                self.rag_enabled = True
                logger.info("🧠 Base de connaissances initialisée avec succès")
            except Exception as e:
                self.rag_enabled = False
                logger.warning(f"⚠️ Erreur initialisation RAG: {e}")
                logger.info("💡 Fonctionnement en mode de base (sans enrichissement marché)")
        else:
            logger.info("📝 Fonctionnement en mode de base (sans RAG)")
    
    def is_available(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def _generate_content(self, prompt: str, temperature: float = 0.7) -> str:
        """Génération de contenu avec Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 500,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                raise Exception(f"Erreur Ollama: {response.status_code}")
                
        except requests.RequestException as e:
            raise Exception(f"Erreur de connexion à Ollama: {str(e)}")
    
    async def generate_linkedin_message_enhanced(self, message_type: str, recipient_name: str, 
                                               recipient_company: str = "", recipient_position: str = "",
                                               context: str = "", sender_name: str = "Utilisateur",
                                               **kwargs) -> Dict[str, str]:
        """Génération de message LinkedIn avec enrichissement RAG optionnel"""
        
        # Variables par défaut
        enhanced_context = context
        company_insights = {}
        enhancement_applied = False
        
        # Enrichissement avec RAG si disponible
        if self.rag_enabled and recipient_company:
            try:
                # Recherche d'insights sur l'entreprise
                company_insights = self.knowledge_base.get_company_insights(recipient_company)
                
                if company_insights.get('jobs_found', 0) > 0:
                    # Construction du contexte enrichi
                    insights_text = []
                    
                    if company_insights.get('top_technologies'):
                        top_techs = [t['tech'] for t in company_insights['top_technologies'][:3]]
                        insights_text.append(f"Technologies utilisées: {', '.join(top_techs)}")
                    
                    if company_insights.get('remote_percentage', 0) > 50:
                        insights_text.append(f"Entreprise flexible ({company_insights['remote_percentage']}% remote)")
                    
                    if company_insights.get('hiring_trend') == 'Active':
                        insights_text.append("Recrutement actif en cours")
                    
                    if insights_text:
                        enhanced_context = f"{context}\n\nInsights marché: {' | '.join(insights_text)}"
                        enhancement_applied = True
                        
            except Exception as e:
                logger.warning(f"Erreur enrichissement RAG: {e}")
        
        # Génération du message
        message = self.generate_linkedin_message(
            message_type, recipient_name, recipient_company, 
            recipient_position, enhanced_context, sender_name, **kwargs
        )
        
        return {
            'message': message,
            'rag_used': self.rag_enabled,
            'company_insights': company_insights,
            'enhancement_applied': enhancement_applied
        }
    
    def generate_linkedin_message(self, message_type: str, recipient_name: str, 
                                recipient_company: str = "", recipient_position: str = "",
                                context: str = "", sender_name: str = "Utilisateur",
                                common_connections: List[str] = None, 
                                personalization_notes: str = "") -> str:
        """Génère des messages LinkedIn personnalisés"""
        
        if common_connections is None:
            common_connections = []
        
        # Prompts spécialisés selon le type de message
        prompts = {
            "connection": """Tu es un expert en networking LinkedIn. Génère un message de demande de connexion professionnel et personnalisé.

CONTEXTE:
- Destinataire: {recipient_name} {position_info} {company_info}
- Expéditeur: {sender_name}
- Contexte: {context}
- Connexions communes: {connections}
- Notes personnalisées: {notes}

CONSIGNES:
- Maximum 300 caractères (limite LinkedIn)
- Ton professionnel mais chaleureux
- Mentionner un élément personnel/commun
- Appel à l'action clair
- Éviter les formules toutes faites

GÉNÈRE LE MESSAGE:""",

            "follow_up": """Tu es un expert en communication LinkedIn. Génère un message de suivi après une connexion acceptée.

CONTEXTE:
- Destinataire: {recipient_name} {position_info} {company_info}
- Expéditeur: {sender_name}
- Contexte de la connexion: {context}
- Notes: {notes}

CONSIGNES:
- Remercier pour l'acceptation
- Proposer une valeur/collaboration
- Ton authentique et professionnel
- Suggestion concrète de suite
- Maximum 500 caractères

GÉNÈRE LE MESSAGE:""",

            "opportunity": """Tu es un expert en prospection LinkedIn. Génère un message pour présenter une opportunité professionnelle.

CONTEXTE:
- Destinataire: {recipient_name} {position_info} {company_info}
- Expéditeur: {sender_name}
- Opportunité: {context}
- Personnalisation: {notes}

CONSIGNES:
- Présenter l'opportunité clairement
- Expliquer pourquoi cette personne
- Ton professionnel et engageant
- Appel à l'action précis
- Maximum 800 caractères

GÉNÈRE LE MESSAGE:"""
        }
        
        # Construction des informations contextuelles
        position_info = f"({recipient_position})" if recipient_position else ""
        company_info = f"chez {recipient_company}" if recipient_company else ""
        connections_str = ", ".join(common_connections) if common_connections else "Aucune"
        
        prompt = prompts.get(message_type, prompts["connection"]).format(
            recipient_name=recipient_name,
            position_info=position_info,
            company_info=company_info,
            sender_name=sender_name,
            context=context,
            connections=connections_str,
            notes=personalization_notes
        )
        
        return self._generate_content(prompt, temperature=0.8)
    
    async def generate_cover_letter_enhanced(self, job_title: str, company_name: str,
                                           job_description: str = "", applicant_name: str = "",
                                           **kwargs) -> Dict[str, str]:
        """Génération de lettre de motivation enrichie avec insights marché"""
        
        # Variables par défaut
        market_context = ""
        company_insights = {}
        market_insights = {}
        
        # Enrichissement avec insights marché si RAG disponible
        if self.rag_enabled:
            try:
                # Insights sur l'entreprise
                company_insights = self.knowledge_base.get_company_insights(company_name)
                
                # Insights généraux sur le marché
                import asyncio
                market_insights = await self.knowledge_base.get_market_insights()
                
                # Construction du contexte marché
                context_parts = []
                
                if company_insights.get('jobs_found', 0) > 0:
                    if company_insights.get('top_technologies'):
                        top_techs = [t['tech'] for t in company_insights['top_technologies'][:3]]
                        context_parts.append(f"Technologies prioritaires chez {company_name}: {', '.join(top_techs)}")
                    
                    if company_insights.get('hiring_trend') == 'Active':
                        context_parts.append(f"{company_name} recrute activement")
                
                # Tendances générales du marché
                if market_insights.get('top_technologies'):
                    market_techs = [t['name'] for t in market_insights['top_technologies'][:3]]
                    context_parts.append(f"Technologies demandées sur le marché: {', '.join(market_techs)}")
                
                if market_insights.get('remote_percentage', 0) > 60:
                    context_parts.append(f"Marché orienté télétravail ({market_insights['remote_percentage']}%)")
                
                if context_parts:
                    market_context = f"\n\nCONTEXTE MARCHÉ:\n{' | '.join(context_parts)}"
                    
            except Exception as e:
                logger.warning(f"Erreur enrichissement lettre: {e}")
        
        # Génération avec contexte enrichi
        enhanced_description = f"{job_description}{market_context}"
        
        cover_letter = self.generate_cover_letter(
            job_title, company_name, enhanced_description, applicant_name, **kwargs
        )
        
        return {
            'cover_letter': cover_letter,
            'market_data_used': {
                'company_insights': company_insights,
                'market_insights': market_insights,
                'market_context_added': bool(market_context),
                'rag_enabled': self.rag_enabled
            }
        }
    
    def generate_cover_letter(self, job_title: str, company_name: str,
                            job_description: str = "", applicant_name: str = "",
                            applicant_experience: str = "", applicant_skills: List[str] = None,
                            tone: str = "professional") -> str:
        """Génère des lettres de motivation personnalisées"""
        
        if applicant_skills is None:
            applicant_skills = []
        
        tone_prompts = {
            "professional": "Ton professionnel et formel",
            "enthusiastic": "Ton enthousiaste et dynamique", 
            "creative": "Ton créatif et original",
            "confident": "Ton confiant et assertif"
        }
        
        skills_str = ", ".join(applicant_skills) if applicant_skills else "Non spécifiées"
        
        prompt = f"""Tu es un expert en rédaction de lettres de motivation. Génère une lettre de motivation professionnelle et percutante.

INFORMATIONS:
- Poste visé: {job_title}
- Entreprise: {company_name}
- Description du poste: {job_description}
- Candidat: {applicant_name}
- Expérience: {applicant_experience}
- Compétences clés: {skills_str}
- Style souhaité: {tone_prompts.get(tone, "Ton professionnel et formel")}

STRUCTURE REQUISE:
1. En-tête avec coordonnées (laisser des espaces pour personnalisation)
2. Objet clair
3. Introduction accrocheuse
4. Paragraphe expérience/compétences alignées au poste
5. Paragraphe motivation/connaissance entreprise
6. Conclusion avec appel à l'action
7. Formule de politesse

CONSIGNES:
- Maximum 400 mots
- Personnalisation évidente pour l'entreprise
- Mise en valeur des compétences pertinentes
- Éviter les clichés
- Structure claire et lisible

GÉNÈRE LA LETTRE COMPLÈTE:"""
        
        return self._generate_content(prompt, temperature=0.7)
    
    def generate_networking_email(self, email_type: str, recipient_name: str,
                                recipient_company: str = "", subject_context: str = "",
                                sender_name: str = "Utilisateur", meeting_purpose: str = "",
                                background_info: str = "") -> Dict[str, str]:
        """Génère des emails de networking avec objet et corps"""
        
        email_prompts = {
            "introduction": """Tu es un expert en networking professionnel. Génère un email d'introduction pour établir un premier contact.

CONTEXTE:
- Destinataire: {recipient_name} {company_info}
- Expéditeur: {sender_name}
- Contexte: {subject_context}
- Informations supplémentaires: {background}

GÉNÈRE:
1. OBJET (max 50 caractères, accrocheur)
2. CORPS D'EMAIL (professionnel, concis, max 200 mots)

FORMAT:
OBJET: [votre objet]
CORPS: [votre email]""",

            "meeting_request": """Tu es un expert en communication professionnelle. Génère un email pour demander un rendez-vous professionnel.

CONTEXTE:
- Destinataire: {recipient_name} {company_info}
- Expéditeur: {sender_name}
- Sujet de rencontre: {meeting_purpose}
- Contexte: {subject_context}
- Informations: {background}

GÉNÈRE:
1. OBJET (clair et direct, max 60 caractères)
2. CORPS D'EMAIL (structure professionnelle, max 250 mots)

FORMAT:
OBJET: [votre objet]
CORPS: [votre email]""",

            "follow_up": """Tu es un expert en suivi professionnel. Génère un email de suivi après un événement ou une rencontre.

CONTEXTE:
- Destinataire: {recipient_name} {company_info}
- Expéditeur: {sender_name}
- Événement/Rencontre: {subject_context}
- Suite souhaitée: {meeting_purpose}
- Détails: {background}

GÉNÈRE:
1. OBJET (référence à l'événement, max 55 caractères)
2. CORPS D'EMAIL (rappel + proposition, max 200 mots)

FORMAT:
OBJET: [votre objet]
CORPS: [votre email]"""
        }
        
        company_info = f"chez {recipient_company}" if recipient_company else ""
        
        prompt = email_prompts.get(email_type, email_prompts["introduction"]).format(
            recipient_name=recipient_name,
            company_info=company_info,
            sender_name=sender_name,
            subject_context=subject_context,
            meeting_purpose=meeting_purpose,
            background=background_info
        )
        
        response = self._generate_content(prompt, temperature=0.7)
        
        # Parsing de la réponse pour séparer objet et corps
        lines = response.split('\n')
        subject = ""
        body = ""
        
        for i, line in enumerate(lines):
            if line.startswith("OBJET:"):
                subject = line.replace("OBJET:", "").strip()
            elif line.startswith("CORPS:"):
                body = '\n'.join(lines[i:]).replace("CORPS:", "").strip()
                break
        
        return {
            "subject": subject,
            "body": body,
            "full_response": response
        }
    
    def analyze_linkedin_profile(self, profile_text: str, target_role: str = "",
                               industry: str = "") -> Dict[str, any]:
        """Analyse un profil LinkedIn et fournit des recommandations"""
        
        prompt = f"""Tu es un expert en optimisation de profils LinkedIn. Analyse ce profil et fournis des recommandations détaillées.

PROFIL À ANALYSER:
{profile_text}

OBJECTIFS:
- Poste visé: {target_role if target_role else "Non spécifié"}
- Secteur: {industry if industry else "Non spécifié"}

ANALYSE DEMANDÉE (format JSON):
{{
    "score_global": "X/10",
    "points_forts": ["point1", "point2", "point3"],
    "points_amelioration": ["amélioration1", "amélioration2", "amélioration3"],
    "titre_suggere": "nouveau titre professionnel",
    "resume_optimise": "résumé amélioré (150 mots max)",
    "mots_cles_manquants": ["mot1", "mot2", "mot3"],
    "recommandations_urgentes": ["action1", "action2"]
}}

GÉNÈRE L'ANALYSE JSON:"""
        
        response = self._generate_content(prompt, temperature=0.6)
        
        try:
            # Tentative de parsing JSON
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            # Si le JSON est mal formé, retourner une analyse basique
            return {
                "score_global": "En cours d'analyse",
                "points_forts": ["Profil analysé"],
                "points_amelioration": ["Analyse en cours"],
                "titre_suggere": "À définir",
                "resume_optimise": response,
                "mots_cles_manquants": ["À identifier"],
                "recommandations_urgentes": ["Revoir le format d'analyse"],
                "raw_response": response
            }
    
    def get_system_status(self) -> Dict[str, any]:
        """Retourne le statut complet du système"""
        status = {
            'ollama_available': self.is_available(),
            'model': self.model,
            'rag_enabled': self.rag_enabled,
            'capabilities': {
                'basic_generation': True,
                'enhanced_generation': self.rag_enabled,
                'market_insights': self.rag_enabled,
                'company_context': self.rag_enabled,
                'profile_market_comparison': self.rag_enabled
            },
            'features': {
                'linkedin_messages': True,
                'cover_letters': True,
                'networking_emails': True,
                'profile_analysis': True,
                'enhanced_with_rag': self.rag_enabled
            }
        }
        
        if self.rag_enabled and self.knowledge_base:
            try:
                kb_stats = self.knowledge_base.get_stats()
                status['knowledge_base'] = kb_stats
            except Exception as e:
                status['knowledge_base_error'] = str(e)
        
        return status