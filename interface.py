#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCB Monitor - Interface Graphique Linux
Application GUI pour contrôler et surveiller le daemon pcb_monitor
Nécessite: Python 3, tkinter (préinstallé sur la plupart des distributions)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import os
import threading
import time
from datetime import datetime

class PCBMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB Monitor - Contrôle du Daemon")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e293b')
        
        # Variables
        self.is_running = tk.BooleanVar(value=False)
        self.auto_refresh = tk.BooleanVar(value=True)
        self.pid_file = "/var/run/daemon_pcb.pid"
        self.log_file = "/var/log/daemon_pcb.log"
        
        # Style
        self.setup_styles()
        
        # Interface
        self.create_widgets()
        
        # Vérifier le statut initial
        self.check_status()
        
        # Démarrer le rafraîchissement automatique
        self.auto_refresh_logs()
    
    def setup_styles(self):
        """Configure les styles de l'interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Boutons
        style.configure('Start.TButton', 
                       background='#22c55e',
                       foreground='white',
                       font=('Arial', 11, 'bold'),
                       padding=10)
        
        style.configure('Stop.TButton',
                       background='#ef4444',
                       foreground='white',
                       font=('Arial', 11, 'bold'),
                       padding=10)
        
        style.configure('Refresh.TButton',
                       background='#3b82f6',
                       foreground='white',
                       font=('Arial', 11, 'bold'),
                       padding=10)
        
        style.map('Start.TButton', background=[('active', '#16a34a')])
        style.map('Stop.TButton', background=[('active', '#dc2626')])
        style.map('Refresh.TButton', background=[('active', '#2563eb')])
    
    def create_widgets(self):
        """Crée tous les widgets de l'interface"""
        
        # ===== HEADER =====
        header = tk.Frame(self.root, bg='#0f172a', height=80)
        header.pack(fill='x', padx=0, pady=0)
        
        title_label = tk.Label(header, 
                              text="🖥️ PCB MONITOR",
                              font=('Arial', 24, 'bold'),
                              bg='#0f172a',
                              fg='#38bdf8')
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(header,
                                 text="Interface de Contrôle et Surveillance du Daemon",
                                 font=('Arial', 10),
                                 bg='#0f172a',
                                 fg='#94a3b8')
        subtitle_label.pack()
        
        # ===== STATUT =====
        status_frame = tk.Frame(self.root, bg='#1e293b')
        status_frame.pack(fill='x', padx=20, pady=10)
        
        self.status_label = tk.Label(status_frame,
                                    text="● STATUT: ARRÊTÉ",
                                    font=('Arial', 14, 'bold'),
                                    bg='#1e293b',
                                    fg='#ef4444')
        self.status_label.pack(side='left')
        
        # ===== CONTRÔLES =====
        control_frame = tk.Frame(self.root, bg='#1e293b')
        control_frame.pack(fill='x', padx=20, pady=10)
        
        self.start_btn = ttk.Button(control_frame,
                                    text="▶ Démarrer",
                                    style='Start.TButton',
                                    command=self.start_daemon)
        self.start_btn.pack(side='left', padx=5, ipadx=20)
        
        self.stop_btn = ttk.Button(control_frame,
                                   text="■ Arrêter",
                                   style='Stop.TButton',
                                   command=self.stop_daemon,
                                   state='disabled')
        self.stop_btn.pack(side='left', padx=5, ipadx=20)
        
        refresh_btn = ttk.Button(control_frame,
                                text="🔄 Rafraîchir",
                                style='Refresh.TButton',
                                command=self.refresh_info)
        refresh_btn.pack(side='left', padx=5, ipadx=20)
        
        auto_refresh_cb = tk.Checkbutton(control_frame,
                                        text="Rafraîchir auto",
                                        variable=self.auto_refresh,
                                        bg='#1e293b',
                                        fg='white',
                                        selectcolor='#334155',
                                        font=('Arial', 10))
        auto_refresh_cb.pack(side='right', padx=10)
        
        # ===== CONTENEUR PRINCIPAL =====
        main_container = tk.Frame(self.root, bg='#1e293b')
        main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # ===== ATTRIBUTS PCB (Gauche) =====
        pcb_frame = tk.LabelFrame(main_container,
                                 text=" 📊 Attributs du PCB ",
                                 font=('Arial', 12, 'bold'),
                                 bg='#334155',
                                 fg='#38bdf8',
                                 relief='raised',
                                 bd=2)
        pcb_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Zone d'affichage des attributs
        self.pcb_text = scrolledtext.ScrolledText(pcb_frame,
                                                  width=40,
                                                  height=20,
                                                  font=('Courier', 10),
                                                  bg='#1e293b',
                                                  fg='#e2e8f0',
                                                  insertbackground='white',
                                                  relief='flat',
                                                  padx=10,
                                                  pady=10)
        self.pcb_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.pcb_text.insert('1.0', "Aucun processus actif\n\nDémarrez le daemon pour voir les informations")
        self.pcb_text.config(state='disabled')
        
        # ===== LOGS (Droite) =====
        logs_frame = tk.LabelFrame(main_container,
                                  text=" 📝 Logs en Temps Réel ",
                                  font=('Arial', 12, 'bold'),
                                  bg='#334155',
                                  fg='#22c55e',
                                  relief='raised',
                                  bd=2)
        logs_frame.pack(side='right', fill='both', expand=True)
        
        # Zone d'affichage des logs
        self.logs_text = scrolledtext.ScrolledText(logs_frame,
                                                   width=50,
                                                   height=20,
                                                   font=('Courier', 9),
                                                   bg='#0f172a',
                                                   fg='#22c55e',
                                                   insertbackground='white',
                                                   relief='flat',
                                                   padx=10,
                                                   pady=10)
        self.logs_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ===== FOOTER =====
        footer = tk.Frame(self.root, bg='#0f172a', height=40)
        footer.pack(fill='x', side='bottom')
        
        footer_label = tk.Label(footer,
                               text=f"📁 PID: {self.pid_file} | 📄 LOG: {self.log_file}",
                               font=('Courier', 9),
                               bg='#0f172a',
                               fg='#64748b')
        footer_label.pack(pady=10)
    
    def run_command(self, command, use_sudo=False):
        """Exécute une commande système"""
        try:
            if use_sudo:
                # Pour les commandes sudo, utiliser pkexec ou gksudo
                cmd = ['pkexec'] + command.split()
            else:
                cmd = command.split()
            
            result = subprocess.run(cmd, 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=10)
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def check_status(self):
        """Vérifie si le daemon est en cours d'exécution"""
        try:
            # Méthode 1: Vérifier via systemctl
            code, out, err = self.run_command("systemctl is-active pcb_monitor.service")
            
            if code == 0 and "active" in out:
                self.is_running.set(True)
                self.update_status_display(True)
                return True
            
            # Méthode 2: Vérifier le fichier PID
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    pid = f.read().strip()
                    
                # Vérifier si le processus existe
                try:
                    os.kill(int(pid), 0)
                    self.is_running.set(True)
                    self.update_status_display(True)
                    return True
                except:
                    pass
            
            self.is_running.set(False)
            self.update_status_display(False)
            return False
            
        except Exception as e:
            self.add_log(f"Erreur lors de la vérification: {e}", "ERROR")
            return False
    
    def update_status_display(self, running):
        """Met à jour l'affichage du statut"""
        if running:
            self.status_label.config(text="● STATUT: EN COURS D'EXÉCUTION",
                                   fg='#22c55e')
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
        else:
            self.status_label.config(text="● STATUT: ARRÊTÉ",
                                   fg='#ef4444')
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def start_daemon(self):
        """Démarre le daemon"""
        def start_thread():
            self.add_log("Démarrage du daemon...", "INFO")
            
            # Essayer avec systemctl
            code, out, err = self.run_command("systemctl start pcb_monitor.service", use_sudo=True)
            
            if code == 0:
                self.add_log("✓ Daemon démarré avec succès (systemd)", "SUCCESS")
                time.sleep(1)
                self.check_status()
                self.load_pcb_info()
            else:
                # Essayer en mode manuel
                self.add_log("Tentative de démarrage manuel...", "INFO")
                code, out, err = self.run_command("/usr/local/bin/pcb_monitor", use_sudo=True)
                
                if code == 0:
                    self.add_log("✓ Daemon démarré avec succès (manuel)", "SUCCESS")
                    time.sleep(1)
                    self.check_status()
                    self.load_pcb_info()
                else:
                    self.add_log(f"✗ Échec du démarrage: {err}", "ERROR")
                    messagebox.showerror("Erreur", f"Impossible de démarrer le daemon:\n{err}")
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_daemon(self):
        """Arrête le daemon"""
        def stop_thread():
            self.add_log("Arrêt du daemon...", "INFO")
            
            code, out, err = self.run_command("systemctl stop pcb_monitor.service", use_sudo=True)
            
            if code == 0:
                self.add_log("✓ Daemon arrêté avec succès", "SUCCESS")
                time.sleep(1)
                self.check_status()
                self.clear_pcb_info()
            else:
                self.add_log(f"✗ Échec de l'arrêt: {err}", "ERROR")
                messagebox.showerror("Erreur", f"Impossible d'arrêter le daemon:\n{err}")
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def refresh_info(self):
        """Rafraîchit toutes les informations"""
        self.check_status()
        if self.is_running.get():
            self.load_pcb_info()
        self.load_logs()
    
    def load_pcb_info(self):
        """Charge les informations du PCB"""
        try:
            if not os.path.exists(self.pid_file):
                return
            
            with open(self.pid_file, 'r') as f:
                pid = f.read().strip()
            
            # Lire les informations depuis /proc
            status_file = f"/proc/{pid}/status"
            
            if not os.path.exists(status_file):
                self.add_log(f"Processus {pid} non trouvé", "WARN")
                return
            
            info = {}
            with open(status_file, 'r') as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
            
            # Formater l'affichage
            self.pcb_text.config(state='normal')
            self.pcb_text.delete('1.0', tk.END)
            
            output = "╔════════════════════════════════════════╗\n"
            output += "║     ATTRIBUTS DU PCB (DAEMON)          ║\n"
            output += "╚════════════════════════════════════════╝\n\n"
            
            output += f"🆔 PID:              {pid}\n"
            output += f"👤 Nom:              {info.get('Name', 'N/A')}\n"
            output += f"⚡ État:             {info.get('State', 'N/A')}\n"
            output += f"👥 PPID:             {info.get('PPid', 'N/A')}\n"
            output += f"🔐 UID:              {info.get('Uid', 'N/A').split()[0]}\n"
            output += f"🔐 GID:              {info.get('Gid', 'N/A').split()[0]}\n"
            output += f"🧵 Threads:          {info.get('Threads', 'N/A')}\n"
            output += f"💾 VmSize:           {info.get('VmSize', 'N/A')}\n"
            output += f"💾 VmRSS:            {info.get('VmRSS', 'N/A')}\n"
            output += f"🔄 Context Switches: {info.get('voluntary_ctxt_switches', 'N/A')}\n"
            
            # Lire la priorité
            try:
                stat_file = f"/proc/{pid}/stat"
                with open(stat_file, 'r') as f:
                    stat = f.read().split()
                    priority = stat[17] if len(stat) > 17 else 'N/A'
                    output += f"⚖️  Priorité:         {priority}\n"
            except:
                pass
            
            output += f"\n📅 Mise à jour:      {datetime.now().strftime('%H:%M:%S')}\n"
            
            self.pcb_text.insert('1.0', output)
            self.pcb_text.config(state='disabled')
            
            self.add_log(f"Informations du processus {pid} chargées", "INFO")
            
        except Exception as e:
            self.add_log(f"Erreur lors du chargement des infos: {e}", "ERROR")
    
    def clear_pcb_info(self):
        """Efface les informations du PCB"""
        self.pcb_text.config(state='normal')
        self.pcb_text.delete('1.0', tk.END)
        self.pcb_text.insert('1.0', "Aucun processus actif\n\nDémarrez le daemon pour voir les informations")
        self.pcb_text.config(state='disabled')
    
    def load_logs(self):
        """Charge les derniers logs"""
        try:
            if not os.path.exists(self.log_file):
                self.logs_text.insert(tk.END, f"Fichier de log non trouvé: {self.log_file}\n")
                return
            
            # Lire les 50 dernières lignes
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                last_lines = lines[-50:] if len(lines) > 50 else lines
            
            self.logs_text.delete('1.0', tk.END)
            for line in last_lines:
                self.logs_text.insert(tk.END, line)
            
            # Scroll vers le bas
            self.logs_text.see(tk.END)
            
        except Exception as e:
            self.add_log(f"Erreur lecture logs: {e}", "ERROR")
    
    def add_log(self, message, level="INFO"):
        """Ajoute un message dans les logs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
    
    def auto_refresh_logs(self):
        """Rafraîchit automatiquement les logs"""
        if self.auto_refresh.get() and self.is_running.get():
            self.load_logs()
            if self.is_running.get():
                self.load_pcb_info()
        
        # Rappeler cette fonction après 5 secondes
        self.root.after(5000, self.auto_refresh_logs)

def main():
    root = tk.Tk()
    app = PCBMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
