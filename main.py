from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

# note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:1234@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = 'y337kGys&zP3B'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    #put function in allowed_routes, not url path, hence no /
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/', methods=['GET'])
def main():
    return redirect('/index')

@app.route('/index', methods=['GET'])
def index():
    user_list = User.query.all()
    email = request.args.get('email')
    user = User.query.get('email')
    return render_template('index.html', email=email, user_list = user_list, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['email'] = email
            flash('You are now logged In!', 'message')
            print(session)
            return redirect('/newpost')
        else:
            flash('User password incorrect or email does not exist', 'error')
    return render_template('login.html', heading='Log In')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        if password != verify:
            flash('Password does not match', 'error')
            return redirect('/signup')

        if len(password) < 3 or len(email) < 3:
            flash('Username and password must be 4 or more characters long.', 'error')
            return redirect('/signup')
        
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user and password == verify and len(email) > 3 and len(password) > 3:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/newpost')
        else:
            flash('Duplicate user exists', 'error')
    return render_template('signup.html', heading='Sign Up Now')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/blog')

@app.route('/blog', methods=['GET'])
def blog():
    heading1 = 'Single Blog Post'
    heading2 = "User's Blog Posts"
    heading3 = 'All Blog Posts'
    id = request.args.get('id')
    owner = request.args.get('owner')
    email = request.args.get('email')

    #query for single blog entry first
    if id:
        post = Blog.query.get(id)
        return render_template('singlepost.html', heading=heading1, post=post, id=id, owner=owner)
    #TODO:
    #show blog posts from only one user (query for user that owns the blog's posts)
    elif email:
        email_id = User.query.get(id)
        email_blog_list = Blog.query.filter_by(owner=email).all()
        return render_template('singleuserblog.html', heading=heading2, email=email, email_blog_list=email_blog_list)
    #show blog posts for all users
    else:
        blog_list = Blog.query.all()
        return render_template('alluserblog.html', heading=heading3, blog_list=blog_list)

@app.route('/newpost', methods=['GET', 'POST'])
def newpost():
    owner = User.query.filter_by(email=session['email']).first()
    
    if request.method == 'POST':
        id = request.form['id']
        post = Blog.query.get(id)
        title = request.form['title']
        body = request.form['body']
        title_error = ''
        body_error = ''

        if title.strip() == "":
            title_error = 'Please create a title.'
            return render_template('newpost.html', heading='New Post', title_error=title_error, body_error=body_error, id=id, title=title, body=body)
        if body.strip() == "":
            body_error = 'Please write something for your blog post.'
            return render_template('newpost.html', heading='New Post', title_error=title_error, body_error=body_error, id=id, title=title, body=body)
        else:
            new_post = Blog(title, body, owner)
            db.session.add(new_post)
            db.session.commit()
            return redirect('/blog?id=' + str(new_post.id))
    
    return render_template('newpost.html', heading='New Post')

if __name__ == '__main__':
    app.run()