from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from flask_login import UserMixin, LoginManager, login_required, logout_user, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

project_consultants = db.Table(
    'project_consultants',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('consultant_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='consultant')
    clients = db.relationship('Client', back_populates='consultant')
    projects = db.relationship('Project', secondary=project_consultants, back_populates='consultants')
    tasks = db.relationship('Task', back_populates='consultant')

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    ssn = db.Column(db.String(11), unique=True, nullable=False)
    postalcode = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.String(500), nullable=True)
    consultant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    consultant = db.relationship('User', back_populates='clients')
    projects = db.relationship('Project', back_populates='client')

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default="To Do", nullable=False)
    consultants = db.relationship('User', secondary=project_consultants, back_populates='projects')
    client = db.relationship('Client', back_populates='projects')
    tasks = db.relationship('Task', back_populates='project')

    __table_args__ = (
        CheckConstraint("status IN ('To Do', 'In Progress', 'Completed')", name="check_project_status"),
    )

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    consultant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default="To Do", nullable=False)
    project = db.relationship('Project', back_populates='tasks')
    consultant = db.relationship('User', back_populates='tasks')

    __table_args__ = (
        CheckConstraint("status IN ('To Do', 'In Progress', 'Completed')", name="check_task_status"),
    )

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            if current_user.role != 'admin':
                return redirect('/profile')
            else:
                return redirect('/dashboard')
        else:
            flash("Invalid username or password")
            return redirect('/login') 
    else:
        return render_template('login.html')

@app.route("/password/recovery", methods=['GET', 'POST'])
def password_recovery():
    if request.method =='POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            return redirect('/')
        else:
            flash("The email address you entered does not exist")
    return render_template('password_recovery.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/register", methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect('/register')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)     
        
        user = User(fullname=fullname, username=username, email=email, phone=phone, password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect('/login')
        except Exception as e:
            print(f"Error: {e}")
            return redirect('/register')
    return render_template('register.html')

@app.route("/clients/add", methods=['GET', 'POST'])
@login_required
def add_client():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        ssn = request.form.get('ssn')
        postalcode = request.form.get('postalcode')
        notes = request.form.get('notes')
        new_client = Client(name=name, email=email, phone=phone, address=address, ssn=ssn, postalcode=postalcode, notes=notes)
        try:
            db.session.add(new_client)
            db.session.commit()
            return redirect('/dashboard')
        except Exception as e:
            print(f"Error: {e}")
            return redirect('/clients/add')
    return render_template('add_client.html')

@app.route("/clients/edit")
@login_required
def edit_client():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_clients = Client.query.all()
    return render_template('edit_client.html', clients=all_clients)

@app.route("/clients/edit/form/<int:client_id>", methods=['GET', 'POST'])
@login_required
def edit_client_form(client_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    client = Client.query.get(client_id)
    all_consultants = User.query.filter_by(role='consultant').all()
    if not client:
        return "Client not found", 404
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        client.ssn = request.form.get('ssn')
        client.postalcode = request.form.get('postalcode')
        client.notes = request.form.get('notes')
        client.consultant_id = request.form.get('consultant')
        try:
            db.session.commit()
            return redirect('/clients/edit')
        except Exception as e:
            print(f"Error: {e}")
            return redirect(f'/clients/edit/form/{client_id}')
    return render_template('edit_client_form.html', client=client, consultants=all_consultants)

@app.route("/clients/delete/<int:client_id>", methods=['POST'])
@login_required
def delete_client(client_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    client = Client.query.get(client_id)
    if not client:
        return "Client not found", 404
    try:
        db.session.delete(client)
        db.session.commit()
        return redirect('/clients/edit')
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while deleting the client", 500 
    
@app.route('/add/project', methods=['GET', 'POST'])
@login_required
def add_project():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_clients = Client.query.all()
    if request.method == 'POST':
        name = request.form.get('project-name')
        client_id = request.form.get('client-id')
        deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date() if request.form.get('deadline') else None
        description = request.form.get('description')
        new_project = Project(name=name, client_id=client_id, deadline=deadline, description=description)
        try:
            db.session.add(new_project)
            db.session.commit()
            return redirect('/dashboard')
        except Exception as e:
            print(f"Error: {e}")
            return redirect('/add/project')
    return render_template('add_project.html', clients=all_clients)

@app.route('/add/task', methods=['GET', 'POST'])
@login_required
def add_task():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_projects = Project.query.all()
    if request.method == 'POST':
        name = request.form.get('task-name')
        project_id = request.form.get('project')
        deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date() if request.form.get('deadline') else None
        description = request.form.get('description')
        new_task = Task(name=name, project_id=project_id, deadline=deadline, description=description)
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/dashboard')
        except Exception as e:
            print(f"Error: {e}")
            return redirect('/add/task')
    return render_template('add_task.html', projects=all_projects)

@app.route('/manage/project')
@login_required
def manage_projects():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_projects = Project.query.all()
    return render_template('manage_project.html', projects=all_projects)

@app.route("/projects/edit/<int:project_id>", methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    project = Project.query.get(project_id)
    all_clients = Client.query.all()
    all_consultants = User.query.filter_by(role='consultant').all()
    all_project_tasks = Task.query.filter_by(project_id=project_id).all()
    if not project:
        return "Project not found", 404
    if request.method == 'POST':
        project.name = request.form.get('project-name')
        project.client_id = request.form.get('client-id')
        project.deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date() if request.form.get('deadline') else None
        selected_consultants = request.form.getlist('consultants_ids')
        project.consultants = User.query.filter(User.id.in_(selected_consultants)).all()
        project.description = request.form.get('description')
        project.status = request.form.get('status')
        try:
            db.session.commit()
            return redirect('/manage/project')  
        except Exception as e:
            print(f"Error: {e}")
            return "An error occurred while updating the project", 500
    return render_template('edit_project.html', project=project, consultants=all_consultants, tasks=all_project_tasks, clients=all_clients, selected_client=project.client_id)

@app.route("/projects/delete/<int:project_id>", methods=['POST'])
@login_required
def delete_project(project_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    project = Project.query.get(project_id)
    if not Project:
        return "Project not found", 404
    try:
        db.session.delete(project)
        db.session.commit()
        return redirect('/manage/project')
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while deleting the project", 500 

@app.route("/projects/tasks/edit/<int:task_id>", methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    task = Task.query.get(task_id)
    all_projects = Project.query.all()
    all_consultants = User.query.filter_by(role='consultant').all()
    project_id = task.project_id
    if not Task:
        return "Task not found", 404
    if request.method == 'POST':
        task.name = request.form.get('name')
        task.project_id = request.form.get('project-id')
        task.deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date() if request.form.get('deadline') else None
        task.consultant_id = request.form.get('consultant_id')
        task.description = request.form.get('description')
        task.status = request.form.get('status')
        try:
            db.session.commit()
            return redirect(f'/projects/edit/{project_id}')
        except Exception as e:
            print(f"Error: {e}")
            return "An error occurred while updating the task", 500
    return render_template('edit_project_task.html', task=task, projects=all_projects, consultants=all_consultants, selected_project=task.project_id, selected_consultant=task.consultant_id)

@app.route("/projects/tasks/delete/<int:task_id>", methods=['POST'])
@login_required
def delete_task(task_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    task = Task.query.get(task_id)
    project_id = task.project_id
    if not Task:
        return "Task not found", 404
    try:
        db.session.delete(task)
        db.session.commit()
        return redirect(f'/projects/edit/{project_id}')
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while deleting the task", 500 
    
@app.route("/clients/list")
@login_required
def clients_list():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_clients = Client.query.all()
    total_clients = Client.query.count()
    return render_template('clients_list.html', clients=all_clients, total_clients=total_clients)

@app.route("/consultants/list")
@login_required
def consultants_list():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_consultants = User.query.filter_by(role='consultant').all()
    total_consultants = User.query.filter_by(role='consultant').count()
    return render_template('consultants_list.html', consultants=all_consultants, total_consultants=total_consultants)

@app.route("/admins/list")
@login_required
def admin_list():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_admins = User.query.filter_by(role='admin').all()
    total_admins = User.query.filter_by(role='admin').count()
    return render_template('admins_list.html', admins=all_admins, total_admins=total_admins)

@app.route('/active/projects/list')
@login_required
def active_projects():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_active_projects = Project.query.filter(Project.status.in_(['To Do', 'In Progress'])).all()
    total_active_projects = Project.query.filter(Project.status.in_(['To Do', 'In Progress'])).count()
    return render_template('active_projects_list.html', active_projects=all_active_projects, total_active_projects=total_active_projects)

@app.route('/completed/projects/list')
@login_required
def completed_projects():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_completed_projects = Project.query.filter_by(status='Completed').all()
    total_completed_projects = Project.query.filter_by(status='Completed').count()
    return render_template('completed_projects_list.html', completed_projects=all_completed_projects, total_completed_projects=total_completed_projects)

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    return render_template('dashboard.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect('/')

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)