from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, logout_user, login_user, current_user

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='consultant')

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=True)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            if current_user.role != 'admin':
                return redirect('/profile')
            else:
                return redirect('/dashboard')
        else:
            return redirect('/login')
    else:
        return render_template('login.html')

@app.route("/password/recovery", methods=['GET', 'POST'])
def password_recovery():
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
            return redirect('/register')  
        
        user = User(fullname=fullname, username=username, email=email, phone=phone, password=password)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect('/login')
        except Exception as e:
            print(f"Error: {e}")
            return redirect('/register')  # Handle duplicate entry or other errors
    return render_template('register.html')

# Admin-Only
@app.route("/clients")
@login_required
def clients():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    all_clients = Client.query.all()
    return render_template('clients.html', clients=all_clients)

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
        new_client = Client(name=name, email=email, phone=phone, address=address)
        try:
            db.session.add(new_client)
            db.session.commit()
            return redirect('/dashboard')
        except Exception as e:
            print(f"Error: {e}")
            return redirect('/clients/add')
    return render_template('add_client.html')

@app.route("/clients/edit/<int:client_id>", methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    if current_user.role != 'admin':
        return "Unauthorized", 403
    client = Client.query.get(client_id)
    if not client:
        return "Client not found", 404
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        try:
            db.session.commit()
            return redirect('/clients')
        except Exception as e:
            print(f"Error: {e}")
            return redirect(f'/clients/edit/{client_id}')
    return render_template('edit_client.html', client=client)

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
        return redirect('/clients')
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while deleting the client", 500


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