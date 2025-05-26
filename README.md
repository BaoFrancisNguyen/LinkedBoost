# LinkedBoost 🚀
## Assistant IA Complet pour LinkedIn et Recherche d'Emploi

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![Ollama](https://img.shields.io/badge/Ollama-Mistral-orange.svg)](https://ollama.ai)
[![Selenium](https://img.shields.io/badge/Selenium-4.15+-red.svg)](https://selenium.dev)

> **LinkedBoost** est une plateforme complète d'intelligence artificielle qui révolutionne votre recherche d'emploi et optimise votre présence LinkedIn grâce à la génération automatique de contenu professionnel et au scraping intelligent d'offres d'emploi.

---

## 🎯 Fonctionnalités Principales

### 🤖 **Génération IA Avancée**
- **Messages LinkedIn** personnalisés (connexions, suivi, opportunités)
- **Lettres de motivation** adaptées à chaque poste
- **Emails de networking** professionnels
- **Analyse de profil LinkedIn** avec recommandations d'optimisation

### 🕷️ **Scraping Intelligent Multi-Sources**
- **Welcome to the Jungle** - Offres tech et startup
- **LinkedIn Jobs** - Réseau professionnel
- **Indeed** - Large catalogue d'emplois
- **Scraping temps réel** avec Selenium
- **Gestion anti-détection** avancée

### 🧠 **Base de Connaissances & RAG**
- **Indexation automatique** des offres collectées
- **Recherche sémantique** intelligente
- **Analytics marché** en temps réel
- **Insights entreprises** basés sur les données collectées
- **Enrichissement contextuel** des générations IA

### 🎛️ **Interface d'Administration**
- **Dashboard en temps réel** avec WebSocket
- **Monitoring des scrapers** avec logs live
- **Gestion de la base de connaissances**
- **Statistiques et métriques** détaillées

---

## 🚀 Installation Rapide

### Prérequis
- **Python 3.8+**
- **Ollama** installé et configuré
- **Chrome** (pour le scraping Selenium)
- **Git** (optionnel)

### Installation Automatique
```bash
# 1. Cloner le projet
git clone https://github.com/votre-repo/linkedboost.git
cd linkedboost

# 2. Configuration automatique
python setup_config.py

# 3. Installation des dépendances
pip install -r requirements.txt

# 4. Configuration d'Ollama
ollama serve
ollama pull mistral:latest

# 5. Test du système
python test_linkedboost.py

# 6. Lancement de l'application
python app.py
```

### Installation Manuelle
```bash
# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer la structure
mkdir -p data logs cache models scrapers

# Configuration
cp .env.template .env
# Modifier .env selon vos besoins

# Démarrage
python app.py
```

---

## 🌐 Accès et Utilisation

### URLs Principales
- **Application** : http://localhost:5000
- **Administration** : http://localhost:5000/admin
- **API Status** : http://localhost:5000/api/status
- **Scraping Dashboard** : http://localhost:5000/admin/scraper

### Interface Utilisateur
```
🏠 Dashboard Principal
├── 📝 Générateurs de Contenu
│   ├── Messages LinkedIn
│   ├── Lettres de Motivation
│   └── Emails de Networking
├── 📊 Analyse de Profil LinkedIn
└── 🔧 Administration
    ├── Scraping & Collecte
    ├── Base de Connaissances
    └── Monitoring Système
```

### API REST
```bash
# Génération de message LinkedIn
POST /api/generate/message
{
  "message_type": "connection",
  "recipient_name": "Marie Dubois",
  "context": "Même secteur d'activité"
}

# Recherche dans la base de connaissances
POST /api/knowledge/search
{
  "query": "développeur python remote",
  "limit": 20
}

# Lancement du scraping
POST /api/scraping/start
{
  "sources": ["wttj", "linkedin"],
  "max_jobs": 50
}
```

---

## 🔧 Configuration Avancée

### Variables d'Environnement (.env)
```bash
# IA et Génération
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest

# Scraping
SCRAPING_ENABLED=True
SELENIUM_HEADLESS=False  # True pour production
ENABLED_SCRAPERS=wttj,linkedin,indeed

# Rate Limiting
REQUEST_DELAY=2.0
MAX_JOBS_PER_SCRAPE=100

# Credentials LinkedIn (optionnel)
LINKEDIN_EMAIL=votre@email.com
LINKEDIN_PASSWORD=votre_mot_de_passe

# Base de données
DATABASE_URL=sqlite:///data/linkedboost.db
```

### Configuration des Scrapers
```python
# Modifier dans config.py
WTTJ_MAX_JOBS = 30
INDEED_MAX_JOBS = 25  
LINKEDIN_MAX_JOBS = 20
MAX_PAGES_PER_SEARCH = 3
```

---

## 🏗️ Architecture Technique

### Structure du Projet
```
linkedboost/
├── 🎯 app.py                    # Application Flask principale
├── ⚙️ config.py                # Configuration centralisée
├── 📋 requirements.txt         # Dépendances Python
├── 🧪 test_linkedboost.py     # Tests système complets
├── 🛠️ setup_config.py         # Configuration automatique
│
├── 📁 models/                  # Logique métier et IA
│   ├── ai_generator.py         # Génération IA avec Ollama
│   ├── scraper.py             # Orchestrateur de scraping
│   ├── knowledge_base.py      # Base de connaissances
│   ├── embeddings.py          # Gestion des embeddings
│   └── simple_search.py       # Moteur de recherche TF-IDF
│
├── 📁 scrapers/               # Scrapers Selenium
│   ├── base_scraper.py        # Classe de base
│   ├── wttj_scraper.py        # Welcome to the Jungle
│   ├── linkedin_scraper.py    # LinkedIn Jobs
│   └── indeed_scraper.py      # Indeed
│
├── 📁 templates/              # Interface Web
│   ├── base.html              # Template de base
│   ├── index.html             # Dashboard principal
│   ├── admin/                 # Interface d'administration
│   └── [générateurs].html     # Pages de génération
│
├── 📁 static/                 # Assets statiques
│   ├── css/style.css          # Styles personnalisés
│   └── js/app.js              # JavaScript principal
│
└── 📁 data/                   # Données persistantes
    ├── linkedboost.db         # Base SQLite principale
    ├── scraped/               # Données scrapées
    └── reports/               # Rapports de scraping
```

### Technologies Utilisées
- **Backend** : Flask, SQLAlchemy, APScheduler
- **IA** : Ollama (Mistral), Sentence Transformers
- **Scraping** : Selenium WebDriver, BeautifulSoup
- **Frontend** : Bootstrap 5, JavaScript ES6
- **Base de données** : SQLite (développement), PostgreSQL (production)

---

## 🤖 Fonctionnalités IA Détaillées

### Génération de Messages LinkedIn
```python
# Types supportés
- connection      # Demandes de connexion
- follow_up       # Messages de suivi  
- opportunity     # Présentation d'opportunités

# Personnalisation automatique
- Analyse du profil destinataire
- Contexte d'entreprise (RAG)
- Connexions communes
- Ton adapté (professionnel, créatif, etc.)
```

### Analyse de Profil LinkedIn
- **Score global** /10 avec justification
- **Points forts** identifiés automatiquement
- **Améliorations suggérées** prioritaires
- **Titre professionnel** optimisé
- **Résumé réécrit** avec mots-clés
- **Mots-clés manquants** pour le secteur

### Enrichissement RAG (Retrieval-Augmented Generation)
- **Insights marché** intégrés dans les générations
- **Données entreprise** pour personnalisation
- **Tendances technologiques** du secteur
- **Statistiques salariales** contextuelles

---

## 🕷️ Système de Scraping

### Scrapers Disponibles
| Source | Offres/jour | Spécialisation | Authentification |
|--------|-------------|----------------|------------------|
| **WTTJ** | 1000+ | Tech, Startups | ❌ Non requise |
| **LinkedIn** | 500+ | Tous secteurs | ⚠️ Optionnelle |
| **Indeed** | 2000+ | Généraliste | ❌ Non requise |

### Fonctionnalités Anti-Détection
- **User-Agent** rotatif réaliste
- **Délais aléatoires** entre requêtes
- **Headers HTTP** authentiques
- **Gestion cookies** automatique
- **Proxy support** (configuration)

### Données Extraites
```json
{
  "title": "Développeur Full Stack Senior",
  "company": "TechCorp",
  "location": "Paris / Remote",
  "description": "Description complète...",
  "technologies": ["Python", "React", "AWS"],
  "experience_level": "senior",
  "remote": true,
  "salary": {"min": 55000, "max": 70000},
  "url": "https://...",
  "source": "wttj"
}
```

---

## 📊 Analytics et Insights

### Dashboard Administrateur
- **Offres collectées** par source et période
- **Technologies trending** sur le marché
- **Répartition géographique** des emplois
- **Statistiques salariales** par poste
- **Taux de remote** par secteur

### Base de Connaissances
- **Recherche sémantique** avec embeddings
- **Filtrage avancé** (lieu, niveau, remote)
- **Export des données** (CSV, JSON)
- **Insights entreprise** personnalisés

---

## 🧪 Tests et Validation

### Tests Automatisés
```bash
# Test complet du système
python test_linkedboost.py

# Tests unitaires
pytest tests/

# Test des scrapers individuels
python -m scrapers.wttj_scraper
python -m scrapers.linkedin_scraper
```

### Validation de Configuration
```bash
# Vérification de l'environnement
python -c "from config import Config; print(Config.validate_config())"

# Test de connexion Ollama
curl http://localhost:11434/api/tags

# Status de l'application
curl http://localhost:5000/api/status
```

---

## 🚀 Déploiement Production

### Docker (Recommandé)
```bash
# Build et démarrage
docker-compose up -d

# Monitoring
docker-compose logs -f
```

### Serveur Traditionnel
```bash
# Installation Gunicorn
pip install gunicorn

# Démarrage production
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Avec Nginx (reverse proxy)
# Voir configuration dans /docs/nginx.conf
```

### Variables d'Environnement Production
```bash
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key
DATABASE_URL=postgresql://user:pass@localhost/linkedboost
OLLAMA_BASE_URL=http://ollama-server:11434
SELENIUM_HEADLESS=True
```

---

## 📈 Performance et Limites

### Performances Typiques
- **Génération IA** : ~2-5 secondes/message
- **Scraping** : ~50-100 offres/minute
- **Recherche** : <100ms pour 10K offres
- **Interface** : Temps de chargement <1s

### Limites Recommandées
- **Max offres/jour** : 2000 (anti-détection)
- **Utilisateurs simultanés** : 10-20
- **Stockage base** : ~1GB pour 100K offres
- **RAM recommandée** : 4GB minimum

---

## 🛠️ Développement et Contribution

### Environnement de Développement
```bash
# Configuration développement
python dev.py setup

# Formatage du code
python dev.py format

# Tests
python dev.py test

# Nettoyage
python dev.py clean
```

### Structure de Contribution
1. **Fork** le projet
2. **Créer** une branche feature
3. **Développer** avec tests
4. **Valider** avec `test_linkedboost.py`
5. **Proposer** une Pull Request

### Ajout d'un Nouveau Scraper
```python
# 1. Hériter de BaseScraper
class MonScraper(BaseScraper):
    def __init__(self):
        super().__init__('MonSite')
    
    async def scrape_jobs(self, limit: int):
        # Implémentation du scraping
        pass

# 2. Ajouter dans config.py
ENABLED_SCRAPERS = "wttj,linkedin,indeed,monsite"

# 3. Enregistrer dans l'orchestrateur
# models/scraper.py
```

---

## 🆘 Dépannage et Support

### Problèmes Courants

#### Ollama Non Disponible
```bash
# Vérifier le statut
ollama serve
curl http://localhost:11434/api/tags

# Réinstaller le modèle
ollama pull mistral:latest
```

#### Scraping Bloqué
```bash
# Mode debug (navigateur visible)
python -c "from config import Config; Config.enable_debug_mode()"

# Vérifier les logs
tail -f logs/linkedboost.log
```

#### Base de Données Corrompue
```bash
# Réinitialiser
rm data/*.db
python app.py  # Recréera automatiquement
```

### Logs et Diagnostics
```bash
# Logs applicatifs
tail -f logs/linkedboost.log

# Logs de scraping
tail -f logs/scraping.log

# Status système
python -c "from models.ai_generator import LinkedBoostAI; print(LinkedBoostAI().get_system_status())"
```

---

## 📄 Licence et Légal

### Licence
Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour les détails.

### Considérations Légales
- ⚖️ **Respect des CGU** des sites scrapés
- 🤖 **Rate limiting** pour éviter la surcharge
- 🔒 **Données personnelles** non collectées
- 📋 **Usage éthique** recommandé

### Disclaimer
LinkedBoost est un outil d'assistance. L'utilisateur reste responsable :
- Du respect des conditions d'utilisation des plateformes
- De la vérification des informations générées
- De la personnalisation des contenus avant envoi

---

## 🎯 Roadmap

### Version 2.0 (Q2 2025)
- [ ] **Scraper Jobijoba** et **Monster**
- [ ] **Notifications push** temps réel
- [ ] **API GraphQL** avancée
- [ ] **Multi-langues** (EN, ES, DE)

### Version 2.1 (Q3 2025)
- [ ] **Integration Slack/Teams** 
- [ ] **Chrome Extension**
- [ ] **Mobile App** (React Native)
- [ ] **AI Training** personnalisé

### Contributions Bienvenues
- 🆕 **Nouveaux scrapers**
- 🌐 **Traductions**
- 🧪 **Tests automatisés**
- 📚 **Documentation**

---

## 📞 Contact et Support

### Communauté
- 💬 **Discord** : [LinkedBoost Community](https://discord.gg/linkedboost)
- 🐛 **Issues** : [GitHub Issues](https://github.com/linkedboost/linkedboost/issues)
- 📧 **Email** : support@linkedboost.com

### Maintainers
- **Lead Developer** : [@votre-github](https://github.com/votre-github)
- **AI Specialist** : [@ia-expert](https://github.com/ia-expert)
- **DevOps** : [@devops-lead](https://github.com/devops-lead)

---

## ⭐ Remerciements

- **Ollama Team** pour l'infrastructure IA locale
- **Selenium Community** pour les outils de scraping
- **Flask Team** pour le framework web
- **Tous les contributeurs** de la communauté

---

<div align="center">

### 🚀 Prêt à révolutionner votre recherche d'emploi ?

**[⬇️ Télécharger LinkedBoost](https://github.com/linkedboost/linkedboost/releases)** 
**[📚 Documentation Complète](https://docs.linkedboost.com)**
**[🎯 Démo en Ligne](https://demo.linkedboost.com)**

---

*Fait avec ❤️ par l'équipe LinkedBoost*

</div>
