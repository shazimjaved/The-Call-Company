# Project Setup & Usage Guide

## 1. Requirements
- Python 3.10+
- pip (Python package manager)
- (Optional) Virtual environment tool (venv)

## 2. Installation Steps
1. **Clone or extract the project ZIP file.**
2. **Navigate to the project directory in terminal.**
3. **Create and activate a virtual environment (recommended):**
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Mac/Linux
   ```
4. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
5. **Seed the database:**
   ```
   flask seed-db
   ```
   (This will create and populate the database with sample data.)
6. **Run the application:**
   ```
   python app.py
   ```
7. **Open your browser and go to:**
   - http://127.0.0.1:5000/

## 3. Usage
- Register a new user account.
- Login with your credentials.
- Browse and sign up for mobile plans.
- Use "Suggest Me the Best Plan" for recommendations.
- View your memberships under "My Memberships".
- Use "Find Membership" to look up by membership ID.

## 4. Notes
- No real payment is processed; payment method is for demonstration only.
- Age restrictions and spending caps are enforced as per requirements.
- For any issues, check the terminal for error messages. 