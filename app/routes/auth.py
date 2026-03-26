from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        login_type = request.form.get('login_type', 'user')  # Get selected login type
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Validate role if admin login is selected
            if login_type == 'admin':
                if user.role != 'admin':
                    flash('You do not have admin privileges. Please use User Login.', 'error')
                    return render_template('login.html')
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role
            session['current_stage'] = user.current_stage or 'IMMUNITY'
            flash('Login successful!', 'success')
            
            # Role-based redirect
            if user.role == 'admin' and login_type == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        role = request.form.get('role', 'user')
        admin_code = request.form.get('admin_code', '')
        
        # Admin access code verification
        ADMIN_ACCESS_CODE = 'TRIGEN_ADMIN_2024'
        
        if role == 'admin':
            if admin_code != ADMIN_ACCESS_CODE:
                flash('Invalid admin access code. Please contact the system administrator.', 'error')
                return redirect(url_for('auth.register'))
        
        if password != confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))
            
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Registration successful as {role}! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
