#!/bin/bash

# Script d'installation automatique de PCB Monitor
# Usage: sudo ./install_pcb_monitor.sh

set -e

echo "🚀 INSTALLATION DE PCB MONITOR"
echo "═══════════════════════════════════════════════"

# Vérifier les droits root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté en tant que root (sudo)"
    exit 1
fi

# Étape 2: Copie de l'exécutable
echo ""
echo "📁 Étape 2: Installation de l'exécutable..."
cp pcb_monitor /usr/local/bin/
chmod 755 /usr/local/bin/pcb_monitor
echo "✅ Exécutable installé dans /usr/local/bin/"


echo ""
echo "⚙️  Étape 5: Configuration du service systemd..."
if [ ! -f "pcb_monitor.service" ]; then
    echo "❌ Erreur: pcb_monitor.service non trouvé"
    exit 1
fi

cp pcb_monitor.service /etc/systemd/system/
chmod 644 /etc/systemd/system/pcb_monitor.service
echo "✅ Service copié dans /etc/systemd/system/"

# Étape 6: Activation du service
echo ""
echo "🔄 Étape 6: Activation du service..."
systemctl daemon-reload
systemctl enable pcb_monitor.service
echo "✅ Service activé pour le démarrage automatique"

# Étape 7: Démarrage du service
echo ""
echo "▶️  Étape 7: Démarrage du service..."
systemctl start pcb_monitor.service
sleep 2

# Vérification du statut
echo ""
echo "🔍 Vérification du statut..."
if systemctl is-active --quiet pcb_monitor.service; then
    echo "✅ Le service PCB Monitor est actif!"
    
    # Afficher le PID
    if [ -f "/var/run/daemon_pcb.pid" ]; then
        PID=$(cat /var/run/daemon_pcb.pid)
        echo "📌 PID du daemon: $PID"
    fi
else
    echo "❌ Le service n'a pas démarré correctement"
    echo "Consultez les logs avec: journalctl -u pcb_monitor.service -n 50"
    exit 1
fi

# Résumé
echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║     INSTALLATION TERMINÉE AVEC SUCCÈS! ✅      ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "📋 COMMANDES UTILES:"
echo "  • Voir le statut:    systemctl status pcb_monitor"
echo "  • Arrêter:           systemctl stop pcb_monitor"
echo "  • Redémarrer:        systemctl restart pcb_monitor"
echo "  • Voir les logs:     journalctl -u pcb_monitor -f"
echo "  • Logs daemon:       tail -f /var/log/daemon_pcb.log"
echo "  • Désactiver démarrage: systemctl disable pcb_monitor"
echo ""
echo "Le daemon démarrera automatiquement à chaque redémarrage! 🎉"
echo ""
