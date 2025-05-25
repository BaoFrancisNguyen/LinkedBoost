# models/__init__.py
"""
LinkedBoost Models Package
Module contenant les modèles et la logique métier de LinkedBoost
"""

__version__ = "1.0.0"
__author__ = "LinkedBoost Team"

# Exports disponibles (imports paresseux pour éviter les erreurs)
__all__ = [
    'LinkedBoostAI',
    'KnowledgeBase', 
    'SimpleSearchEngine'
]

# Les imports réels se feront lors de l'utilisation
# Cela évite les erreurs d'import circulaire