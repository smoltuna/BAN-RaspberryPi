sudo service dbus start
sudo service bluetooth start
p=$(find /usr/local/lib -name bluepy-helper)
sudo setcap cap_net_raw+e  "$p"
sudo setcap cap_net_admin+eip  "$p"
python -m streamlit run Homepage.py
