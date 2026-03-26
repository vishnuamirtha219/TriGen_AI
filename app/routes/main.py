from flask import Blueprint, render_template, redirect, url_for, session, flash
from app.models import User
from app.extensions import db

main_bp = Blueprint('main', __name__)

def stage_required(required_stage):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            
            user = User.query.get(session['user_id'])
            if not user:
                return redirect(url_for('auth.login'))
            
            # Sequence: IMMUNITY -> SICKLE_CELL -> LSD -> COMPLETED
            stages = ['IMMUNITY', 'SICKLE_CELL', 'LSD', 'COMPLETED']
            try:
                user_stage_idx = stages.index(user.current_stage)
                req_stage_idx = stages.index(required_stage)
                
                if user_stage_idx < req_stage_idx:
                    flash(f"Please complete {stages[user_stage_idx]} phase first.", "warning")
                    return redirect(url_for(f"main.{stages[user_stage_idx].lower()}"))
                
                # If user already completed this stage and is trying to go back, that's fine for now, 
                # but let's stick to the required workflow.
            except (ValueError, IndexError):
                pass
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@main_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    from app.models import User, MedicalRecord, ImmunityResult, SickleResult, LSDResult
    from sqlalchemy import func
    
    user_count = User.query.count()
    record_count = MedicalRecord.query.count()
    
    # User role breakdown
    admin_count = User.query.filter_by(role='admin').count()
    regular_user_count = User.query.filter_by(role='user').count()
    
    # Get breakdown of records
    immunity_count = MedicalRecord.query.filter_by(module_type='IMMUNITY').count()
    sickle_count = MedicalRecord.query.filter_by(module_type='SICKLE_CELL').count()
    lsd_count = MedicalRecord.query.filter_by(module_type='LSD').count()
    
    # Confidence score analytics
    avg_immunity_confidence = db.session.query(func.avg(ImmunityResult.confidence_score)).scalar() or 0
    avg_sickle_confidence = db.session.query(func.avg(SickleResult.confidence_score)).scalar() or 0
    avg_lsd_confidence = db.session.query(func.avg(LSDResult.confidence_score)).scalar() or 0
    
    # High confidence counts (>80%)
    high_conf_immunity = ImmunityResult.query.filter(ImmunityResult.confidence_score >= 80).count()
    high_conf_sickle = SickleResult.query.filter(SickleResult.confidence_score >= 80).count()
    high_conf_lsd = LSDResult.query.filter(LSDResult.confidence_score >= 80).count()
    
    recent_records = MedicalRecord.query.order_by(MedicalRecord.record_date.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', 
                           user_count=user_count,
                           admin_count=admin_count,
                           regular_user_count=regular_user_count,
                           record_count=record_count,
                           immunity_count=immunity_count,
                           sickle_count=sickle_count,
                           lsd_count=lsd_count,
                           avg_immunity_confidence=round(avg_immunity_confidence, 1),
                           avg_sickle_confidence=round(avg_sickle_confidence, 1),
                           avg_lsd_confidence=round(avg_lsd_confidence, 1),
                           high_conf_immunity=high_conf_immunity,
                           high_conf_sickle=high_conf_sickle,
                           high_conf_lsd=high_conf_lsd,
                           recent_records=recent_records)

@main_bp.route('/immunity')
@stage_required('IMMUNITY')
def immunity():
    return render_template('immunity.html')

@main_bp.route('/sickle_cell')
@stage_required('SICKLE_CELL')
def sickle_cell():
    return render_template('sickle_cell.html')

@main_bp.route('/lsd')
@stage_required('LSD')
def lsd():
    return render_template('lsd.html')

@main_bp.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    return render_template('history.html', user=user)

@main_bp.route('/reports/<filename>')
def serve_report(filename):
    import os
    from flask import send_from_directory
    from config import Config
    # Reports dir is sibling to data dir
    reports_dir = os.path.join(os.path.dirname(Config.UPLOAD_FOLDER), 'reports')
    return send_from_directory(reports_dir, filename)
