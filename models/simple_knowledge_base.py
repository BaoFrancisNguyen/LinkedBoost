# models/simple_knowledge_base.py - Version sans Hugging Face
import sqlite3
import json
from typing import List, Dict, Any
from datetime import datetime
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

class SimpleKnowledgeBase:
    """Base de connaissances simplifiée sans dépendances Hugging Face"""
    
    def __init__(self):
        self.db_path = "data/simple_knowledge_base.db"
        self.create_tables()
    
    def create_tables(self):
        """Crée les tables de base de données"""
        import os
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_offers_simple (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id TEXT UNIQUE,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                technologies TEXT,  -- JSON
                experience_level TEXT,
                remote BOOLEAN DEFAULT FALSE,
                salary_text TEXT,
                url TEXT,
                source TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                search_text TEXT  -- Texte pour recherche full-text
            )
        ''')
        
        # Index pour la recherche
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_search_text 
            ON job_offers_simple(search_text)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Base de données simple créée")
    
    async def store_job(self, job_data: Dict[str, Any]) -> bool:
        """Stocke une offre d'emploi"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construction du texte de recherche
            search_text = self.build_search_text(job_data)
            hash_id = job_data.get('hash_id', self.generate_hash(job_data))
            
            # Vérification unicité
            cursor.execute('SELECT 1 FROM job_offers_simple WHERE hash_id = ?', (hash_id,))
            if cursor.fetchone():
                return False  # Déjà existant
            
            cursor.execute('''
                INSERT INTO job_offers_simple (
                    hash_id, title, company, location, description,
                    technologies, experience_level, remote, salary_text,
                    url, source, search_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hash_id,
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('location', ''),
                job_data.get('description', ''),
                json.dumps(job_data.get('technologies', [])),
                job_data.get('experience_level', 'mid'),
                job_data.get('remote', False),
                job_data.get('salary', {}).get('text', ''),
                job_data.get('url', ''),
                job_data.get('source', ''),
                search_text
            ))
            
            conn.commit()
            logger.debug(f"✅ Offre stockée: {job_data.get('title', 'Sans titre')}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur stockage offre: {e}")
            return False
        finally:
            conn.close()
    
    def build_search_text(self, job_data: Dict[str, Any]) -> str:
        """Construit le texte de recherche optimisé"""
        parts = [
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('description', ''),
            ' '.join(job_data.get('technologies', [])),
            job_data.get('experience_level', '')
        ]
        
        # Nettoyage et normalisation
        search_text = ' '.join(filter(None, parts))
        search_text = re.sub(r'[^\w\s]', ' ', search_text.lower())
        search_text = re.sub(r'\s+', ' ', search_text)
        
        return search_text.strip()
    
    async def search_jobs(self, query: str, filters: Dict[str, Any] = None, 
                         limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche simple basée sur SQL LIKE"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Construction de la requête
            where_conditions = []
            params = []
            
            # Recherche textuelle
            if query:
                query_words = query.lower().split()
                for word in query_words:
                    where_conditions.append("search_text LIKE ?")
                    params.append(f"%{word}%")
            
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
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            sql_query = f'''
                SELECT hash_id, title, company, location, description,
                       technologies, experience_level, remote, url, source, salary_text
                FROM job_offers_simple
                WHERE {where_clause}
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
                    'search_method': 'simple_sql'
                })
            
            logger.info(f"🔍 Trouvé {len(results)} offres pour '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche: {e}")
            return []
    
    async def get_market_insights(self) -> Dict[str, Any]:
        """Génère des insights basiques du marché"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Stats de base
            cursor.execute('SELECT COUNT(*) FROM job_offers_simple')
            total_jobs = cursor.fetchone()[0]
            
            if total_jobs == 0:
                return {'total_jobs': 0, 'message': 'Aucune donnée - lancez le scraping'}
            
            # Top technologies
            cursor.execute('SELECT technologies FROM job_offers_simple')
            tech_data = cursor.fetchall()
            
            all_techs = []
            for row in tech_data:
                try:
                    techs = json.loads(row[0])
                    all_techs.extend(techs)
                except:
                    continue
            
            tech_count = Counter(all_techs)
            top_technologies = [{'name': tech, 'count': count} 
                              for tech, count in tech_count.most_common(10)]
            
            # Remote stats
            cursor.execute('SELECT COUNT(*) FROM job_offers_simple WHERE remote = 1')
            remote_count = cursor.fetchone()[0]
            remote_percentage = round((remote_count / total_jobs * 100), 1)
            
            # Top entreprises
            cursor.execute('''
                SELECT company, COUNT(*) as count
                FROM job_offers_simple 
                GROUP BY company 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_companies = [{'name': comp, 'jobs': count} 
                           for comp, count in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_jobs': total_jobs,
                'top_technologies': top_technologies,
                'remote_percentage': remote_percentage,
                'top_hiring_companies': top_companies,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur insights: {e}")
            return {'error': str(e)}
    
    def get_company_insights(self, company_name: str) -> Dict[str, Any]:
        """Insights sur une entreprise spécifique"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            normalized_name = company_name.lower().strip()
            
            cursor.execute('''
                SELECT title, location, experience_level, remote, technologies
                FROM job_offers_simple 
                WHERE LOWER(company) LIKE ?
            ''', (f"%{normalized_name}%",))
            
            jobs = cursor.fetchall()
            conn.close()
            
            if not jobs:
                return {'company': company_name, 'jobs_found': 0}
            
            # Analyse basique
            total_jobs = len(jobs)
            remote_jobs = sum(1 for job in jobs if job[3])
            
            # Technologies
            all_techs = []
            for job in jobs:
                if job[4]:
                    try:
                        techs = json.loads(job[4])
                        all_techs.extend(techs)
                    except:
                        continue
            
            tech_count = Counter(all_techs)
            top_techs = [{'tech': tech, 'count': count} 
                        for tech, count in tech_count.most_common(5)]
            
            return {
                'company': company_name,
                'jobs_found': total_jobs,
                'remote_percentage': round((remote_jobs / total_jobs) * 100, 1),
                'top_technologies': top_techs,
                'hiring_trend': 'Active' if total_jobs > 2 else 'Limited'
            }
            
        except Exception as e:
            logger.error(f"Erreur insights entreprise: {e}")
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques de la base"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM job_offers_simple')
            total_jobs = cursor.fetchone()[0]
            
            cursor.execute('SELECT source, COUNT(*) FROM job_offers_simple GROUP BY source')
            sources = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_jobs': total_jobs,
                'sources': sources,
                'search_method': 'simple_sql',
                'database_path': self.db_path
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def generate_hash(self, job_data: Dict[str, Any]) -> str:
        """Génère un hash pour l'offre"""
        import hashlib
        unique_string = f"{job_data.get('title', '')}{job_data.get('company', '')}{job_data.get('url', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()