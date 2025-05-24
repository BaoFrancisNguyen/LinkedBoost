// static/js/app.js - LinkedBoost JavaScript principal

/**
 * LinkedBoost - Assistant IA pour LinkedIn
 * Fonctions JavaScript communes
 */

class LinkedBoostApp {
    constructor() {
        this.init();
    }

    init() {
        console.log('🚀 LinkedBoost initialisé');
        this.checkStatus();
        this.setupEventListeners();
        this.setupTooltips();
    }

    /**
     * Vérification du statut de l'IA
     */
    async checkStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            this.updateStatusIndicator(data.ollama_available);
            
            // Mise à jour périodique du statut
            setTimeout(() => this.checkStatus(), 30000); // Toutes les 30 secondes
            
        } catch (error) {
            console.error('Erreur lors de la vérification du statut:', error);
            this.updateStatusIndicator(false);
        }
    }

    /**
     * Met à jour l'indicateur de statut dans la navbar
     */
    updateStatusIndicator(isAvailable) {
        const indicator = document.getElementById('status-indicator');
        if (indicator) {
            if (isAvailable) {
                indicator.className = 'badge bg-success';
                indicator.innerHTML = '<i class="fas fa-circle me-1"></i>IA Connectée';
            } else {
                indicator.className = 'badge bg-danger';
                indicator.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>IA Hors ligne';
            }
        }
    }

    /**
     * Configuration des écouteurs d'événements globaux
     */
    setupEventListeners() {
        // Gestion des formulaires avec validation
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Gestion des boutons de copie
        document.addEventListener('click', this.handleButtonClick.bind(this));
        
        // Raccourcis clavier
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Auto-resize des textareas
        document.querySelectorAll('textarea').forEach(textarea => {
            this.setupAutoResize(textarea);
        });
    }

    /**
     * Gestion des soumissions de formulaire
     */
    handleFormSubmit(event) {
        const form = event.target;
        
        // Validation basique
        if (form.querySelector('[required]')) {
            const requiredFields = form.querySelectorAll('[required]');
            let hasEmptyFields = false;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    hasEmptyFields = true;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (hasEmptyFields) {
                event.preventDefault();
                this.showNotification('Veuillez remplir tous les champs obligatoires', 'warning');
                return false;
            }
        }
    }

    /**
     * Gestion des clics sur les boutons
     */
    handleButtonClick(event) {
        const button = event.target.closest('button');
        if (!button) return;
        
        // Boutons de copie
        if (button.hasAttribute('onclick') && button.getAttribute('onclick').includes('copyToClipboard')) {
            // Géré par les fonctions individuelles
            return;
        }
        
        // Autres boutons avec animations
        if (button.type === 'submit') {
            this.addButtonAnimation(button);
        }
    }

    /**
     * Raccourcis clavier
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + Entrée pour soumettre le formulaire actif
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            const activeForm = document.activeElement.closest('form');
            if (activeForm) {
                event.preventDefault();
                activeForm.dispatchEvent(new Event('submit'));
            }
        }
        
        // Échap pour nettoyer les champs
        if (event.key === 'Escape') {
            const activeElement = document.activeElement;
            if (activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'INPUT') {
                if (event.shiftKey) {
                    activeElement.value = '';
                }
            }
        }
    }

    /**
     * Auto-resize des textareas
     */
    setupAutoResize(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    }

    /**
     * Animation des boutons
     */
    addButtonAnimation(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 150);
    }

    /**
     * Configuration des tooltips Bootstrap
     */
    setupTooltips() {
        // Activer les tooltips Bootstrap si disponible
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    /**
     * Affichage de notifications
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
        `;
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getIconForType(type)} me-2"></i>
                <span>${message}</span>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-suppression
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }

    /**
     * Icônes pour les types de notification
     */
    getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * Utilitaires pour les formulaires
     */
    static resetForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            // Supprimer les classes de validation
            form.querySelectorAll('.is-invalid, .is-valid').forEach(el => {
                el.classList.remove('is-invalid', 'is-valid');
            });
        }
    }

    /**
     * Sauvegarde automatique dans le localStorage (si nécessaire)
     */
    static saveFormData(formId) {
        const form = document.getElementById(formId);
        if (form) {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            localStorage.setItem(`linkedboost_${formId}`, JSON.stringify(data));
        }
    }

    /**
     * Chargement des données sauvegardées
     */
    static loadFormData(formId) {
        const saved = localStorage.getItem(`linkedboost_${formId}`);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                const form = document.getElementById(formId);
                if (form) {
                    Object.entries(data).forEach(([key, value]) => {
                        const field = form.querySelector(`[name="${key}"]`);
                        if (field) {
                            field.value = value;
                        }
                    });
                }
            } catch (error) {
                console.error('Erreur lors du chargement des données:', error);
            }
        }
    }
}

/**
 * Fonctions utilitaires globales
 */

// Fonction de copie dans le presse-papiers (utilisée dans les templates)
window.copyToClipboard = function(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    element.select();
    element.setSelectionRange(0, 99999); // Pour mobile
    
    try {
        document.execCommand('copy');
        
        // Feedback visuel
        const button = event.target.closest('button');
        if (button) {
            const originalText = button.innerHTML;
            button.innerHTML = button.innerHTML.replace(/fa-\w+/, 'fa-check');
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        }
        
        // Notification
        if (window.linkedBoostApp) {
            window.linkedBoostApp.showNotification('Contenu copié dans le presse-papiers !', 'success', 2000);
        }
        
    } catch (err) {
        console.error('Erreur lors de la copie:', err);
        if (window.linkedBoostApp) {
            window.linkedBoostApp.showNotification('Erreur lors de la copie', 'danger', 3000);
        }
    }
};

// Validation en temps réel des emails
window.validateEmail = function(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
};

// Compteur de caractères pour les champs avec limite
window.setupCharacterCounter = function(inputId, maxLength, counterId) {
    const input = document.getElementById(inputId);
    const counter = document.getElementById(counterId);
    
    if (input && counter) {
        input.addEventListener('input', function() {
            const remaining = maxLength - this.value.length;
            counter.textContent = `${this.value.length}/${maxLength}`;
            
            if (remaining < 50) {
                counter.className = 'text-warning';
            } else if (remaining < 0) {
                counter.className = 'text-danger';
            } else {
                counter.className = 'text-muted';
            }
        });
    }
};

// Formatage automatique des noms (première lettre en majuscule)
window.formatName = function(input) {
    if (input.value) {
        input.value = input.value
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    }
};

// Nettoyage des espaces multiples
window.cleanSpaces = function(input) {
    if (input.value) {
        input.value = input.value.replace(/\s+/g, ' ').trim();
    }
};

/**
 * Initialisation de l'application
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser l'application principale
    window.linkedBoostApp = new LinkedBoostApp();
    
    // Ajouter des classes d'animation aux éléments
    const animatedElements = document.querySelectorAll('.card, .btn');
    animatedElements.forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
        el.classList.add('fade-in');
    });
    
    // Configuration des champs avec formatage automatique
    document.querySelectorAll('[data-format="name"]').forEach(input => {
        input.addEventListener('blur', () => window.formatName(input));
    });
    
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('blur', () => window.cleanSpaces(textarea));
    });
    
    console.log('✅ LinkedBoost application prête');
});