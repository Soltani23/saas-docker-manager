from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Container
from docker_manager import DockerManager
from config import Config
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Docker manager
docker_mgr = DockerManager(app.config.get('DOCKER_BASE_URL', 'unix:///var/run/docker.sock'))

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# Routes

@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            logger.info(f"User {username} logged in successfully")
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('login.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('login.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {username}")
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their containers"""
    containers = Container.query.filter_by(user_id=current_user.id).all()
    
    # Update container statuses from Docker
    for container in containers:
        container.status = docker_mgr.get_container_status(container.container_id)
    
    db.session.commit()
    
    return render_template('dashboard.html', user=current_user, containers=containers)

# API Routes for container management

@app.route('/api/containers', methods=['GET'])
@login_required
def get_containers():
    """Get all containers for current user"""
    containers = Container.query.filter_by(user_id=current_user.id).all()
    
    result = []
    for c in containers:
        c.status = docker_mgr.get_container_status(c.container_id)
        result.append({
            'id': c.id,
            'container_id': c.container_id,
            'name': c.name,
            'port': c.port,
            'status': c.status,
            'url': f'http://localhost:{c.port}'
        })
    
    db.session.commit()
    return jsonify(result)

@app.route('/api/containers/create', methods=['POST'])
@login_required
def create_container():
    """Create a new Nginx container for user"""
    try:
        data = request.json
        container_name = data.get('name', f'user{current_user.id}_nginx_{len(current_user.containers) + 1}')
        
        # Find available port
        used_ports = [c.port for c in Container.query.all()]
        port = None
        for p in range(app.config['PORT_RANGE_START'], app.config['PORT_RANGE_END']):
            if p not in used_ports:
                port = p
                break
        
        if not port:
            return jsonify({'error': 'No available ports'}), 400
        
        # Custom HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{current_user.username}'s Container</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}
        .container {{
            text-align: center;
            padding: 3rem;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        h1 {{ font-size: 3rem; margin-bottom: 1rem; }}
        p {{ font-size: 1.2rem; opacity: 0.9; }}
        .info {{ 
            margin-top: 2rem; 
            padding: 1rem;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 {current_user.username}'s Container</h1>
        <p>Container: {container_name}</p>
        <div class="info">
            <p><strong>Port:</strong> {port}</p>
            <p><strong>Status:</strong> Running ✅</p>
            <p><strong>Server:</strong> Nginx Alpine</p>
        </div>
    </div>
</body>
</html>"""
        
        # Create Docker container
        result = docker_mgr.create_nginx_container(
            container_name=container_name,
            port=port,
            html_content=html_content,
            user_id=current_user.id
        )
        
        # Save to database
        container = Container(
            container_id=result['id'],
            name=container_name,
            port=port,
            status=result['status'],
            user_id=current_user.id
        )
        
        db.session.add(container)
        db.session.commit()
        
        logger.info(f"Container {container_name} created for user {current_user.username}")
        
        return jsonify({
            'success': True,
            'container': {
                'id': container.id,
                'name': container.name,
                'port': port,
                'url': f'http://localhost:{port}'
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating container: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/containers/<int:container_id>/start', methods=['POST'])
@login_required
def start_container(container_id):
    """Start a stopped container"""
    container = Container.query.get_or_404(container_id)
    
    # Verify ownership
    if container.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if docker_mgr.start_container(container.container_id):
        container.status = 'running'
        db.session.commit()
        return jsonify({'success': True, 'status': 'running'})
    
    return jsonify({'error': 'Failed to start container'}), 500

@app.route('/api/containers/<int:container_id>/stop', methods=['POST'])
@login_required
def stop_container(container_id):
    """Stop a running container"""
    container = Container.query.get_or_404(container_id)
    
    # Verify ownership
    if container.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if docker_mgr.stop_container(container.container_id):
        container.status = 'exited'
        db.session.commit()
        return jsonify({'success': True, 'status': 'exited'})
    
    return jsonify({'error': 'Failed to stop container'}), 500

@app.route('/api/containers/<int:container_id>/delete', methods=['DELETE'])
@login_required
def delete_container(container_id):
    """Delete a container"""
    container = Container.query.get_or_404(container_id)
    
    # Verify ownership
    if container.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if docker_mgr.delete_container(container.container_id):
        db.session.delete(container)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Failed to delete container'}), 500

# Initialize database
def init_db():
    """Initialize database and create default users"""
    with app.app_context():
        db.create_all()
        
        # Create default users if they don't exist
        if not User.query.filter_by(username='soltani').first():
            user1 = User(username='soltani', email='amal@example.com')
            user1.set_password('amal123')
            db.session.add(user1)
        
        if not User.query.filter_by(username='amadou').first():
            user2 = User(username='amadou', email='amadou@example.com')
            user2.set_password('amadou123')
            db.session.add(user2)
        
        db.session.commit()
        logger.info("Database initialized with default users")

if __name__ == '__main__':
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Run app
    app.run(host='0.0.0.0', port=5000, debug=True)
