#!/usr/bin/env python3
# test_linkedboost.py - Script de test complet
import asyncio
import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.getcwd())

async def test_full_system():
    """Test complet du système LinkedBoost"""
    print("🚀 Test complet de LinkedBoost")
    print("=" * 50)
    
    errors = []
    
    # 1. Test de la configuration
    print("\n1️⃣ Test de configuration...")
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
    print("\n2️⃣ Test Ollama...")
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
    print("\n3️⃣ Test scraping...")
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
    print("\n4️⃣ Test base de connaissances...")
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
    print("\n" + "=" * 50)
    if not errors:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("\n✅ LinkedBoost est prêt à être utilisé")
        print("\n🌐 Lancez l'application avec: python app.py")
        print("📱 Interface admin: http://localhost:5000/admin")
    else:
        print("❌ ERREURS DÉTECTÉES:")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
        print("\n💡 Consultez la documentation pour résoudre ces erreurs")
    
    return len(errors) == 0

if __name__ == "__main__":
    asyncio.run(test_full_system())
