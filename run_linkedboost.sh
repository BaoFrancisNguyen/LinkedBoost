#!/bin/bash
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
