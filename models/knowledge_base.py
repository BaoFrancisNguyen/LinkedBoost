# models/knowledge_base.py - Version sans Hugging Face
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)

# Import conditionnel selon la solution choisie
try:
    from models.embeddings_ollama import OllamaEmbeddingManager
    EMBEDDING_METHOD = "ollama"
    logger.info("✅ Utilisation d'Ollama pour les embeddings")
except ImportError:
    try:
        from models.simple_search import SimpleSearchEngine
        EMBEDDING_METHOD = "tfidf"
        logger.info("✅ Utilisation de TF-IDF pour la recherche")
    except ImportError:
        EMBEDDING_METHOD = "none"
        logger.warning("⚠️ Aucun moteur de recherche disponible")

class KnowledgeBase:
    """Base de connaissances sans dépendances Hugging Face"""
    
    def __init__(self):
        self.db_path = "data/knowledge_base.db"
        self.search_engine = None
        
        # Initialisation du moteur de recherche selon la méthode disponible
        if EMBEDDING_METHOD == "ollama":
            try:
                self.search_engine = OllamaEmbeddingManager()
                logger.info("🧠 Moteur de recherche Ollama initialisé")
            except Exception as e:
                logger.warning(f"Erreur init Ollama: {e}")
                EMBEDDING_METHOD == "tfidf"
        
        if EMBEDDING_METHOD == "tfidf":
            try:
                self.search_engine = SimpleSearchEngine()
                logger.info("🔍 Moteur de recherche TF-IDF initialisé")
            except Exception as e:
                logger.warning(f"Erreur init TF-IDF: {e}")
        
        self.create_tables()
    
    def create_tables(self):
        """Crée les tables de base de données principales"""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table principale des offres
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_offers_main (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    description TEXT,
                    requirements TEXT,  -- JSON
                    technologies TEXT,  -- JSON
                    salary_min INTEGER,
                    salary_max INTEGER,
                    salary_text TEXT,
                    experience_level TEXT,
                    remote BOOLEAN DEFAULT FALSE,
                    contract_type TEXT,
                    url TEXT,
                    source TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Table des insights marché
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_type TEXT,  -- salary_trend, skill_demand, etc.
                    category TEXT,      -- Secteur/fonction
                    key_metric TEXT,
                    value REAL,
                    trend_direction TEXT,  -- up, down, stable
                    confidence_score REAL,
                    data_points INTEGER,
                    metadata TEXT,  -- JSON
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des profils d'entreprise
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS company_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    normalized_name TEXT,
                    industry TEXT,
                    size TEXT,
                    description TEXT,
                    culture_keywords TEXT,  -- JSON
                    benefits TEXT,          -- JSON
                    tech_stack TEXT,        -- JSON
                    hiring_trends TEXT,     -- JSON
                    linkedin_url TEXT,
                    website_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Tables de base de données créées")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables: {e}")
            raise
    
    async def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Stocke une offre d'emploi complète"""
        try:
            # Stockage dans la base principale
            success = self.store_job_main(job_data)
            
            # Stockage dans le moteur de recherche si disponible
            if success and self.search_engine:
                if EMBEDDING_METHOD == "ollama":
                    await self.search_engine.store_job_with_embedding(job_data)
                elif EMBEDDING_METHOD == "tfidf":
                    self.search_engine.store_job(job_data)
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur stockage offre: {e}")
            return False
    
    def store_job_main(self, job_data: Dict[str, Any]) -> bool:
        """Stockage dans la table principale"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Vérification unicité
            hash_id = job_data.get('hash_id', self.generate_hash(job_data))
            
            cursor.execute('SELECT 1 FROM job_offers_main WHERE hash_id = ?', (hash_id,))
            if cursor.fetchone():
                return False  # Déjà existant
            
            # Insertion
            salary_info = job_data.get('salary', {})
            
            cursor.execute('''
                INSERT INTO job_offers_main (
                    hash_id, title, company, location, description,
                    requirements, technologies, salary_min, salary_max, salary_text,
                    experience_level, remote, contract_type, url, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hash_id,
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('location', ''),
                job_data.get('description', ''),
                json.dumps(job_data.get('requirements', [])),
                json.dumps(job_data.get('technologies', [])),
                salary_info.get('min'),
                salary_info.get('max'),
                salary_info.get('text', ''),
                job_data.get('experience_level', 'mid'),
                job_data.get('remote', False),
                job_data.get('contract_type', ''),
                job_data.get('url', ''),
                job_data.get('source', '')
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Erreur stockage base principale: {e}")
            return False
        finally:
            conn.close()
    
    async def search_jobs(self, query: str, filters: Dict[str, Any] = None, 
                         limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche hybride selon le moteur disponible"""
        
        # Recherche avec moteur spécialisé si disponible
        search_results = []
        
        if self.search_engine:
            try:
                if EMBEDDING_METHOD == "ollama":
                    search_results = await self.search_engine.search_similar_jobs(
                        query, limit=limit*2
                    )
                elif EMBEDDING_METHOD == "tfidf":
                    search_results = self.search_engine.search_jobs(
                        query, limit=limit*2
                    )
            except Exception as e:
                logger.warning(f"Erreur recherche spécialisée: {e}")
        
        # Recherche SQL de base en complément ou fallback
        sql_results = self.search_jobs_sql(query, filters, limit)
        
        # Fusion des résultats
        return self.merge_search_results(search_results, sql_results, limit)
    
    def search_jobs_sql(self, query: str, filters: Dict[str, Any] = None, 
                       limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche SQL de base"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construction de la requête SQL
            where_conditions = ["is_active = 1"]
            params = []
            
            # Recherche textuelle simple
            if query:
                where_conditions.append('''
                    (title LIKE ? OR company LIKE ? OR description LIKE ? 
                     OR technologies LIKE ? OR location LIKE ?)
                ''')
                search_term = f"%{query}%"
                params.extend([search_term] * 5)
            
            # Filtres additionnels
            if filters:
                if filters.get('location'):
                    where_conditions.append("location LIKE ?")
                    params.append(f"%{filters['location']}%")
                
                if filters.get('experience_level'):
                    where_conditions.append("experience_level = ?")
                    params.append(filters['experience_level'])
                
                if filters.get('remote') is not None:
                    where_conditions.append("remote = ?")
                    params.append(filters['remote'])
                
                if filters.get('company'):
                    where_conditions.append("company LIKE ?")
                    params.append(f"%{filters['company']}%")
            
            # Requête finale
            sql_query = f'''
                SELECT hash_id, title, company, location, description, technologies,
                       experience_level, remote, url, source, salary_text
                FROM job_offers_main
                WHERE {' AND '.join(where_conditions)}
                ORDER BY scraped_at DESC
                LIMIT ?
            '''
            params.append(limit)
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            conn.close()
            
            # Formatage des résultats
            results = []
            for row in rows:
                results.append({
                    'hash_id': row[0],
                    'title': row[1],
                    'company': row[2],
                    'location': row[3],
                    'description': row[4][:300] + "..." if len(row[4]) > 300 else row[4],
                    'technologies': json.loads(row[5]) if row[5] else [],
                    'experience_level': row[6],
                    'remote': bool(row[7]),
                    'url': row[8],
                    'source': row[9],
                    'salary_text': row[10],
                    'search_method': 'sql'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche SQL: {e}")
            return []
    
    def merge_search_results(self, search_results: List[Dict], 
                           sql_results: List[Dict], limit: int) -> List[Dict[str, Any]]:
        """Fusionne les résultats de recherche"""
        
        # Si pas de résultats de recherche spécialisée, utiliser SQL
        if not search_results:
            return sql_results[:limit]
        
        # Fusion intelligente en évitant les doublons
        merged = []
        seen_ids = set()
        
        # Ajouter d'abord les résultats de recherche spécialisée (meilleur scoring)
        for result in search_results:
            hash_id = result.get('hash_id') or result.get('content_hash')
            if hash_id and hash_id not in seen_ids:
                merged.append(result)
                seen_ids.add(hash_id)
        
        # Compléter avec les résultats SQL
        for result in sql_results:
            hash_id = result.get('hash_id')
            if hash_id and hash_id not in seen_ids and len(merged) < limit:
                merged.append(result)
                seen_ids.add(hash_id)
        
        return merged[:limit]
    
    async def get_market_insights(self) -> Dict[str, Any]:
        """Génère des insights du marché basés sur les données collectées"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Statistiques de base
            cursor.execute('SELECT COUNT(*) FROM job_offers_main WHERE is_active = 1')
            total_jobs = cursor.fetchone()[0]
            
            if total_jobs == 0:
                return {
                    'total_jobs': 0,
                    'message': 'Aucune donnée disponible - démarrez le scraping'
                }
            
            # Top technologies
            cursor.execute('SELECT technologies FROM job_offers_main WHERE technologies IS NOT NULL')
            tech_data = cursor.fetchall()
            
            tech_count = {}
            for row in tech_data:
                try:
                    technologies = json.loads(row[0])
                    for tech in technologies:
                        tech_count[tech] = tech_count.get(tech, 0) + 1
                except:
                    continue
            
            top_technologies = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Distribution des niveaux d'expérience
            cursor.execute('''
                SELECT experience_level, COUNT(*) 
                FROM job_offers_main 
                WHERE experience_level IS NOT NULL 
                GROUP BY experience_level
            ''')
            exp_levels = cursor.fetchall()
            
            # Pourcentage de remote
            cursor.execute('SELECT COUNT(*) FROM job_offers_main WHERE remote = 1')
            remote_count = cursor.fetchone()[0]
            remote_percentage = (remote_count / total_jobs * 100) if total_jobs > 0 else 0
            
            # Top entreprises qui recrutent
            cursor.execute('''
                SELECT company, COUNT(*) as job_count
                FROM job_offers_main 
                WHERE company IS NOT NULL
                GROUP BY company 
                ORDER BY job_count DESC 
                LIMIT 10
            ''')
            top_companies = cursor.fetchall()
            
            # Évolution récente (derniers 7 jours vs avant)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM job_offers_main 
                WHERE scraped_at >= datetime('now', '-7 days')
            ''')
            recent_jobs = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_jobs': total_jobs,
                'recent_jobs_7d': recent_jobs,
                'top_technologies': [{'name': tech, 'count': count} for tech, count in top_technologies],
                'experience_distribution': [{'level': level or 'Unknown', 'count': count} for level, count in exp_levels],
                'remote_percentage': round(remote_percentage, 1),
                'top_hiring_companies': [{'name': company, 'jobs': count} for company, count in top_companies],
                'last_updated': datetime.now().isoformat(),
                'data_quality': {
                    'tech_coverage': len([t for t in tech_count if tech_count[t] > 1]),
                    'company_diversity': len(top_companies),
                    'remote_data_available': remote_count > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur génération insights: {e}")
            return {'error': str(e), 'total_jobs': 0}
    
    def get_company_insights(self, company_name: str) -> Dict[str, Any]:
        """Insights spécifiques à une entreprise"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Normalisation du nom d'entreprise
            normalized_name = company_name.lower().strip()
            
            # Offres de cette entreprise
            cursor.execute('''
                SELECT title, location, experience_level, remote, technologies, scraped_at
                FROM job_offers_main 
                WHERE LOWER(company) LIKE ? AND is_active = 1
                ORDER BY scraped_at DESC
            ''', (f"%{normalized_name}%",))
            
            company_jobs = cursor.fetchall()
            conn.close()
            
            if not company_jobs:
                return {'company': company_name, 'jobs_found': 0, 'insights': 'Aucune donnée disponible'}
            
            # Analyse des données
            total_jobs = len(company_jobs)
            remote_jobs = sum(1 for job in company_jobs if job[3])  # remote column
            
            # Technologies utilisées
            all_techs = []
            for job in company_jobs:
                if job[4]:  # technologies column
                    try:
                        techs = json.loads(job[4])
                        all_techs.extend(techs)
                    except:
                        continue
            
            tech_count = {}
            for tech in all_techs:
                tech_count[tech] = tech_count.get(tech, 0) + 1
            
            top_techs = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Niveaux d'expérience
            exp_levels = {}
            for job in company_jobs:
                level = job[2] or 'Unknown'  # experience_level column
                exp_levels[level] = exp_levels.get(level, 0) + 1
            
            return {
                'company': company_name,
                'jobs_found': total_jobs,
                'remote_percentage': round((remote_jobs / total_jobs) * 100, 1),
                'top_technologies': [{'tech': tech, 'count': count} for tech, count in top_techs],
                'experience_levels': exp_levels,
                'recent_activity': total_jobs > 0,
                'hiring_trend': 'Active' if total_jobs > 2 else 'Limited',
                'last_job_posted': company_jobs[0][5] if company_jobs else None  # scraped_at
            }
            
        except Exception as e:
            logger.error(f"Erreur insights entreprise: {e}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes de la base de connaissances"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Stats principales
            cursor.execute('SELECT COUNT(*) FROM job_offers_main')
            total_jobs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM job_offers_main WHERE is_active = 1')
            active_jobs = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT source, COUNT(*) 
                FROM job_offers_main 
                GROUP BY source
            ''')
            sources = dict(cursor.fetchall())
            
            cursor.execute('SELECT MAX(scraped_at) FROM job_offers_main')
            last_scrape = cursor.fetchone()[0]
            
            conn.close()
            
            # Stats du moteur de recherche
            search_stats = {}
            if self.search_engine:
                search_stats = self.search_engine.get_stats()
            
            return {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'sources': sources,
                'last_scrape': last_scrape,
                'search_method': EMBEDDING_METHOD,
                'search_engine_stats': search_stats,
                'database_path': self.db_path
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            return {'error': str(e)}
    
    def generate_hash(self, job_data: Dict[str, Any]) -> str:
        """Génère un hash unique pour l'offre"""
        import hashlib
        
        unique_string = f"{job_data.get('title', '')}{job_data.get('company', '')}{job_data.get('url', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Nettoie les offres anciennes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE job_offers_main 
                SET is_active = 0 
                WHERE scraped_at < datetime('now', '-{} days')
                AND is_active = 1
            '''.format(days_old))
            
            cleaned_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"🧹 {cleaned_count} offres anciennes désactivées")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")
            return 0