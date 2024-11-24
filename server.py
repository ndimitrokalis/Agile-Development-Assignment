from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, logout_user, login_user

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = None
        if user is None:
            return redirect('/login')
        else:
            if user.password == password:
                login_user(user)
                return redirect('/profile')
            else:
                return redirect('/login')
    else:
        return render_template('login.html')

@app.route("/register",methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = None
        try:
            pass
            return redirect('/login')
        except:
            return redirect('/register')
    return render_template('register.html')

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect('/')

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

if __name__ == '__main__':
    app.run()