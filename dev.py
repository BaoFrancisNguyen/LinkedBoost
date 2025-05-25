#!/usr/bin/env python3
# dev.py - Utilitaires de développement pour LinkedBoost

import os
import subprocess
import sys
import time

def run_command(cmd, description):
    """Exécute une commande avec affichage"""
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
    """Configure l'environnement de développement"""
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
    """Formate le code avec Black"""
    print("🎨 Formatage du code...")
    run_command("black .", "Formatage Black")
    run_command("flake8 . --max-line-length=88 --extend-ignore=E203,W503", "Vérification Flake8")

def run_tests():
    """Lance les tests"""
    print("🧪 Lancement des tests...")
    run_command("python test_linkedboost.py", "Tests système")
    
    if os.path.exists("tests/"):
        run_command("pytest tests/", "Tests unitaires")

def clean_project():
    """Nettoie le projet"""
    print("🧹 Nettoyage du projet...")
    
    # Supprimer les fichiers Python compilés
    run_command("find . -name '*.pyc' -delete", "Suppression .pyc")
    run_command("find . -name '__pycache__' -type d -exec rm -rf {} +", "Suppression __pycache__")
    
    # Nettoyer les logs anciens
    if os.path.exists("logs/"):
        run_command("find logs/ -name '*.log' -mtime +7 -delete", "Nettoyage logs anciens")

def backup_data():
    """Sauvegarde les données"""
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
        print("\nCommandes disponibles:")
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
