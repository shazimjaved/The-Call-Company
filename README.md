# The Call Company

A modern Flask web application for comparing and managing mobile network plans.
![Car Price Predictor](https://github.com/shazimjaved/The-Call-Company/blob/main/tcc1.jpg)

---

## 🚀 Features

- **Browse & Compare Plans:** View all available mobile plans in a beautiful, responsive interface.
- **Smart Plan Suggestion:** Get personalized plan recommendations based on your needs.
- **Sign Up & Membership Management:** Sign up for plans, view your memberships, and see all details.
- **My Profile:** Update your username, email, and password in a secure profile area.
- **Find Membership:** Instantly look up your membership by ID.
- **Modern UI/UX:** Clean, mobile-friendly design with clear visual hierarchy.
- **Age Restrictions:** Automatic spending cap and content restrictions for users under 18.

---

## 🗂️ Project Structure

```
the_call_company/
├── app.py                # Main Flask application
├── requirements.txt      # Python dependencies
├── static/
│   └── css/
│       └── style.css     # Stylesheet
├── templates/
│   ├── layout.html       # Base layout
│   ├── index.html        # Home page
│   ├── signup.html       # Plan signup form
│   ├── confirmation.html # Signup confirmation
│   ├── find_member.html  # Find membership by ID
│   ├── member_details.html # Membership details
│   ├── my_memberships.html # All your memberships
│   ├── profile.html      # My Profile page
│   └── ...               # Other templates
├── instance/
│   └── the_call_company.db # SQLite database (auto-created)
├── README.md             # This file
└── init_db.py            # (Optional) DB initialization script
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites

- Python 3.x
- (Optional) MySQL Server (if not using SQLite)
- Virtual environment tool (`venv` recommended)

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd the_call_company
```

### 3. Create & Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize the Database

- By default, uses SQLite (no setup needed).
- To seed with sample data, run:
  ```bash
  flask seed-db
  ```

- If using MySQL, update `SQLALCHEMY_DATABASE_URI` in `app.py` and set environment variables as needed.

### 6. Run the Application

```bash
flask run
```
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 📝 Usage

- **Browse Plans:** See all plans on the home page.
- **Suggest Me the Best Plan:** Get a personalized recommendation.
- **Sign Up:** Register for a plan and manage your memberships.
- **My Profile:** Update your account details.
- **Find Membership:** Retrieve membership info by ID.

---

## 🤝 Contributing

Pull requests and suggestions are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

---

## 🆘 Support

For help, open an issue or contact the project maintainer.

---

