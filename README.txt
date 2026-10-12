BLOOD BANK INVENTORY MANAGEMENT SYSTEM
Priority Queue by Expiry Date

REQUIREMENTS
- Python 3.9 or newer
- Flask

HOW TO RUN ON WINDOWS
1. Extract the project folder.
2. Open Command Prompt in the blood_bank_inventory folder.
3. Install Flask:
   py -m pip install -r requirements.txt
4. Start the website:
   py app.py
5. Open this address in your browser:
   http://127.0.0.1:5000

FEATURES
- Dashboard with available and expired unit counts
- Add blood units with unique unit IDs, blood group, and expiry date
- View inventory sorted by expiry date
- Issue one eligible unit for a selected blood group
- Uses Python heapq as a min-heap priority queue
- Saves inventory in a local SQLite database file named blood_bank.db

IMPORTANT
This is an educational data structures project, not a real blood-bank clinical system.
It only models the requested blood group and expiry-date rule. Real blood transfusion
requires compatibility testing, screening, and qualified medical procedures.
