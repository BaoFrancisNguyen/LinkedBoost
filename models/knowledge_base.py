# models/knowledge_base.py - Correction import EmbeddingManager

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """Base de connaissances - Version avec import corrigé"""
    
    def __init__(self):
        self.db_path = "data/knowledge_base.db"
        self.embedding_manager = None
        
        # Initialisation conditionnelle des embeddings - CORRECTION
        try:
            from models.embeddings import EmbeddingManager  # Import local
            self.embedding_manager = EmbeddingManager()
            self.embeddings_enabled = self.embedding_manager.method != "none"
            logger.info(f"🧠 Base de connaissances initialisée (embeddings: {self.embeddings_enabled})")
        except ImportError as e:
            self.embeddings_enabled = False
            logger.warning(f"⚠️ EmbeddingManager non disponible: {e}")
        except Exception as e:
            self.embeddings_enabled = False
            logger.warning(f"⚠️ Base de connaissances sans embeddings: {e}")
        
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
            
            conn.commit()
            conn.close()
            logger.info("✅ Tables de base de données créées")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables: {e}")
            raise
    
    async def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Stocke une offre d'emploi"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérification unicité
            hash_id = job_data.get('hash_id')
            if not hash_id:
                hash_id = self.generate_hash(job_data)
            
            cursor.execute('SELECT 1 FROM job_offers_main WHERE hash_id = ?', (hash_id,))
            if cursor.fetchone():
                conn.close()
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
                salary_info.get('min') if isinstance(salary_info, dict) else None,
                salary_info.get('max') if isinstance(salary_info, dict) else None,
                salary_info.get('text', '') if isinstance(salary_info, dict) else str(salary_info),
                job_data.get('experience_level', 'mid'),
                job_data.get('remote', False),
                job_data.get('contract_type', ''),
                job_data.get('url', ''),
                job_data.get('source', '')
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur stockage offre: {e}")
            return False
    
    async def search_jobs(self, query: str, filters: Dict[str, Any] = None, 
                         limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche d'offres d'emploi"""
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
            logger.error(f"Erreur recherche: {e}")
            return []
    
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
            
            conn.close()
            
            return {
                'total_jobs': total_jobs,
                'top_technologies': [{'name': tech, 'count': count} for tech, count in top_technologies],
                'experience_distribution': [{'level': level or 'Unknown', 'count': count} for level, count in exp_levels],
                'remote_percentage': round(remote_percentage, 1),
                'top_hiring_companies': [{'name': company, 'jobs': count} for company, count in top_companies],
                'last_updated': datetime.now().isoformat()
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
            
            return {
                'company': company_name,
                'jobs_found': total_jobs,
                'remote_percentage': round((remote_jobs / total_jobs) * 100, 1),
                'top_technologies': [{'tech': tech, 'count': count} for tech, count in top_techs],
                'hiring_trend': 'Active' if total_jobs > 2 else 'Limited',
                'last_job_posted': company_jobs[0][5] if company_jobs else None
            }
            
        except Exception as e:
            logger.error(f"Erreur insights entreprise: {e}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la base de connaissances"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
            
            return {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'sources': sources,
                'last_scrape': last_scrape,
                'embeddings_enabled': self.embeddings_enabled,
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