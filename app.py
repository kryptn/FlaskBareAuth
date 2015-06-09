from functools import wraps

from flask import Flask, session, redirect, url_for, render_template, request, flash
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
db = SQLAlchemy(app)
app.secret_key = "This is supposed to be a secret"

class User(db.Model):
    """ 
    User database model

    """
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256))

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username

def authenticated(f):
    """
    Decorator to enforce authentication on routed methods

    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
            flash('You must be logged in')
            return redirect(url_for('index'))
    return wrapper

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    """
    Checks database to verify user doesn't exist,
    then creates and logs on new user

    Any error is flashed

    """

    if request.method == 'POST':
        result = User.query.filter_by(username=request.form['username']).first()
        if result is None:
            new_user = User(request.form['username'],request.form['password'])
            session['username'] = new_user.username
            db.session.add(new_user)
            db.session.commit()
            flash('registered and logged in')
        else:
            flash('user already exists')

    return redirect(url_for('index'))

@app.route('/login', methods=['GET','POST'])
def login():
    """
    Verifies user exists and compares password

    Any error is flashed
    """

    if request.method == 'POST':
        result = User.query.filter_by(username=request.form['username']).first()
        if result and request.form['password'] == result.password:
            session['username'] = result.username
        else:
            flash('wrong user or password')

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """
    Destroys any active session

    """
    
    session.pop('username', None)
    flash('Logged out')
    return redirect(url_for('index'))

@app.route('/secret')
@authenticated
def secret():
    """
    Authenticated only route

    @authenticated will flash a message if not authed
    """
    return render_template('secret.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
