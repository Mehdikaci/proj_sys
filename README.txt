
cd Desktop/libprocesshider
make

chmod +x install_pcb_monitor.sh
sudo ./install_pcb_monitor.sh

VERIFICATION:
cd /tmp/
cat daemon_pcb.log
cat daemon_pcb.pid

cd /usr/local/lib
ls // trouver libprocesshider.so

/proc/'pid_du_processus'


