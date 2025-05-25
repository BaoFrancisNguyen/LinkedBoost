@echo off
REM run_linkedboost.bat - Script de lancement LinkedBoost pour Windows

echo 🚀 Démarrage de LinkedBoost
echo ==========================

REM Vérifier l'environnement virtuel
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  Aucun environnement virtuel détecté
    echo 💡 Recommandé: venv\Scripts\activate
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
