# utils/text_processor.py - Utilitaires de traitement de texte
import re
from typing import List, Dict, Set, Any
from collections import Counter

class TextProcessor:
    """Processeur de texte pour l'analyse des offres d'emploi"""
    
    def __init__(self):
        self.tech_keywords = self.load_tech_keywords()
        self.soft_skills = self.load_soft_skills()
        
    def load_tech_keywords(self) -> Set[str]:
        """Charge les mots-clés techniques"""
        return {
            # Langages
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
            'typescript', 'swift', 'kotlin', 'scala', 'r', 'matlab',
            
            # Frameworks/Libraries
            'react', 'vue', 'angular', 'django', 'flask', 'spring', 'laravel',
            'node.js', 'express', 'fastapi', 'tensorflow', 'pytorch', 'keras',
            
            # Bases de données
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
            'oracle', 'cassandra', 'neo4j',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab',
            'terraform', 'ansible', 'chef', 'puppet',
            
            # Outils
            'git', 'jira', 'confluence', 'slack', 'figma', 'adobe', 'photoshop'
        }
    
    def load_soft_skills(self) -> Set[str]:
        """Charge les soft skills"""
        return {
            'leadership', 'communication', 'teamwork', 'problem solving',
            'creativity', 'adaptability', 'organization', 'autonomie',
            'rigueur', 'curiosité', 'collaboration', 'innovation'
        }
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extrait les compétences techniques et soft skills"""
        text_lower = text.lower()
        
        found_tech = []
        found_soft = []
        
        # Recherche des compétences techniques
        for tech in self.tech_keywords:
            if tech in text_lower:
                found_tech.append(tech)
        
        # Recherche des soft skills
        for skill in self.soft_skills:
            if skill in text_lower:
                found_soft.append(skill)
        
        return {
            'technical': found_tech,
            'soft': found_soft
        }
    
    def extract_salary_info(self, text: str) -> Dict[str, Any]:
        """Extraction avancée des informations de salaire"""
        salary_patterns = [
            r'(\d+)\s*k€?\s*[-–]\s*(\d+)\s*k€?',  # 45k - 55k
            r'(\d+)\s*000\s*[-–]\s*(\d+)\s*000\s*€',  # 45000 - 55000€
            r'salaire\s*:?\s*(\d+)\s*k€?',  # Salaire: 50k
            r'rémunération\s*:?\s*(\d+)\s*k€?',
            r'package\s*:?\s*(\d+)\s*k€?',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    return {
                        'min': int(groups[0]) * 1000,
                        'max': int(groups[1]) * 1000,
                        'currency': 'EUR',
                        'period': 'annual'
                    }
                else:
                    return {
                        'amount': int(groups[0]) * 1000,
                        'currency': 'EUR',
                        'period': 'annual'
                    }
        
        return {}
    
    def classify_experience_level(self, text: str) -> str:
        """Classification avancée du niveau d'expérience"""
        text_lower = text.lower()
        
        # Patterns pour les différents niveaux
        junior_patterns = [
            r'junior', r'débutant', r'0[-\s]?[12]?\s*an', r'stage', r'alternance',
            r'first job', r'graduate', r'entry level'
        ]
        
        senior_patterns = [
            r'senior', r'lead', r'principal', r'architect', r'[5-9]\+?\s*an',
            r'expert', r'[1-9][0-9]\+?\s*an'
        ]
        
        mid_patterns = [
            r'[23456]\s*[-\s]\s*[456789]\s*an', r'confirmé', r'experienced'
        ]
        
        # Scoring par catégorie
        junior_score = sum(1 for pattern in junior_patterns if re.search(pattern, text_lower))
        senior_score = sum(1 for pattern in senior_patterns if re.search(pattern, text_lower))
        mid_score = sum(1 for pattern in mid_patterns if re.search(pattern, text_lower))
        
        if senior_score > junior_score and senior_score > mid_score:
            return 'senior'
        elif junior_score > mid_score:
            return 'junior'
        else:
            return 'mid'
    
    def detect_remote_keywords(self, text: str) -> Dict[str, Any]:
        """Détection avancée des modalités de travail"""
        text_lower = text.lower()
        
        remote_keywords = {
            'full_remote': ['100% remote', 'full remote', 'télétravail complet', 'entièrement à distance'],
            'hybrid': ['hybride', 'télétravail partiel', '2-3 jours', 'flexible'],
            'office': ['présentiel', 'sur site', 'bureau obligatoire']
        }
        
        result = {
            'remote_type': 'unknown',
            'confidence': 0.0,
            'keywords_found': []
        }
        
        for work_type, keywords in remote_keywords.items():
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                result['remote_type'] = work_type
                result['keywords_found'] = found_keywords
                result['confidence'] = len(found_keywords) / len(keywords)
                break
        
        return result
    
    def extract_company_benefits(self, text: str) -> List[str]:
        """Extrait les avantages entreprise mentionnés"""
        benefits_keywords = {
            'mutuelle', 'assurance santé', 'tickets restaurant', 'carte ticket restaurant',
            'participation', 'intéressement', 'plan épargne', 'stock options',
            'formation', 'certification', 'conférences', 'budget formation',
            'flex office', 'coworking', 'horaires flexibles', 'aménagement du temps',
            'congés', 'rtt', 'vacances', 'sabbatique',
            'vélo', 'transport', 'remboursement transport', 'parking',
            'crèche', 'garde enfants', 'family friendly'
        }
        
        found_benefits = []
        text_lower = text.lower()
        
        for benefit in benefits_keywords:
            if benefit in text_lower:
                found_benefits.append(benefit)
        
        return found_benefits
    
    def extract_technologies_advanced(self, text: str) -> Dict[str, List[str]]:
        """Extraction avancée des technologies par catégorie"""
        text_lower = text.lower()
        
        tech_categories = {
            'languages': ['python', 'javascript', 'java', 'typescript', 'go', 'rust', 'php', 'ruby'],
            'frontend': ['react', 'vue', 'angular', 'html', 'css', 'sass', 'bootstrap'],
            'backend': ['django', 'flask', 'spring', 'node.js', 'express', 'fastapi'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch'],
            'cloud': ['aws', 'azure', 'gcp', 'heroku', 'vercel', 'netlify'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'gitlab', 'terraform', 'ansible'],
            'data': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'spark'],
            'mobile': ['react native', 'flutter', 'swift', 'kotlin', 'xamarin']
        }
        
        found_tech = {}
        
        for category, technologies in tech_categories.items():
            found_in_category = []
            for tech in technologies:
                if tech in text_lower:
                    found_in_category.append(tech)
            
            if found_in_category:
                found_tech[category] = found_in_category
        
        return found_tech
    
    def calculate_job_score(self, job_text: str, user_skills: List[str]) -> Dict[str, Any]:
        """Calcule un score de compatibilité entre une offre et des compétences utilisateur"""
        job_skills = self.extract_skills(job_text)
        job_techs = job_skills['technical']
        
        user_skills_lower = [skill.lower() for skill in user_skills]
        job_techs_lower = [tech.lower() for tech in job_techs]
        
        # Intersection des compétences
        matching_skills = set(user_skills_lower).intersection(set(job_techs_lower))
        
        if not job_techs_lower:
            return {'score': 0, 'matching_skills': [], 'missing_skills': []}
        
        # Score basé sur le pourcentage de match
        score = len(matching_skills) / len(job_techs_lower) * 100
        
        # Compétences manquantes
        missing_skills = set(job_techs_lower) - set(user_skills_lower)
        
        return {
            'score': round(score, 1),
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills),
            'total_job_skills': len(job_techs_lower),
            'total_user_skills': len(user_skills_lower)
        }
    
    def normalize_company_name(self, company_name: str) -> str:
        """Normalise le nom d'entreprise pour éviter les doublons"""
        if not company_name:
            return ""
        
        # Suppressions courantes
        normalized = company_name.lower()
        
        # Suppression des suffixes légaux
        legal_suffixes = [
            'sas', 'sarl', 'sa', 'sasu', 'eurl', 'snc', 'sci',
            'ltd', 'llc', 'inc', 'corp', 'gmbh', 'ag'
        ]
        
        for suffix in legal_suffixes:
            normalized = re.sub(rf'\b{suffix}\b', '', normalized)
        
        # Suppression des mots inutiles
        stop_words = ['société', 'company', 'entreprise', 'group', 'groupe']
        for word in stop_words:
            normalized = re.sub(rf'\b{word}\b', '', normalized)
        
        # Nettoyage final
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Suppression ponctuation
        normalized = re.sub(r'\s+', ' ', normalized)     # Espaces multiples
        normalized = normalized.strip()
        
        return normalized.title()  # Première lettre en majuscule

# utils/scheduler.py - Planificateur de tâches
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import asyncio
from models.scraper import ScrapingOrchestrator
from config import Config

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Planificateur de tâches pour LinkedBoost"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scraping_orchestrator = ScrapingOrchestrator()
        self.is_running = False
    
    def start(self):
        """Démarre le planificateur"""
        if not self.is_running and Config.SCRAPING_ENABLED:
            # Scraping automatique toutes les X heures
            self.scheduler.add_job(
                func=self.run_scheduled_scraping,
                trigger=CronTrigger(hours=Config.SCRAPING_INTERVAL_HOURS),
                id='scheduled_scraping',
                name='Scraping automatique des offres d\'emploi',
                replace_existing=True
            )
            
            # Nettoyage des anciennes données (une fois par semaine)
            self.scheduler.add_job(
                func=self.cleanup_old_data,
                trigger=CronTrigger(day_of_week=0, hour=2),  # Dimanche à 2h
                id='data_cleanup',
                name='Nettoyage des anciennes données',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("✅ Planificateur de tâches démarré")
    
    def stop(self):
        """Arrête le planificateur"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("⏹ Planificateur de tâches arrêté")
    
    def run_scheduled_scraping(self):
        """Lance le scraping programmé"""
        logger.info("🕐 Démarrage du scraping programmé")
        
        try:
            # Création d'une nouvelle boucle d'événements pour le thread du scheduler
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Exécution du scraping
            stats = loop.run_until_complete(
                self.scraping_orchestrator.run_full_scrape(['wttj'])
            )
            
            logger.info(f"✅ Scraping programmé terminé : {stats.get('total_jobs', 0)} offres")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du scraping programmé : {e}")
        finally:
            loop.close()
    
    def cleanup_old_data(self):
        """Nettoie les anciennes données"""
        logger.info("🧹 Démarrage du nettoyage des données")
        
        try:
            from models.knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            
            # Suppression des offres de plus de 30 jours
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # Cette fonctionnalité sera implémentée dans KnowledgeBase
            # kb.cleanup_old_jobs(cutoff_date)
            
            logger.info("✅ Nettoyage des données terminé")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage : {e}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Retourne le statut des tâches planifiées"""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'scheduler_running': self.is_running,
            'jobs': jobs,
            'total_jobs': len(jobs)
        }