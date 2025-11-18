
cd Desktop/libprocesshider
make

chmod +x install_pcb_monitor.sh
chmod +x insterface.py
sudo apt-get install python3-tk

sudo ./install_pcb_monitor.sh
sudo ./interface.py

VERIFICATION:

cat var/run/daemon_pcb.log
cat var/log/daemon_pcb.pid


/proc/'pid_du_processus'


