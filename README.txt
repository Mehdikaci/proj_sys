mkdir Desktop/libprocesshider
//mettre pcb_info.c et processhider.c et Makefile dans ce dossier
cd Desktop/libprocesshider
make
gcc -o pcb_info pcb_info.c
./pcb_info

VERIFICATION:
cd /tmp/
cat daemon_pcb.log
cat daemon_pcb.pid

cd /usr/local/lib
ls // trouver libprocesshider.so

/proc/'pid_du_processus'


