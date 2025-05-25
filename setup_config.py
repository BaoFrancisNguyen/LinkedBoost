#!/usr/bin/env python3
# setup_config.py - Script de configuration automatique LinkedBoost
import os
import sys
import shutil
from pathlib import Path

def create_directories():
    """Crée la structure de dossiers nécessaire"""
    directories = [
        'data',
        'logs', 
        'cache',
        'models',
        'scrapers',
        'templates/admin',
        'static/css',
        'static/js',
        'tests'
    ]
    
    print("📁 Création de la structure de dossiers...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")

def setup_env_file():
    """Configure le fichier .env"""
    env_file = Path('.env')
    env_template = Path('.env.template')
    
    if env_file.exists():
        print("⚠️  Le fichier .env existe déjà")
        response = input("Voulez-vous le remplacer ? (y/N): ")
        if response.lower() != 'y':
            print("   📝 Fichier .env conservé")
            return
    
    if env_template.exists():
        shutil.copy('.env.template', '.env')
        print("✅ Fichier .env créé depuis le template")
    else:
        # Création d'un .env minimal
        env_content = """# Configuration LinkedBoost - Générée automatiquement
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=linkedboost-dev-key-change-in-production

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest

# Scraping
SCRAPING_ENABLED=True
SELENIUM_HEADLESS=True
REQUEST_DELAY=2.0
ENABLED_SCRAPERS=wttj

# Base de données
DATABASE_URL=sqlite:///data/linkedboost.db
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Fichier .env minimal créé")

def check_dependencies():
    """Vérifie les dépendances Python"""
    print("\n📦 Vérification des dépendances...")
    
    # Dépendances critiques
    critical_deps = {
        'flask': 'Flask',
        'requests': 'requests',
        'python-dotenv': 'dotenv',
        'beautifulsoup4': 'bs4'
    }
    
    # Dépendances optionnelles
    optional_deps = {
        'selenium': 'selenium',
        'pandas': 'pandas', 
        'sklearn': 'scikit-learn',
        'sentence-transformers': 'sentence_transformers'
    }
    
    missing_critical = []
    missing_optional = []
    
    for pkg_name, import_name in critical_deps.items():
        try:
            __import__(import_name.replace('-', '_'))
            print(f"   ✅ {pkg_name}")
        except ImportError:
            print(f"   ❌ {pkg_name} MANQUANT")
            missing_critical.append(pkg_name)
    
    for pkg_name, import_name in optional_deps.items():
        try:
            __import__(import_name.replace('-', '_'))
            print(f"   ✅ {pkg_name} (optionnel)")
        except ImportError:
            print(f"   ⚠️  {pkg_name} (optionnel)")
            missing_optional.append(pkg_name)
    
    if missing_critical:
        print(f"\n❌ Dépendances critiques manquantes: {', '.join(missing_critical)}")
        print("   Installation: pip install " + ' '.join(missing_critical))
        return False
    
    if missing_optional:
        print(f"\n💡 Dépendances optionnelles manquantes: {', '.join(missing_optional)}")
        print("   Pour le scraping complet: pip install selenium webdriver-manager")
        print("   Pour les embeddings: pip install sentence-transformers")
    
    return True

def test_ollama_connection():
    """Teste la connexion à Ollama"""
    print("\n🤖 Test de connexion à Ollama...")
    
    try:
        import requests
        from config import Config
        
        response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"   ✅ Ollama connecté ({len(models)} modèles disponibles)")
            
            # Vérifier si Mistral est disponible
            model_names = [m.get('name', '') for m in models]
            if any('mistral' in name for name in model_names):
                print("   ✅ Modèle Mistral disponible")
            else:
                print("   ⚠️  Modèle Mistral non trouvé")
                print("   Installation: ollama pull mistral:latest")
            
            return True
        else:
            print(f"   ❌ Erreur HTTP {response.status_code}")
            return False
            
    except ImportError:
        print("   ❌ Module 'requests' manquant")
        return False
    except Exception as e:
        print(f"   ❌ Erreur connexion: {e}")
        print("   💡 Démarrez Ollama avec: ollama serve")
        return False

def test_selenium_setup():
    """Teste la configuration Selenium"""
    print("\n🌐 Test de configuration Selenium...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get('https://www.google.com')
        title = driver.title
        driver.quit()
        
        print(f"   ✅ Selenium fonctionnel (testé sur: {title[:30]}...)")
        return True
        
    except ImportError:
        print("   ⚠️  Selenium non installé")
        print("   Installation: pip install selenium webdriver-manager")
        return False
    except Exception as e:
        print(f"   ❌ Erreur Selenium: {e}")
        print("   💡 Installez Chrome et ChromeDriver")
        return False

def create_init_files():
    """Crée les fichiers __init__.py manquants"""
    print("\n📄 Création des fichiers d'initialisation...")
    
    init_files = [
        'models/__init__.py',
        'scrapers/__init__.py'
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"   ✅ {init_file}")

def validate_config():
    """Valide la configuration complète"""
    print("\n🔍 Validation de la configuration...")
    
    try:
        from config import Config
        
        validation = Config.validate_config()
        
        if validation['valid']:
            print("   ✅ Configuration valide")
        else:
            print("   ❌ Erreurs de configuration:")
            for error in validation['errors']:
                print(f"      - {error}")
        
        if validation['warnings']:
            print("   ⚠️  Avertissements:")
            for warning in validation['warnings']:
                print(f"      - {warning}")
        
        # Afficher le résumé
        summary = Config.get_config_summary()
        print(f"\n📊 Résumé de configuration:")
        print(f"   Environment: {summary['environment']}")
        print(f"   Modèle Ollama: {summary['ollama_model']}")
        print(f"   Scraping: {'✅' if summary['scraping_enabled'] else '❌'}")
        print(f"   Scrapers: {', '.join(summary['enabled_scrapers'])}")
        print(f"   Méthode recherche: {summary['search_method']}")
        
        return validation['valid']
        
    except ImportError as e:
        print(f"   ❌ Erreur import config: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur validation: {e}")
        return False

def generate_test_script():
    """Génère un script de test complet"""
    test_script = """#!/usr/bin/env python3
# test_linkedboost.py - Script de test complet
import asyncio
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.getcwd())

async def test_full_system():
    \"\"\"Test complet du système LinkedBoost\"\"\"
    print("🚀 Test complet de LinkedBoost")
    print("=" * 50)
    
    errors = []
    
    # 1. Test de la configuration
    print("\\n1️⃣ Test de configuration...")
    try:
        from config import Config
        validation = Config.validate_config()
        if validation['valid']:
            print("   ✅ Configuration OK")
        else:
            print("   ❌ Erreurs de configuration")
            errors.extend(validation['errors'])
    except Exception as e:
        print(f"   ❌ Erreur config: {e}")
        errors.append(str(e))
    
    # 2. Test Ollama
    print("\\n2️⃣ Test Ollama...")
    try:
        from models.ai_generator import LinkedBoostAI
        ai = LinkedBoostAI()
        if ai.is_available():
            print("   ✅ Ollama connecté")
            
            # Test de génération simple
            message = ai.generate_linkedin_message(
                message_type="connection",
                recipient_name="Test User",
                context="Test de configuration"
            )
            if message:
                print("   ✅ Génération IA fonctionnelle")
            else:
                print("   ⚠️  Génération IA retourne vide")
        else:
            print("   ❌ Ollama non disponible")
            errors.append("Ollama non connecté")
    except Exception as e:
        print(f"   ❌ Erreur Ollama: {e}")
        errors.append(str(e))
    
    # 3. Test scraping
    print("\\n3️⃣ Test scraping...")
    try:
        from models.scraper import ScrapingOrchestrator
        orchestrator = ScrapingOrchestrator()
        
        if orchestrator.scrapers:
            print(f"   ✅ Scrapers disponibles: {list(orchestrator.scrapers.keys())}")
            
            # Test de scraping (limité)
            stats = await orchestrator.run_full_scrape(['wttj'])
            jobs_count = stats.get('total_jobs', 0)
            print(f"   ✅ Scraping testé: {jobs_count} offres")
            
            if stats.get('selenium_available'):
                print("   ✅ Selenium activé")
            else:
                print("   ⚠️  Mode simulation (Selenium non disponible)")
        else:
            print("   ❌ Aucun scraper disponible")
            errors.append("Pas de scrapers")
    except Exception as e:
        print(f"   ❌ Erreur scraping: {e}")
        errors.append(str(e))
    
    # 4. Test base de connaissances
    print("\\n4️⃣ Test base de connaissances...")
    try:
        from models.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        stats = kb.get_stats()
        
        print(f"   ✅ Base de données: {stats.get('total_jobs', 0)} offres")
        print(f"   ✅ Méthode recherche: {stats.get('search_method', 'unknown')}")
        
        # Test de recherche
        results = await kb.search_jobs("développeur python", limit=3)
        print(f"   ✅ Recherche testée: {len(results)} résultats")
        
    except Exception as e:
        print(f"   ❌ Erreur base de connaissances: {e}")
        errors.append(str(e))
    
    # 5. Résumé
    print("\\n" + "=" * 50)
    if not errors:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("\\n✅ LinkedBoost est prêt à être utilisé")
        print("\\n🌐 Lancez l'application avec: python app.py")
        print("📱 Interface admin: http://localhost:5000/admin")
    else:
        print("❌ ERREURS DÉTECTÉES:")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
        print("\\n💡 Consultez la documentation pour résoudre ces erreurs")
    
    return len(errors) == 0

if __name__ == "__main__":
    asyncio.run(test_full_system())
"""
    
    with open('test_linkedboost.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("   ✅ Script de test créé: test_linkedboost.py")

def create_run_script():
    """Crée un script de lancement optimisé"""
    
    # Script pour Unix/Linux/Mac
    run_script_unix = """#!/bin/bash
# run_linkedboost.sh - Script de lancement LinkedBoost

echo "🚀 Démarrage de LinkedBoost"
echo "=========================="

# Vérifier l'environnement virtuel
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Aucun environnement virtuel détecté"
    echo "💡 Recommandé: source venv/bin/activate"
fi

# Vérifier Ollama
echo "🤖 Vérification d'Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama non disponible sur localhost:11434"
    echo "💡 Démarrez Ollama avec: ollama serve"
    echo "💡 Installez le modèle: ollama pull mistral:latest"
    exit 1
else
    echo "✅ Ollama connecté"
fi

# Créer les dossiers nécessaires
mkdir -p data logs cache

# Démarrer l'application
echo "🌐 Démarrage de l'application..."
python app.py

echo "👋 LinkedBoost arrêté"
"""
    
    # Script pour Windows
    run_script_windows = """@echo off
REM run_linkedboost.bat - Script de lancement LinkedBoost pour Windows

echo 🚀 Démarrage de LinkedBoost
echo ==========================

REM Vérifier l'environnement virtuel
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  Aucun environnement virtuel détecté
    echo 💡 Recommandé: venv\\Scripts\\activate
)

REM Créer les dossiers nécessaires
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache

REM Vérifier Ollama (simple)
echo 🤖 Vérification d'Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo ❌ Ollama non disponible sur localhost:11434
    echo 💡 Démarrez Ollama avec: ollama serve
    echo 💡 Installez le modèle: ollama pull mistral:latest
    pause
    exit /b 1
) else (
    echo ✅ Ollama connecté
)

REM Démarrer l'application
echo 🌐 Démarrage de l'application...
python app.py

echo 👋 LinkedBoost arrêté
pause
"""
    
    # Créer les scripts
    with open('run_linkedboost.sh', 'w', encoding='utf-8') as f:
        f.write(run_script_unix)
    
    with open('run_linkedboost.bat', 'w', encoding='utf-8') as f:
        f.write(run_script_windows)
    
    # Rendre le script Unix exécutable
    try:
        os.chmod('run_linkedboost.sh', 0o755)
    except:
        pass
    
    print("   ✅ Scripts de lancement créés")
    print("      - run_linkedboost.sh (Unix/Linux/Mac)")
    print("      - run_linkedboost.bat (Windows)")

def create_development_helpers():
    """Crée des utilitaires pour le développement"""
    print("\n🛠️  Création des utilitaires de développement...")
    
    # Script de développement
    dev_script = """#!/usr/bin/env python3
# dev.py - Utilitaires de développement pour LinkedBoost

import os
import subprocess
import sys
import time

def run_command(cmd, description):
    \"\"\"Exécute une commande avec affichage\"\"\"
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} terminé")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur {description}: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def setup_dev_environment():
    \"\"\"Configure l'environnement de développement\"\"\"
    print("🔧 Configuration environnement de développement")
    
    # Installer les dépendances de dev
    dev_packages = [
        "black",  # Formatage code
        "flake8", # Linting
        "pytest", # Tests
        "pytest-flask", # Tests Flask
        "python-dotenv[cli]" # CLI dotenv
    ]
    
    for package in dev_packages:
        run_command(f"pip install {package}", f"Installation {package}")

def format_code():
    \"\"\"Formate le code avec Black\"\"\"
    print("🎨 Formatage du code...")
    run_command("black .", "Formatage Black")
    run_command("flake8 . --max-line-length=88 --extend-ignore=E203,W503", "Vérification Flake8")

def run_tests():
    \"\"\"Lance les tests\"\"\"
    print("🧪 Lancement des tests...")
    run_command("python test_linkedboost.py", "Tests système")
    
    if os.path.exists("tests/"):
        run_command("pytest tests/", "Tests unitaires")

def clean_project():
    \"\"\"Nettoie le projet\"\"\"
    print("🧹 Nettoyage du projet...")
    
    # Supprimer les fichiers Python compilés
    run_command("find . -name '*.pyc' -delete", "Suppression .pyc")
    run_command("find . -name '__pycache__' -type d -exec rm -rf {} +", "Suppression __pycache__")
    
    # Nettoyer les logs anciens
    if os.path.exists("logs/"):
        run_command("find logs/ -name '*.log' -mtime +7 -delete", "Nettoyage logs anciens")

def backup_data():
    \"\"\"Sauvegarde les données\"\"\"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    
    print(f"💾 Sauvegarde dans {backup_dir}...")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Sauvegarder les données importantes
    if os.path.exists("data/"):
        run_command(f"cp -r data/ {backup_dir}/", "Sauvegarde données")
    
    if os.path.exists(".env"):
        run_command(f"cp .env {backup_dir}/", "Sauvegarde configuration")

def main():
    if len(sys.argv) < 2:
        print("🔧 Utilitaires de développement LinkedBoost")
        print("Usage: python dev.py <commande>")
        print("\\nCommandes disponibles:")
        print("  setup     - Configure l'environnement de dev")
        print("  format    - Formate le code")
        print("  test      - Lance les tests")
        print("  clean     - Nettoie le projet") 
        print("  backup    - Sauvegarde les données")
        return
    
    command = sys.argv[1]
    
    if command == "setup":
        setup_dev_environment()
    elif command == "format":
        format_code()
    elif command == "test":
        run_tests()
    elif command == "clean":
        clean_project()
    elif command == "backup":
        backup_data()
    else:
        print(f"❌ Commande inconnue: {command}")

if __name__ == "__main__":
    main()
"""
    
    with open('dev.py', 'w', encoding='utf-8') as f:
        f.write(dev_script)
    
    try:
        os.chmod('dev.py', 0o755)
    except:
        pass
    
    print("   ✅ dev.py créé (utilitaires développement)")

def create_documentation():
    """Crée la documentation de base"""
    print("\n📚 Création de la documentation...")
    
    # README.md
    readme_content = """# LinkedBoost - Assistant IA pour LinkedIn

## 🎯 Description
LinkedBoost est un assistant IA complet pour optimiser votre présence LinkedIn et automatiser la génération de contenu professionnel.

## 🚀 Installation rapide
```bash
# Configuration automatique
python setup_config.py

# Installation des dépendances
pip install -r requirements.txt

# Test du système
python test_linkedboost.py

# Lancement
python app.py
```

## 🌐 Accès
- **Application principale** : http://localhost:5000
- **Interface d'administration** : http://localhost:5000/admin
- **API de statut** : http://localhost:5000/api/status

## ✨ Fonctionnalités
- 🤖 **Génération IA** de messages LinkedIn, lettres de motivation, emails
- 📊 **Analyse de profils** LinkedIn avec recommandations
- 🕷️ **Scraping automatique** d'offres d'emploi (WTTJ, Indeed, LinkedIn)
- 🔍 **Recherche sémantique** dans les offres collectées
- 📈 **Analytics marché** en temps réel
- 🎛️ **Interface d'administration** complète

## 📋 Prérequis
- Python 3.8+
- Ollama installé (`ollama serve`)
- Modèle Mistral (`ollama pull mistral:latest`)
- Chrome (pour le scraping Selenium)

## 🔧 Configuration
Voir le fichier `.env.template` pour toutes les options de configuration.

## 📖 Documentation complète
Consultez `INSTALL.md` pour le guide d'installation détaillé.

## 🆘 Support
- Tests : `python test_linkedboost.py`
- Logs : `tail -f logs/linkedboost.log`
- Configuration : `python setup_config.py`
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("   ✅ README.md créé")
    
    # .gitignore
    gitignore_content = """# LinkedBoost .gitignore

# Environnement Python
venv/
env/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Configuration sensible
.env
config_local.py

# Données et cache
data/
logs/
cache/
*.db
*.sqlite
*.sqlite3

# Selenium
geckodriver.log
chromedriver.log

# Embeddings et modèles
embeddings/
models_cache/
chroma_db/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backup
*.bak
*.backup
backup/

# Logs
*.log
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("   ✅ .gitignore créé")

def show_final_summary():
    """Affiche le résumé final avec les prochaines étapes"""
    print("\n" + "🎉" + "=" * 48 + "🎉")
    print("         CONFIGURATION LINKEDBOOST TERMINÉE")
    print("🎉" + "=" * 48 + "🎉")
    
    print("\n📁 Structure créée:")
    print("   ├── config.py                 (Configuration principale)")
    print("   ├── .env                      (Variables d'environnement)")
    print("   ├── requirements.txt          (Dépendances Python)")
    print("   ├── models/__init__.py        (Modules IA/scraping)")
    print("   ├── scrapers/__init__.py      (Modules de scraping)")
    print("   ├── data/                     (Base de données)")
    print("   ├── logs/                     (Fichiers de logs)")
    print("   ├── cache/                    (Cache application)")
    print("   └── templates/admin/          (Interface admin)")
    
    print("\n🚀 Scripts créés:")
    print("   ├── test_linkedboost.py      (Test complet du système)")
    print("   ├── run_linkedboost.sh       (Lancement Unix/Linux/Mac)")
    print("   ├── run_linkedboost.bat      (Lancement Windows)")
    print("   ├── dev.py                   (Utilitaires développement)")
    print("   ├── README.md                (Documentation principale)")
    print("   └── .gitignore               (Configuration Git)")
    
    print("\n📋 PROCHAINES ÉTAPES:")
    print("   1️⃣  pip install -r requirements.txt")
    print("   2️⃣  Éditez .env selon vos besoins")
    print("   3️⃣  python test_linkedboost.py")
    print("   4️⃣  python app.py")
    print("   5️⃣  Accédez à http://localhost:5000/admin")
    
    print("\n🔧 COMMANDES UTILES:")
    print("   • Test système:     python test_linkedboost.py")
    print("   • Validation:       python -c \"from config import Config; print(Config.validate_config())\"")
    print("   • Lancement:        ./run_linkedboost.sh (ou python app.py)")
    print("   • Développement:    python dev.py setup")
    
    print("\n🆘 EN CAS DE PROBLÈME:")
    print("   • Consultez INSTALL.md pour le guide détaillé")
    print("   • Vérifiez les logs: tail -f logs/*.log") 
    print("   • Relancez setup:   python setup_config.py")
    
    print("\n🌟 LinkedBoost est prêt à être utilisé !")
    print("   Interface admin: http://localhost:5000/admin")
    print("   Documentation:   README.md et INSTALL.md")

def main():
    """Fonction principale de configuration"""
    print("🔧 Configuration automatique de LinkedBoost")
    print("=" * 50)
    
    success = True
    
    # 1. Créer la structure
    create_directories()
    create_init_files()
    
    # 2. Configuration
    setup_env_file()
    
    # 3. Vérifications
    if not check_dependencies():
        success = False
    
    if not test_ollama_connection():
        success = False
    
    test_selenium_setup()  # Non bloquant
    
    # 4. Validation
    if not validate_config():
        success = False
    
    # 5. Scripts utilitaires
    print("\n🛠️  Création des scripts utilitaires...")
    generate_test_script()
    create_run_script()
    create_development_helpers()
    
    # 6. Documentation
    create_documentation()
    
    # 7. Résumé final
    if success:
        show_final_summary()
    else:
        print("\n⚠️  CONFIGURATION TERMINÉE AVEC DES AVERTISSEMENTS")
        print("\n🔧 Résolvez les erreurs ci-dessus puis relancez:")
        print("   python setup_config.py")

if __name__ == "__main__":
    main()