import os
import random
import string
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
import click
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_secure_secret_key')

# Database Configuration - Using SQLite for easier setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///the_call_company.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---
class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    plans = db.relationship('Plan', backref='provider', lazy=True)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('provider.id'), nullable=False)
    plan_name = db.Column(db.String(100), nullable=False)
    data = db.Column(db.String(50))
    calls_text = db.Column(db.String(50))
    phone_model = db.Column(db.String(100))
    price_per_month = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    members = db.relationship('Member', backref='user', lazy=True)

class Member(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    spending_cap = db.Column(db.Boolean, default=False)
    age_restricted_content = db.Column(db.Boolean, default=False)
    payment_method = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Link to User
    plan = db.relationship('Plan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- Helper Functions ---
def generate_membership_id():
    while True:
        new_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Member.query.get(new_id):
            return new_id

# --- Routes ---
@app.route('/')
def index():
    plans = Plan.query.order_by(Plan.provider_id, Plan.price_per_month).all()
    return render_template('index.html', plans=plans)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            # Clear any existing session
            session.pop('user_id', None)
            session.pop('username', None)
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/signup/<int:plan_id>', methods=['GET', 'POST'])
def signup(plan_id):
    if 'user_id' not in session:
        flash('Please log in to sign up for a plan.', 'warning')
        return redirect(url_for('login'))
    
    plan = Plan.query.get_or_404(plan_id)
    if request.method == 'POST':
        full_name = request.form['full_name']
        date_of_birth_str = request.form['date_of_birth']
        date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
        payment_method = request.form.get('payment_method')
        user_id = session['user_id']

        # Age calculation
        today = datetime.today().date()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

        # Check if user is under 16
        if age < 16:
            flash('Sorry, you must be at least 16 years old to sign up.', 'danger')
            return render_template('signup.html', plan=plan)

        # Create new member
        new_member = Member(
            id=generate_membership_id(),
            full_name=full_name,
            date_of_birth=date_of_birth,
            plan_id=plan.id,
            payment_method=payment_method,
            user_id=user_id
        )

        # Apply restrictions for under 18s
        if age < 18:
            new_member.spending_cap = (plan.price_per_month > 15)
            new_member.age_restricted_content = True
            if plan.price_per_month > 15:
                flash(f'As you are under 18, a £15 spending cap has been applied to this plan.', 'info')

        db.session.add(new_member)
        db.session.commit()
        flash('Sign-up successful!', 'success')
        return redirect(url_for('confirmation', member_id=new_member.id))

    return render_template('signup.html', plan=plan)

@app.route('/confirmation/<member_id>')
def confirmation(member_id):
    member = Member.query.get_or_404(member_id)
    return render_template('confirmation.html', member=member)

@app.route('/member', methods=['GET', 'POST'])
def find_member():
    if request.method == 'POST':
        member_id = request.form['member_id']
        member = Member.query.get(member_id)
        if member:
            return redirect(url_for('member_details', member_id=member.id))
        else:
            flash('Membership ID not found.', 'danger')
            return redirect(url_for('find_member'))
    return render_template('find_member.html')

@app.route('/member/<member_id>')
def member_details(member_id):
    member = Member.query.get(member_id)
    return render_template('member_details.html', member=member)

@app.route('/suggest', methods=['GET', 'POST'])
def suggest():
    suggested_plan = None
    if request.method == 'POST':
        data_needed = request.form.get('data_needed')
        calls_needed = request.form.get('calls_needed')
        phone_model = request.form.get('phone_model')
        age = request.form.get('age')
        keyword = request.form.get('keyword', '').strip()

        query = Plan.query
        requirements = []

        # Keyword search logic
        if keyword:
            keyword_like = f"%{keyword.lower()}%"
            query = query.filter(
                db.or_(
                    db.func.lower(Plan.provider.has(Provider.name)).ilike(keyword_like),
                    db.func.lower(Plan.plan_name).ilike(keyword_like),
                    db.func.lower(Plan.data).ilike(keyword_like),
                    db.func.lower(Plan.calls_text).ilike(keyword_like),
                    db.func.lower(Plan.phone_model).ilike(keyword_like),
                    db.cast(Plan.price_per_month, db.String).ilike(keyword_like)
                )
            )
            requirements.append(f'keyword "{keyword}"')

        # Personalized suggestion logic
        if data_needed:
            try:
                data_needed_num = float(data_needed)
                requirements.append(f"{data_needed_num}GB data")
                query = query.filter(
                    db.or_(
                        Plan.data.ilike('%unl%'),
                        db.cast(db.func.replace(Plan.data, ' GB', ''), db.Float) >= data_needed_num
                    )
                )
            except ValueError:
                pass
        if calls_needed:
            requirements.append(f"{calls_needed} calls/texts")
            query = query.filter(Plan.calls_text.ilike(f"%{calls_needed}%"))
        if phone_model:
            requirements.append(f"{phone_model} phone")
            query = query.filter(Plan.phone_model.ilike(f"%{phone_model}%"))
        if age:
            try:
                age = int(age)
                if age < 18:
                    requirements.append("age-appropriate pricing")
                    query = query.filter(Plan.price_per_month <= 15)
            except ValueError:
                pass

        suggested_plan = query.order_by(Plan.price_per_month).first()

        # If no plan found, get alternative suggestions
        if not suggested_plan and requirements:
            flash('No exact match found for your requirements. Here are some suggestions:', 'info')
            
            # Try finding plans without phone model if that was specified
            if phone_model:
                base_query = Plan.query
                if data_needed:
                    try:
                        base_query = base_query.filter(
                            db.or_(
                                Plan.data.ilike('%unl%'),
                                db.cast(db.func.replace(Plan.data, ' GB', ''), db.Float) >= float(data_needed)
                            )
                        )
                    except ValueError:
                        pass
                if calls_needed:
                    base_query = base_query.filter(Plan.calls_text.ilike(f"%{calls_needed}%"))
                if age < 18:
                    base_query = base_query.filter(Plan.price_per_month <= 15)
                
                alternative = base_query.order_by(Plan.price_per_month).first()
                if alternative:
                    flash(f'Found a plan matching your data and calls requirements without the specific phone model.', 'info')
            
            # Try finding plans with less data if that was specified
            elif data_needed:
                try:
                    data_needed_num = float(data_needed)
                    if data_needed_num > 1:
                        lower_data_query = Plan.query
                        if calls_needed:
                            lower_data_query = lower_data_query.filter(Plan.calls_text.ilike(f"%{calls_needed}%"))
                        if age < 18:
                            lower_data_query = lower_data_query.filter(Plan.price_per_month <= 15)
                        
                        alternative = lower_data_query.filter(
                            db.cast(db.func.replace(Plan.data, ' GB', ''), db.Float) >= (data_needed_num / 2)
                        ).order_by(Plan.price_per_month).first()
                        
                        if alternative:
                            flash(f'Found a plan with {alternative.data} instead of {data_needed}GB.', 'info')
                except ValueError:
                    pass

    return render_template('suggest.html', suggested_plan=suggested_plan)

@app.route('/my_memberships')
def my_memberships():
    if 'user_id' not in session:
        flash('Please log in to view your memberships.', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    memberships = Member.query.filter_by(user_id=user.id).order_by(Member.created_at.desc()).all()
    return render_template('my_memberships.html', memberships=memberships)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')
        updated = False
        # Username update
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                flash('Username already taken.', 'danger')
            else:
                user.username = new_username
                session['username'] = new_username
                updated = True
        # Email update
        if new_email and new_email != user.email:
            if User.query.filter_by(email=new_email).first():
                flash('Email already in use.', 'danger')
            else:
                user.email = new_email
                updated = True
        # Password update
        if new_password:
            user.password_hash = generate_password_hash(new_password)
            updated = True
        if updated:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        elif not (new_username or new_email or new_password):
            flash('No changes made.', 'info')
    return render_template('profile.html', user=user)

# --- CLI Commands for DB management ---
@app.cli.command("seed-db")
def seed_db():
    """Populates the database with initial data."""
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Providers
        fone = Provider(name='Fone')
        gap = Provider(name='Gap')
        flipper = Provider(name='Flipper')
        db.session.add_all([fone, gap, flipper])
        db.session.commit()

        # Fone Plans
        fone_plans = [
            Plan(provider=fone, plan_name='Super saver', data='0.5 GB', calls_text='500/500', price_per_month=8),
            Plan(provider=fone, plan_name='Saver', data='1 GB', calls_text='750/750', price_per_month=11),
            Plan(provider=fone, plan_name='Average', data='4 GB', calls_text='unl/unl', price_per_month=16),
            Plan(provider=fone, plan_name='Regular', data='8 GB', calls_text='unl/unl', price_per_month=19),
            Plan(provider=fone, plan_name='Spender', data='100 GB', calls_text='unl/unl', price_per_month=29),
            Plan(provider=fone, plan_name='All-in', data='100 GB', calls_text='unl/unl', phone_model='iPhone 14 Pro', price_per_month=75),
            Plan(provider=fone, plan_name='All-in', data='100 GB', calls_text='unl/unl', phone_model='iPhone 14', price_per_month=60),
            Plan(provider=fone, plan_name='All-in', data='100 GB', calls_text='unl/unl', phone_model='iPhone 13', price_per_month=55),
            Plan(provider=fone, plan_name='All-in', data='100 GB', calls_text='unl/unl', phone_model='Samsung S22', price_per_month=75),
            Plan(provider=fone, plan_name='All-in', data='100 GB', calls_text='unl/unl', phone_model='Samsung S21', price_per_month=52),
            Plan(provider=fone, plan_name='Just phone', phone_model='iPhone 14 Pro', price_per_month=55),
            Plan(provider=fone, plan_name='Just phone', phone_model='iPhone 14', price_per_month=40),
            Plan(provider=fone, plan_name='Just phone', phone_model='iPhone 13', price_per_month=35),
            Plan(provider=fone, plan_name='Just phone', phone_model='Samsung S22', price_per_month=55),
            Plan(provider=fone, plan_name='Just phone', phone_model='Samsung S21', price_per_month=32),
        ]

        # Gap Plans
        gap_plans = [
            Plan(provider=gap, plan_name='Super saver', data='1 GB', calls_text='unl/unl', price_per_month=10),
            Plan(provider=gap, plan_name='Saver', data='2 GB', calls_text='unl/unl', price_per_month=14),
            Plan(provider=gap, plan_name='Average', data='5 GB', calls_text='unl/unl', price_per_month=19),
            Plan(provider=gap, plan_name='Regular', data='10 GB', calls_text='unl/unl', price_per_month=25),
            Plan(provider=gap, plan_name='Spender', data='unl GB', calls_text='unl/unl', price_per_month=32),
            Plan(provider=gap, plan_name='All-in', data='unl GB', calls_text='unl/unl', phone_model='iPhone 14 Pro', price_per_month=79),
            Plan(provider=gap, plan_name='All-in', data='unl GB', calls_text='unl/unl', phone_model='iPhone 14', price_per_month=55),
            Plan(provider=gap, plan_name='All-in', data='unl GB', calls_text='unl/unl', phone_model='iPhone 13', price_per_month=50),
            Plan(provider=gap, plan_name='All-in', data='unl GB', calls_text='unl/unl', phone_model='Samsung S22', price_per_month=72),
            Plan(provider=gap, plan_name='All-in', data='unl GB', calls_text='unl/unl', phone_model='Samsung S21', price_per_month=50),
            Plan(provider=gap, plan_name='Just phone', phone_model='iPhone 14 Pro', price_per_month=59),
            Plan(provider=gap, plan_name='Just phone', phone_model='iPhone 14', price_per_month=42),
            Plan(provider=gap, plan_name='Just phone', phone_model='iPhone 13', price_per_month=37),
            Plan(provider=gap, plan_name='Just phone', phone_model='Samsung S22', price_per_month=57),
            Plan(provider=gap, plan_name='Just phone', phone_model='Samsung S21', price_per_month=30),
        ]

        # Flipper Plans
        flipper_plans = [
            Plan(provider=flipper, plan_name='Super saver', data='1 GB', calls_text='500/500', price_per_month=6),
            Plan(provider=flipper, plan_name='Saver', data='2 GB', calls_text='750/750', price_per_month=8),
            Plan(provider=flipper, plan_name='Average', data='3 GB', calls_text='unl/unl', price_per_month=10),
            Plan(provider=flipper, plan_name='Regular', data='6 GB', calls_text='unl/unl', price_per_month=15),
            Plan(provider=flipper, plan_name='Spender', data='35 GB', calls_text='unl/unl', price_per_month=22),
            Plan(provider=flipper, plan_name='All-in', data='35 GB', calls_text='unl/unl', phone_model='iPhone 14 Pro', price_per_month=70),
            Plan(provider=flipper, plan_name='All-in', data='35 GB', calls_text='unl/unl', phone_model='iPhone 14', price_per_month=58),
            Plan(provider=flipper, plan_name='All-in', data='35 GB', calls_text='unl/unl', phone_model='iPhone 13', price_per_month=49),
            Plan(provider=flipper, plan_name='All-in', data='35 GB', calls_text='unl/unl', phone_model='Samsung S22', price_per_month=70),
            Plan(provider=flipper, plan_name='All-in', data='35 GB', calls_text='unl/unl', phone_model='Samsung S21', price_per_month=48),
            Plan(provider=flipper, plan_name='Just phone', phone_model='iPhone 14 Pro', price_per_month=60),
            Plan(provider=flipper, plan_name='Just phone', phone_model='iPhone 14', price_per_month=39),
            Plan(provider=flipper, plan_name='Just phone', phone_model='iPhone 13', price_per_month=29),
            Plan(provider=flipper, plan_name='Just phone', phone_model='Samsung S22', price_per_month=50),
            Plan(provider=flipper, plan_name='Just phone', phone_model='Samsung S21', price_per_month=35),
        ]
        
        db.session.add_all(fone_plans)
        db.session.add_all(gap_plans)
        db.session.add_all(flipper_plans)
        
        db.session.commit()
        click.echo("Database seeded with initial data.")

if __name__ == '__main__':
    app.run(debug=True)