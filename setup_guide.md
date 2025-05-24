# Guide de mise en place - Flask + Ollama avec Mistral

## 📋 Prérequis

### Logiciels requis
- **Python 3.8+** installé sur votre système
- **Ollama** installé et configuré
- **Git** (optionnel, pour cloner le projet)

### Vérification d'Ollama
```bash
# Vérifier qu'Ollama est installé
ollama --version

# Démarrer Ollama (si pas déjà fait)
ollama serve

# Télécharger Mistral
ollama pull mistral:latest

# Vérifier que Mistral est disponible
ollama list
```

## 🚀 Installation rapide

### 1. Création de la structure du projet
```bash
mkdir flask-ollama-app
cd flask-ollama-app

# Création des dossiers
mkdir -p app/{routes,services,templates,static/{css,js}}
```

### 2. Environnement virtuel Python
```bash
# Création de l'environnement virtuel
python -m venv venv

# Activation (Linux/Mac)
source venv/bin/activate

# Activation (Windows)
venv\Scripts\activate
```

### 3. Installation des dépendances
```bash
# Créer le fichier requirements.txt avec le contenu fourni
pip install -r requirements.txt
```

### 4. Fichiers à créer

Créez les fichiers suivants avec le contenu fourni dans les artefacts :

**Structure finale :**
```
flask-ollama-app/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── ollama_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   └── chat.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
├── config.py
├── requirements.txt
├── run.py
├── .env
└── README.md
```

### 5. Configuration
```bash
# Créer le fichier .env
echo "FLASK_DEBUG=True
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest
SECRET_KEY=your-secret-key-change-in-production" > .env
```

## 🎯 Lancement de l'application

### Méthode 1 : Démarrage manuel
```bash
# 1. Démarrer Ollama (dans un terminal séparé)
ollama serve

# 2. Activer l'environnement virtuel
source venv/bin/activate

# 3. Démarrer Flask
python run.py
```

### Méthode 2 : Script automatisé
```bash
# Rendre le script exécutable
chmod +x start.sh

# Lancer l'application
./start.sh
```

### Méthode 3 : Docker (pour déploiement)
```bash
# Construction et démarrage avec Docker Compose
docker-compose up -d

# Vérification des logs
docker-compose logs -f
```

## 🌐 Accès à l'application

Une fois l'application démarrée, accédez à :
- **Page d'accueil** : http://localhost:5000
- **Interface de chat** : http://localhost:5000/chat
- **API de statut** : http://localhost:5000/status

## 🔧 Fonctionnalités principales

### Interface Web
- **Chat en temps réel** avec Mistral
- **Streaming des réponses** pour une expérience fluide
- **Configuration des paramètres** (température, tokens max)
- **Export des conversations** en Markdown
- **Interface responsive** adaptée mobile

### API REST
- `POST /api/generate` - Génération de réponse
- `POST /api/stream` - Génération avec streaming
- `GET /api/models` - Liste des modèles disponibles
- `GET /status` - Statut de l'application

### Exemple d'utilisation de l'API
```bash
# Test de génération simple
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Bonjour, comment allez-vous?"}'

# Test avec options personnalisées
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Expliquez-moi les bases de Python",
    "options": {
      "temperature": 0.7,
      "num_predict": 200
    }
  }'
```

## 🛠 Personnalisation

### Modification du modèle
```python
# Dans config.py
OLLAMA_MODEL = 'llama2:latest'  # Ou tout autre modèle
```

### Ajout de nouveaux modèles
```bash
# Télécharger d'autres modèles
ollama pull llama2:latest
ollama pull codellama:latest
ollama pull phi:latest
```

### Configuration avancée
```python
# Dans app/services/ollama_service.py
def generate_response(self, prompt, **kwargs):
    payload = {
        "model": self.model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": kwargs.get('temperature', 0.7),
            "top_p": kwargs.get('top_p', 0.9),
            "top_k": kwargs.get('top_k', 40),
            "num_predict": kwargs.get('num_predict', 150),
            "repeat_penalty": kwargs.get('repeat_penalty', 1.1)
        }
    }
```

## 📊 Monitoring et logs

### Vérification du statut
```bash
# Statut de l'application
curl http://localhost:5000/status

# Logs de Flask
tail -f app.log  # Si configuré

# Logs d'Ollama
ollama logs
```

### Métriques disponibles
- Statut de connexion à Ollama
- Modèles disponibles
- Temps de réponse
- Erreurs de communication

## 🐛 Dépannage

### Problèmes courants

**1. Ollama non disponible**
```bash
# Vérifier qu'Ollama fonctionne
curl http://localhost:11434/api/tags

# Redémarrer Ollama si nécessaire
pkill ollama
ollama serve
```

**2. Modèle non trouvé**
```bash
# Vérifier les modèles installés
ollama list

# Télécharger Mistral si absent
ollama pull mistral:latest
```

**3. Erreurs de dépendances Python**
```bash
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

**4. Port déjà utilisé**
```bash
# Changer le port dans run.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Logs de débogage
```python
# Activer les logs détaillés dans config.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Déploiement en production

### Configuration de production
```python
# config.py - Classe de production
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://ollama:11434')
```

### Variables d'environnement
```bash
export FLASK_ENV=production
export SECRET_KEY=your-very-secure-secret-key
export OLLAMA_BASE_URL=http://your-ollama-server:11434
```

### Serveur WSGI (Gunicorn)
```bash
# Installation
pip install gunicorn

# Démarrage
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Nginx (reverse proxy)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/stream {
        proxy_pass http://127.0.0.1:5000;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

## 🔐 Sécurité

### Bonnes pratiques
- Changez la `SECRET_KEY` en production
- Utilisez HTTPS en production
- Limitez l'accès à l'API si nécessaire
- Surveillez les logs pour détecter les abus

### Limitation de débit (optionnel)
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@limiter.limit("10 per minute")
@api_bp.route('/generate', methods=['POST'])
def generate():
    # ...
```

## 📈 Améliorations possibles

### Fonctionnalités avancées
- **Authentification utilisateur**
- **Sauvegarde des conversations** en base de données
- **Support multi-modèles** en temps réel
- **Interface d'administration**
- **Statistiques d'utilisation**
- **API de gestion des modèles**

### Optimisations
- **Cache des réponses** fréquentes
- **Pool de connexions** à Ollama
- **Compression des réponses**
- **CDN pour les assets statiques**

## 🤝 Contribution

### Structure du code
- `app/routes/` - Contrôleurs Flask
- `app/services/` - Logique métier
- `app/templates/` - Templates HTML
- `app/static/` - CSS, JS, images

### Tests
```bash
# Installer les dépendances de test
pip install pytest pytest-flask

# Lancer les tests
python -m pytest tests/
```

## 📚 Ressources

- [Documentation Ollama](https://github.com/jmorganca/ollama)
- [Documentation Flask](https://flask.palletsprojects.com/)
- [Modèles disponibles](https://ollama.ai/library)
- [Guide Mistral](https://docs.mistral.ai/)

---

**🎉 Votre application Flask + Ollama est maintenant prête !**

Démarrez avec `python run.py` et accédez à http://localhost:5000