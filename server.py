from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, logout_user, login_user

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/profile")
def profile():
    return render_template('profile.html')

@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')

@app.route("/logout")
def logout():
    return redirect('/')

if __name__ == '__main__':
    app.run()