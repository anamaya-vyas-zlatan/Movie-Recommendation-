from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,IntegerField,ValidationError,DateField, SubmitField
from passlib.hash import sha256_crypt
from functools import wraps
import mysql.connector
import pickle
import pandas as pd
import requests #new

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'MO'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#model
movies_dict = pickle.load(open('movies_dict.pkl','rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl','rb'))

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:13]

    recommended_movies = []
    recommended_movies_posters = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id

        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies,recommended_movies_posters

def fetch_poster(movie_id):
    response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=bc40eaab70b5fdf4aafa14df3e3dfc39'.format(movie_id))
    data = response.json()
    return "https://image.tmdb.org/t/p/w500/" + data['poster_path']


def mo_details(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    print(movies.info)
    return movie_index


##### model unto this point #########
mysql =MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

class RegisterForm(Form):
    Name = StringField('Name', [validators.Length(min =1, max = 100)])
    Username = StringField('Username', [validators.Length(min= 1, max = 80)])
    Email = StringField('Email', [validators.Length(min =1, max =100)])
    Phone_Number = IntegerField('Phone Number')
    Password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('confirm Password')


@app.route('/Register', methods=['GET', 'POST'])
def Register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        Name = form.Name.data
        Username = form.Username.data
        Email = form.Email.data
        Phone_Number = form.Phone_Number.data
        Password = sha256_crypt.encrypt(str(form.Password.data))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Register(Name, Username, Email, Phone_Number, Password) VALUES(%s, %s, %s, %s, %s)",
                    (Name,Username,Email,Phone_Number,Password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('Register'))
    return render_template('Register.html', form = form)


@app.route('/Login', methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM Register WHERE Username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['Password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('Login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('Login.html', error=error)

    return render_template('Login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('index'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))



@app.route('/dashboard',methods=['GET', 'POST'])
def dashboard():
    mn = "Nothing has been selected"
    recommendations = ["No Recommendations for you, yet"]
    posters = ['']
    if request.method == 'POST':
        # Get Form Fields
        mn = request.form['moto']
        recommendations,posters = recommend(mn)
        # print(mo_details(mn))

    return render_template('dashboard.html',at = mn, recommendations = recommendations, posters = posters)


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
