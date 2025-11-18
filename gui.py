import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import os
import psutil

class PCBMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB Process Monitor")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        self.daemon_pid = None
        self.process_running = False
        
        self.setup_ui()
        self.check_daemon_status()
        
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        title_label = tk.Label(main_frame, text="🎯 PCB PROCESS MONITOR", 
                              font=('Arial', 16, 'bold'), 
                              fg='#ecf0f1', bg='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame des boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Bouton Créer Processus
        self.btn_create = tk.Button(button_frame, text="🚀 Créer Processus", 
                                   command=self.create_process,
                                   font=('Arial', 12), 
                                   bg='#27ae60', fg='white',
                                   width=15, height=2)
        self.btn_create.grid(row=0, column=0, padx=10)
        
        # Bouton Cacher Infos
        self.btn_hide = tk.Button(button_frame, text="👁️ Cacher Infos", 
                                 command=self.hide_process,
                                 font=('Arial', 12),
                                 bg='#f39c12', fg='white',
                                 width=15, height=2,
                                 state=tk.DISABLED)
        self.btn_hide.grid(row=0, column=1, padx=10)
        
        # Bouton Stopper Processus
        self.btn_stop = tk.Button(button_frame, text="⏹️ Stopper Processus", 
                                 command=self.stop_process,
                                 font=('Arial', 12),
                                 bg='#e74c3c', fg='white',
                                 width=15, height=2,
                                 state=tk.DISABLED)
        self.btn_stop.grid(row=0, column=2, padx=10)
        
        # Frame d'information
        info_frame = ttk.LabelFrame(main_frame, text="📊 Informations du PCB", padding="10")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Zone de texte pour les informations
        self.info_text = scrolledtext.ScrolledText(info_frame, 
                                                  height=15, 
                                                  width=80,
                                                  font=('Courier', 10))
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Frame du statut
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Label de statut
        self.status_label = tk.Label(status_frame, 
                                    text="🔍 En attente de démarrage...", 
                                    font=('Arial', 10), 
                                    fg='#bdc3c7', bg='#2c3e50')
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Bouton Actualiser
        self.btn_refresh = tk.Button(status_frame, text="🔄 Actualiser", 
                                    command=self.refresh_info,
                                    font=('Arial', 10),
                                    bg='#3498db', fg='white')
        self.btn_refresh.grid(row=0, column=1, padx=10)
        
        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        status_frame.columnconfigure(0, weight=1)
        
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
                        self.update_status(f"✅ Daemon actif (PID: {pid})")
                        self.refresh_info()
                        return
        except:
            pass
            
        self.update_status("🔍 Aucun daemon actif")
        
    def create_process(self):
        """Crée le processus daemon"""
        def run_daemon():
            try:
                # Compiler le programme C si nécessaire
                if not os.path.exists("./pcb_monitor"):
                    compile_result = subprocess.run(["gcc", "-o", "pcb_monitor", "pcb_monitor.c"], 
                                                  capture_output=True, text=True)
                    if compile_result.returncode != 0:
                        self.root.after(0, lambda: messagebox.showerror("Erreur", 
                                f"Erreur de compilation:\n{compile_result.stderr}"))
                        return
                
                # Exécuter le daemon
                result = subprocess.run(["./pcb_monitor"], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.root.after(0, self.on_process_created)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Erreur", 
                            f"Erreur lors du démarrage:\n{result.stderr}"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erreur", f"Exception: {str(e)}"))
        
        self.update_status("🔄 Démarrage du daemon...")
        threading.Thread(target=run_daemon, daemon=True).start()
        
    def on_process_created(self):
        """Callback lorsque le processus est créé"""
        # Attendre un peu que le daemon s'initialise
        time.sleep(2)
        self.check_daemon_status()
        self.refresh_info()
        messagebox.showinfo("Succès", "Processus daemon créé avec succès!")
        
    def hide_process(self):
        """Cache les informations du processus"""
        try:
            if self.daemon_pid:
                # Utiliser prctl pour changer le nom du processus (caché)
                subprocess.run(["prctl", "--pid", str(self.daemon_pid), "--name=hidden_process"])
                
                # Alternative: utiliser mount --bind pour cacher /proc/pid
                subprocess.run(["mount", "--bind", "/dev/null", f"/proc/{self.daemon_pid}"], 
                             capture_output=True)
                
                self.update_status("👁️ Processus caché")
                self.refresh_info()
                messagebox.showinfo("Succès", "Informations du processus cachées!")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de cacher le processus: {str(e)}")
            
    def stop_process(self):
        """Arrête le processus daemon"""
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment arrêter le processus?"):
            try:
                if self.daemon_pid:
                    # Envoyer le signal SIGTERM
                    subprocess.run(["kill", "-TERM", str(self.daemon_pid)])
                    
                    # Attendre la fin du processus
                    for _ in range(10):
                        if not psutil.pid_exists(self.daemon_pid):
                            break
                        time.sleep(0.5)
                    
                    # Forcer l'arrêt si nécessaire
                    if psutil.pid_exists(self.daemon_pid):
                        subprocess.run(["kill", "-KILL", str(self.daemon_pid)])
                    
                    self.process_running = False
                    self.daemon_pid = None
                    self.update_buttons_state()
                    self.update_status("⏹️ Processus arrêté")
                    self.info_text.delete(1.0, tk.END)
                    messagebox.showinfo("Succès", "Processus arrêté avec succès!")
                    
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'arrêter le processus: {str(e)}")
                
    def refresh_info(self):
        """Actualise les informations du PCB"""
        if not self.daemon_pid or not psutil.pid_exists(self.daemon_pid):
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "Aucun processus actif")
            self.process_running = False
            self.update_buttons_state()
            return
            
        try:
            # Lire le fichier de log pour les informations
            if os.path.exists("/var/log/daemon_pcb.log"):
                with open("/var/log/daemon_pcb.log", "r") as f:
                    logs = f.readlines()
                    # Prendre les 50 dernières lignes
                    recent_logs = logs[-50:] if len(logs) > 50 else logs
                    log_content = "".join(recent_logs)
                    
                    self.info_text.delete(1.0, tk.END)
                    self.info_text.insert(tk.END, log_content)
            
            # Informations système supplémentaires
            process = psutil.Process(self.daemon_pid)
            info = f"\n\n=== INFORMATIONS SYSTÈME (PID: {self.daemon_pid}) ===\n"
            info += f"Nom: {process.name()}\n"
            info += f"Statut: {process.status()}\n"
            info += f"Utilisation CPU: {process.cpu_percent():.2f}%\n"
            info += f"Utilisation Mémoire: {process.memory_info().rss / 1024 / 1024:.2f} MB\n"
            info += f"Temps de création: {time.ctime(process.create_time())}\n"
            
            self.info_text.insert(tk.END, info)
            
        except Exception as e:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Erreur lors de la lecture des informations: {str(e)}")
            
    def update_buttons_state(self):
        """Met à jour l'état des boutons"""
        if self.process_running:
            self.btn_create.config(state=tk.DISABLED, bg='#95a5a6')
            self.btn_hide.config(state=tk.NORMAL, bg='#f39c12')
            self.btn_stop.config(state=tk.NORMAL, bg='#e74c3c')
        else:
            self.btn_create.config(state=tk.NORMAL, bg='#27ae60')
            self.btn_hide.config(state=tk.DISABLED, bg='#95a5a6')
            self.btn_stop.config(state=tk.DISABLED, bg='#95a5a6')
            
    def update_status(self, message):
        """Met à jour le message de statut"""
        self.status_label.config(text=message)

def main():
    # Vérifier les privilèges
    if os.geteuid() != 0:
        print("⚠️  Attention: Cette application nécessite des privilèges root")
        print("Veuillez exécuter avec: sudo python3 pcb_gui.py")
        
        if not messagebox.askyesno("Privilèges requis", 
                                 "Cette application nécessite des privilèges root.\n"
                                 "Voulez-vous continuer quand même?"):
            return
    
    root = tk.Tk()
    app = PCBMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()