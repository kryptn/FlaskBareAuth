# Flask Auth Tutorial

So you want a basic example? I made a quick tutorial.

Please don't just copy and paste this, actually follow through and understand each step.

A basic authentication platform has four pieces:

* Create a new user
* Let users log in
* Maintain user session
* Let users log out

We can break it down pretty simply. First, we're going to use [`flask`](http://flask.pocoo.org/) and [`flask-sqlalchemy`](https://pythonhosted.org/Flask-SQLAlchemy/index.html) so get those installed with pip

First step for this new flask app (save as `app.py`):

    from flask import flask, session, redirect, url_for, render_template, request, flash

    app = Flask(__name__)
    #this stores 'auth.db' in the relative directory
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
    db = SQLAlchemy(app)
    # We need a secret key since we'll be using flask's request
    app.secret_key = "Such a secret"

Now we have a basic app and a database, but nothing in it. We're keeping this simple and we'll just store username and password. Still in `app.py`:

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

Now we need to set up our actual database. Run python in your shell:

    >>> from app import db
    >>> db.create_all()

And now you'll find an 'auth.db' file in your folder.  
Now that we have a functioning database, we can use it! Let's test it out with another python shell.
    
    >>> new_user = User('the_new_user', 'their secure password')
    >>> db.session.add(new_user)
    >>> db.session.commit()
    >>> User.query.filter_by(username="the_new_user").first()
    >>> <User the_new_user>

Neat, right?

Now we need some pages to actually let users log in. Still in `app.py`:

    @app.route('/')
    def index():
        return render_template('index.html')

In our template `templates/layout.html` we'll handle the [`message flashing`](http://flask.pocoo.org/docs/0.10/quickstart/#message-flashing), that'll show the user any errors that might come up:

    <!doctype html>
    <title>Flask Basic Login</title>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul class=flashes>
          {% for message in messages %}
            <li>{{ message }}</li>
          {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    {% block body %}{% endblock %}

In our template `templates/index.html` we'll have both forms, because I'm lazy and didn't feel like making a separate register page:

    {% extends "layout.html" %}
    {% block body %}
    {% if session['username'] %}
    <h1>Hello {{ session['username']}}!</h1>
    <a href="{{url_for('logout')}}">Logout</a>
    or <a href="{{url_for('secret')}}">go to the secret page</a>
    {% else %}
    <h1> Login </h1>
    <form action="{{url_for('login')}}" method=post>
        <dl>
            <dt>Username:
            <dd><input type=text name=username value="{{request.form.username}}">
            <dt>Password:
            <dd><input type=password name=password>
        </dl>
        <p><input type=submit value="Login"></p>
    </form>
    
    <h1> Register </h1>
    <form action="{{url_for('register')}}" method=post>
        <dl>
            <dt>Username:
            <dd><input type=text name=username value="{{request.form.username}}">
            <dt>Password:
            <dd><input type=password name=password>
        </dl>
        <p><input type=submit value="Register"></p>
    </form>

    {% endif %}
    {% endblock %}

And we'll want a secret-only-while-logged-in page, right? `templates/secret.html`:

    {% extends "layout.html" %}
    {% block body %}
    <h1>Hi {{session['username']}}! This is the secret page</h1>
    <p><a href="{{url_for('index')}}">Go home</a></p>
    <p><a href="{{url_for('logout')}}">logout</a></p>
    {% endblock %}

So now we have our templates, let's implement the logic for it all. We need a method for registration, logging in, and logging out.

Let's start with registration. Since we're keeping this simple, all we have to do is check if a user exists already, which is pretty simple using SQLAlchemy:

    >>> result = User.query.filter_by(username='our test username').first()

the `.first` will either return the first result that matches, or None if there isn't one. we can take advantage of that pretty simply in `app.py`:

    @app.route('/register', methods=['GET','POST'])
    def register():
        if request.method == 'POST': #check to make sure it was a POST request by the form
            result = User.query.filter_by(username=request.form['username']).first()
            if result is None:
                new_user = User(request.form['username'],request.form['password'])
                session['username'] = new_user.username
                db.session.add(new_user)
                db.session.commit() #create and add the new user
                flash('registered and logged in') #send the flash message if successful
            else:
                flash('user already exists') #or an error message if not
    
        return redirect(url_for('index')) #redirect back to our index route

This lets a user create a new account, stores their username and password, and logs them in automatically. Now we need a way for an existing user to log in again in `app.py`:

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            result = User.query.filter_by(username=request.form['username']).first()
            if result and request.form['password'] == result.password:
                session['username'] = result.username #store logged in user to their session
            else:
                flash('wrong user or password')
    
        return redirect(url_for('index'))

This will log in a user if their user exists, first, and then if their password matches. There's still some room for improvement, since we're storing plaintext passwords. it wouldn't be hard to secure it with [`hashlib`](https://docs.python.org/2/library/hashlib.html) but we're keeping it extremely simple.

We still need our secret page, and that requires an extra step. We need to make sure the user is actually authenticated before rendering the secret template, and there's a few ways to do this. We can put everything inside an if statement in the method that checks the existence of our user in the session object, or what we will do, is make a decorator using [`functools.wraps`](https://docs.python.org/2/library/functools.html#functools.wraps) to do all that for us! in `app.py`:

    from functools import wraps

    def authenticated(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'username' in session:
                return f(*args, **kwargs)
            else:
                flash('You must be logged in')
                return redirect(url_for('index'))
        return wrapper

That way we can just add `@authenticated` to the method to ensure the user will be authed before seeing the content:

    @app.route('/secret')
    @authenticated
    def secret():
        return render_template('secret.html')

And finally we need a way to log the user out, in `app.py`:

    @app.route('/logout')
    def logout():
        session.pop('username', None)
        flash('Logged out')
        return redirect(url_for('index'))

This destroys the user session, regardless if it existed or not. 

So now we should have a working basic example of authentication. throw this at the bottom of `app.py`:

    if __name__ == "__main__":
        app.run(debug=True) #host='0.0.0.0' if you're running it externally

And run it with `python app.py`. It should start up, you can go to whichever ip/url it's being hosted on with port 5000, and it should load right up! go ahead and register, log out, log in, and everything.

If something is missing, you can compare it to the [Project I created just for this](https://github.com/kryptn/FlaskBareAuth).

Let me know how things work!
