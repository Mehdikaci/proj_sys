import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import os
import psutil

class ModernPCBMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB Process Monitor")
        self.root.geometry("900x700")
        self.root.configure(bg='#0f1b2d')
        
        # Configuration des styles modernes
        self.setup_styles()
        
        self.daemon_pid = None
        self.process_running = False
        
        self.setup_ui()
        self.check_daemon_status()
        
    def setup_styles(self):
        """Configure les styles modernes pour l'interface"""
        style = ttk.Style()
        
        # Couleurs modernes
        self.colors = {
            'primary': '#3b82f6',
            'secondary': '#6366f1',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'dark_bg': '#0f1b2d',
            'card_bg': '#1e293b',
            'text_light': '#f8fafc',
            'text_muted': '#94a3b8',
            'border': '#334155'
        }
        
        # Style des boutons
        style.configure('Rounded.TButton',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10),
                       relief='flat',
                       background=self.colors['primary'],
                       foreground=self.colors['text_light'],
                       font=('Segoe UI', 11, 'bold'))
        
        style.map('Rounded.TButton',
                 background=[('active', self.colors['secondary']),
                           ('disabled', '#475569')])
        
        # Style des frames
        style.configure('Card.TFrame',
                       background=self.colors['card_bg'],
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Dark.TFrame',
                       background=self.colors['dark_bg'])
        
    def create_rounded_button(self, parent, text, command, color, width=20):
        """Crée un bouton moderne avec bordures arrondies"""
        btn = tk.Button(parent,
                       text=text,
                       command=command,
                       bg=color,
                       fg=self.colors['text_light'],
                       font=('Segoe UI', 11, 'bold'),
                       width=width,
                       height=2,
                       border=0,
                       relief='flat',
                       cursor='hand2')
        
        # Effet de survol
        def on_enter(e):
            if btn['state'] == 'normal':
                # Assombrir légèrement la couleur
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                r = max(0, r - 20)
                g = max(0, g - 20)
                b = max(0, b - 20)
                darker_color = f'#{r:02x}{g:02x}{b:02x}'
                btn.config(bg=darker_color)
        
        def on_leave(e):
            if btn['state'] == 'normal':
                btn.config(bg=color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
        
    def setup_ui(self):
        # Frame principal avec fond sombre
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header avec titre
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title_label = tk.Label(header_frame,
                             text="PCB PROCESS MONITOR",
                             font=('Segoe UI', 24, 'bold'),
                             fg=self.colors['text_light'],
                             bg=self.colors['dark_bg'])
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(header_frame,
                                text="Interface de surveillance des processus système",
                                font=('Segoe UI', 12),
                                fg=self.colors['text_muted'],
                                bg=self.colors['dark_bg'])
        subtitle_label.pack()
        
        # Carte des boutons d'action
        action_card = ttk.Frame(main_frame, style='Card.TFrame', padding="25")
        action_card.pack(fill=tk.X, pady=(0, 25))
        
        # Titre de la carte d'actions
        action_title = tk.Label(action_card,
                              text="Actions du Processus",
                              font=('Segoe UI', 14, 'bold'),
                              fg=self.colors['text_light'],
                              bg=self.colors['card_bg'])
        action_title.pack(anchor='w', pady=(0, 20))
        
        # Frame pour les boutons
        button_frame = ttk.Frame(action_card, style='Card.TFrame')
        button_frame.pack(fill=tk.X)
        
        # Bouton Créer Processus
        self.btn_create = self.create_rounded_button(
            button_frame,
            "🚀 Créer le Processus",
            self.create_process,
            self.colors['success'],
            width=22
        )
        self.btn_create.pack(side=tk.LEFT, padx=(0, 15))
        
        # Bouton Stopper Processus
        self.btn_stop = self.create_rounded_button(
            button_frame,
            "Stopper le Processus",
            self.stop_process,
            self.colors['danger'],
            width=22
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 15))
        
        # Bouton Actualiser
        self.btn_refresh = self.create_rounded_button(
            button_frame,
            "Actualiser les Infos",
            self.refresh_info,
            self.colors['primary'],
            width=22
        )
        self.btn_refresh.pack(side=tk.LEFT)
        
        # Carte des informations
        info_card = ttk.Frame(main_frame, style='Card.TFrame', padding="20")
        info_card.pack(fill=tk.BOTH, expand=True)
        
        # En-tête des informations
        info_header = tk.Frame(info_card, bg=self.colors['card_bg'])
        info_header.pack(fill=tk.X, pady=(0, 15))
        
        info_title = tk.Label(info_header,
                            text="📊 Informations du PCB en Temps Réel",
                            font=('Segoe UI', 14, 'bold'),
                            fg=self.colors['text_light'],
                            bg=self.colors['card_bg'])
        info_title.pack(side=tk.LEFT)
        
        # Indicateur de statut
        self.status_indicator = tk.Label(info_header,
                                       text="●",
                                       font=('Segoe UI', 16),
                                       fg='#ef4444',
                                       bg=self.colors['card_bg'])
        self.status_indicator.pack(side=tk.RIGHT, padx=(0, 10))
        
        self.status_label = tk.Label(info_header,
                                   text="En attente...",
                                   font=('Segoe UI', 10),
                                   fg=self.colors['text_muted'],
                                   bg=self.colors['card_bg'])
        self.status_label.pack(side=tk.RIGHT)
        
        # Zone de texte avec scrollbar personnalisée
        text_frame = tk.Frame(info_card, bg=self.colors['card_bg'])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.info_text = scrolledtext.ScrolledText(
            text_frame,
            height=20,
            width=85,
            font=('Consolas', 10),
            bg='#1a2435',
            fg=self.colors['text_light'],
            insertbackground=self.colors['text_light'],
            selectbackground=self.colors['primary'],
            relief='flat',
            padx=15,
            pady=15,
            wrap=tk.WORD
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Footer avec informations système
        footer_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        footer_text = tk.Label(footer_frame,
                             text="PCB Monitor- Système de surveillance de processus",
                             font=('Segoe UI', 9),
                             fg=self.colors['text_muted'],
                             bg=self.colors['dark_bg'])
        footer_text.pack()
        
    def check_daemon_status(self):
        """Vérifie si le daemon est déjà en cours d'exécution"""
        try:
            # Vérifier le fichier PID
            if os.path.exists("/var/run/daemon_pcb.pid"):
                with open("/var/run/daemon_pcb.pid", "r") as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        self.daemon_pid = pid
                        self.process_running = True
                        self.update_buttons_state()
                        self.update_status(f"✅ Daemon actif (PID: {pid})", 'success')
                        self.refresh_info()
                        return
            
            # Chercher le processus par nom
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and ('pcb_monitor' in proc.info['name'].lower() or 
                                            any('pcb_monitor' in str(arg).lower() for arg in proc.info['cmdline'] or [])):
                        self.daemon_pid = proc.info['pid']
                        self.process_running = True
                        self.update_buttons_state()
                        self.update_status(f"Processus trouvé (PID: {self.daemon_pid})", 'success')
                        self.refresh_info()
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            print(f"Erreur lors de la vérification: {e}")
            
        self.update_status("🔍 Aucun processus actif", 'muted')
        
    def create_process(self):
        """Crée le processus daemon"""
        def run_daemon():
            try:
                # Vérifier si le binaire existe
                if not os.path.exists("/usr/local/bin/pcb_monitor"):
                    if not os.path.exists("./pcb_monitor"):
                        if os.path.exists("pcb_info.c"):
                            compile_result = subprocess.run(["gcc", "-o", "pcb_monitor", "pcb_info.c"], 
                                                          capture_output=True, text=True)
                            if compile_result.returncode != 0:
                                self.root.after(0, lambda: messagebox.showerror("Erreur", 
                                        f"Erreur de compilation:\n{compile_result.stderr}"))
                                return
                    
                    subprocess.run(["sudo", "cp", "pcb_monitor", "/usr/local/bin/"], 
                                 capture_output=True)
                
                # Démarrer le processus
                if os.path.exists("/etc/systemd/system/pcb_monitor.service"):
                    result = subprocess.run(["sudo", "systemctl", "start", "pcb_monitor.service"], 
                                          capture_output=True, text=True)
                else:
                    result = subprocess.run(["sudo", "/usr/local/bin/pcb_monitor"], 
                                          capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.root.after(0, self.on_process_created)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Erreur", 
                            f"Erreur lors du démarrage:\n{result.stderr}"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erreur", f"Exception: {str(e)}"))
        
        self.update_status("Démarrage en cours...", 'warning')
        threading.Thread(target=run_daemon, daemon=True).start()
        
    def on_process_created(self):
        """Callback lorsque le processus est créé"""
        time.sleep(3)
        self.check_daemon_status()
        self.refresh_info()
        messagebox.showinfo("Succès", "Processus daemon créé avec succès!")
            
    def stop_process(self):
        """Arrête le processus daemon"""
        if messagebox.askyesno("Confirmation", 
                             "Voulez-vous vraiment arrêter le processus?\nCette action est irréversible.",
                             icon='warning'):
            try:
                if self.daemon_pid:
                    self.update_status("Arrêt en cours...", 'warning')
                    
                    if os.path.exists("/etc/systemd/system/pcb_monitor.service"):
                        subprocess.run(["sudo", "systemctl", "stop", "pcb_monitor.service"])
                    
                    subprocess.run(["sudo", "kill", "-TERM", str(self.daemon_pid)])
                    
                    # Attendre l'arrêt
                    for _ in range(15):
                        if not psutil.pid_exists(self.daemon_pid):
                            break
                        time.sleep(0.5)
                    
                    if psutil.pid_exists(self.daemon_pid):
                        subprocess.run(["sudo", "kill", "-KILL", str(self.daemon_pid)])
                    
                    subprocess.run(["sudo", "rm", "-f", "/var/run/daemon_pcb.pid"])
                    
                    self.process_running = False
                    self.daemon_pid = None
                    self.update_buttons_state()
                    self.update_status("Processus arrêté", 'muted')
                    self.info_text.delete(1.0, tk.END)
                    messagebox.showinfo("Succès", "Processus arrêté avec succès!")
                    
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'arrêter le processus: {str(e)}")
                
    def refresh_info(self):
        """Actualise les informations du PCB"""
        if not self.daemon_pid or not psutil.pid_exists(self.daemon_pid):
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "Aucun processus actif\n\n")
            self.info_text.insert(tk.END, "Utilisez le bouton 'Créer le Processus' pour démarrer la surveillance.")
            self.process_running = False
            self.update_buttons_state()
            return
            
        try:
            self.info_text.delete(1.0, tk.END)
            
            # Style pour les titres
            self.info_text.tag_configure('title', foreground='#3b82f6', font=('Consolas', 11, 'bold'))
            self.info_text.tag_configure('subtitle', foreground='#10b981', font=('Consolas', 10, 'bold'))
            self.info_text.tag_configure('data', foreground='#f8fafc')
            self.info_text.tag_configure('muted', foreground='#94a3b8')
            
            # Informations processus
            process = psutil.Process(self.daemon_pid)
            
            self.info_text.insert(tk.END, "📋 INFORMATIONS DU PROCESSUS\n", 'title')
            self.info_text.insert(tk.END, "═" * 50 + "\n", 'muted')
            
            info_data = [
                ("PID", f"{self.daemon_pid}"),
                ("Nom", process.name()),
                ("Statut", process.status()),
                ("Parent PID", f"{process.ppid()}"),
                ("CPU", f"{process.cpu_percent():.2f}%"),
                ("Mémoire", f"{process.memory_info().rss / 1024 / 1024:.2f} MB"),
                ("Démarré le", time.ctime(process.create_time())),
                ("Utilisateur", process.username())
            ]
            
            for key, value in info_data:
                self.info_text.insert(tk.END, f"• {key:<15}", 'subtitle')
                self.info_text.insert(tk.END, f"{value}\n", 'data')
            
            # Informations détaillées depuis /proc
            proc_path = f"/proc/{self.daemon_pid}/status"
            if os.path.exists(proc_path):
                self.info_text.insert(tk.END, "\n ÉTAT DU SYSTÈME\n", 'title')
                self.info_text.insert(tk.END, "═" * 50 + "\n", 'muted')
                
                with open(proc_path, 'r') as f:
                    for line in f:
                        if any(key in line for key in ['State', 'VmSize', 'VmRSS', 'Threads']):
                            parts = line.strip().split('\t')
                            if len(parts) >= 2:
                                self.info_text.insert(tk.END, f"• {parts[0]:<12}", 'subtitle')
                                self.info_text.insert(tk.END, f"{parts[1]}\n", 'data')
            
            # Derniers logs
            if os.path.exists("/var/log/daemon_pcb.log"):
                self.info_text.insert(tk.END, "\n📝 DERNIÈRES ACTIVITÉS\n", 'title')
                self.info_text.insert(tk.END, "═" * 50 + "\n", 'muted')
                
                with open("/var/log/daemon_pcb.log", "r") as f:
                    logs = f.readlines()[-10:]  # 10 dernières lignes
                    for log in logs:
                        self.info_text.insert(tk.END, f"↳ {log}", 'muted')
            
        except Exception as e:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"❌ Erreur: {str(e)}", 'data')
            
    def update_buttons_state(self):
        """Met à jour l'état des boutons"""
        if self.process_running:
            self.btn_create.config(state=tk.DISABLED, bg='#475569')
            self.btn_stop.config(state=tk.NORMAL, bg=self.colors['danger'])
        else:
            self.btn_create.config(state=tk.NORMAL, bg=self.colors['success'])
            self.btn_stop.config(state=tk.DISABLED, bg='#475569')
            
    def update_status(self, message, status_type='muted'):
        """Met à jour le message de statut"""
        colors = {
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'muted': '#94a3b8',
            'primary': '#3b82f6'
        }
        
        self.status_label.config(text=message, fg=colors.get(status_type, '#94a3b8'))
        self.status_indicator.config(fg=colors.get(status_type, '#ef4444'))

def main():
    # Vérifier les privilèges
    if os.geteuid() != 0:
        root = tk.Tk()
        root.withdraw()
        
        if messagebox.askyesno("Privilèges requis", 
                             "🔒 Cette application nécessite des privilèges administrateur.\n\n"
                             "Voulez-vous exécuter avec sudo maintenant?",
                             icon='warning'):
            subprocess.run(["sudo", "python3", __file__])
            return
        else:
            return
    
    root = tk.Tk()
    app = ModernPCBMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
