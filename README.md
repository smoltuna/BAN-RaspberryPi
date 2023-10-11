# Wearable and Camera integration

## To deploy the streamlit webapp

### First step: install dependencies:
```
pip3 install -r requirements.txt
```
### Second step: give bluetooth permissions:
```
 sudo setcap cap_net_raw+e  <PATH>/bluepy-helper
 sudo setcap cap_net_admin+eip  <PATH>/bluepy-helper
  ```
### To find bluepy-helper file, use:
```
find /usr/local/lib -name bluepy-helper
```

### Third step deploy:
```
python3 -m streamlit run Homepage.py
```
