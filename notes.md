# AI Intrusion Detection System (Flask + SQLite + Chart.js)

## Features
- Register/Login
- Add Flow Logs
- ML Prediction using Pickle model
- Save predictions into SQLite
- Dashboard Chart using Chart.js

## Step 1: Install
```bash
pip install -r requirements.txt
```

## Step 2: Train Model
```bash
python train_model.py
```

This will create:
`model/ids_model.pkl`

## Step 3: Run Flask App
```bash
python app.py
```

Open:
http://127.0.0.1:5000/

## CICIDS2017 Integration
Replace dataset path in `train_model.py` with your CICIDS2017 cleaned CSV file.
Make sure the column names match `feature_cols`.









Sample Normal Input (BENIGN)
Flow Duration = 40000
Total Fwd Packets = 80
Total Backward Packets = 70
Flow Bytes/s = 200000
Flow Packets/s = 150
Fwd Packet Length Mean = 700
Bwd Packet Length Mean = 650
Destination Port = 80
Protocol = 6


 Sample Attack Input (ATTACK)
Flow Duration = 90000
Total Fwd Packets = 300
Total Backward Packets = 50
Flow Bytes/s = 800000
Flow Packets/s = 600
Fwd Packet Length Mean = 1200
Bwd Packet Length Mean = 400
Destination Port = 23
Protocol = 6


Port 23 (Telnet) suspicious kabatti mostly ATTACK prediction osthadi.