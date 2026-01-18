# CS-303: Software Engineering Assignment 1

## Smart Parking System

A web-based system to manage parking slots for users and ground admins.

## How to Run

1. Clone the repository

```bash
git clone https://github.com/CodingGirlGargi/SE_Assignment1_Smart_Parking_System_Group8.git
```

2. Create a virtual environment in python.

```bash
python -m venv venv
```
```bash
# Activate on Windows:
venv\Scripts\activate
```
```bash
# Activate on Unix/MacOS:
source venv/bin/activate
```

3. Install the requirements:

```bash
pip install -r requirements.txt
```

3. Run the application:
   Navigate to the project directory and run:

```bash
python app.py
```

4. Access the system at http://127.0.0.1:5000

## Note

1. Supabase connection will not work on Institute Wifi. Connect to your personal Hotspot.
2. The user license number should follow the pattern: 2 alphabets followed by 13 numeric digits
3. The ground admin credentials are fixed as follows:

| admin_id | admin_name          | admin_password      | ground_id |
| -------: | ------------------- | ------------------- | --------: |
|      512 | adminMandiMela      | adminMandiMela      |       200 |
|      513 | adminShimlaChurch   | adminShimlaChurch   |       205 |
|      514 | adminMandiTemple    | adminMandiTemple    |       201 |
|      515 | adminShimlaTownHall | adminShimlaTownHall |       206 |
|      516 | adminHydCyberCity   | adminHydCyberCity   |       400 |
|      517 | adminHydGurudwara   | adminHydGurudwara   |       401 |
|      518 | adminWarangalRT     | adminWarangalRT     |       405 |

