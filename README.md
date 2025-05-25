# LinkedBoost - Assistant IA pour LinkedIn

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
