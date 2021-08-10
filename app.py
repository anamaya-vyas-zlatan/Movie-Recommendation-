from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, IntegerField, ValidationError, \
    DateField, SubmitField
from passlib.hash import sha256_crypt
from functools import wraps
import mysql.connector
import pickle
import pandas as pd
import requests  # new
import jinja2

env = jinja2.Environment()
env.globals.update(zip=zip)
# use env to load template(s)



app= Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'MO'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# model
movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))


# mo_read = pd.read_csv('tmdb_5000_movies.csv')

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:7]

    recommended_movies = []
    recommended_movies_posters = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_movies_posters


def fetch_poster(movie_id):
    response = requests.get(
        'https://api.themoviedb.org/3/movie/{}?api_key=bc40eaab70b5fdf4aafa14df3e3dfc39'.format(movie_id))
    data = response.json()
    return "https://image.tmdb.org/t/p/w500/" + data['poster_path']


def mo_details(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    movie_id = movies.iloc[movie_index].movie_id
    return movie_id


def movie_overview(movie_id):
    response = requests.get(
        'https://api.themoviedb.org/3/movie/{}?api_key=bc40eaab70b5fdf4aafa14df3e3dfc39'.format(movie_id))
    data = response.json()
    g = data['genres']
    genres = [x['name'] for x in g]
    return data['overview'], data['budget'], data['vote_average'], genres


# movie_names = movies.loc[movies.title]
arr = movies["title"].tolist()

##### model unto this point #########
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')


class RegisterForm(Form):
    Name = StringField('Name', [validators.Length(min=1, max=100)])
    Username = StringField('Username', [validators.Length(min=1, max=80)])
    Email = StringField('Email', [validators.Length(min=1, max=100)])
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
                    (Name, Username, Email, Phone_Number, Password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('Login'))
    return render_template('Register.html', form=form)


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
    movie_name_atc.clear()
    overview_atc.clear()
    pic_atc.clear()
    cost_atc.clear()
    movie_id_atc.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

def maketuple(movie, poster):
    a = len(movie)
    list = []
    for i in range(a):
        l = (movie[i], poster[i])
        list.append(l)
    return list

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    mn = "Nothing has been selected"
    recommendations = ["No Recommendations for you, yet"]
    posters = ['']
    genres = ['']
    overview = ""
    budget = 0
    pic = ''
    vote_average = 0
    if request.method == 'POST':
        # Get Form Fields
        mn = request.form['moto']
        recommendations, posters = recommend(mn)
        mi = mo_details(mn)
        overview, budget, vote_average, genres = movie_overview(mi)
        pic = fetch_poster(mi)
        session["mn"] = mn
        session["ov"] = overview
        session["pc"] = pic
        list = maketuple(recommendations,posters)
        # id_atc = mo_details(mn)
        # print(pic_atc)
        # print(movie_name_atc)
        # print(cost_atc)
        # print(overview_atc)
        # print(movie_id_atc)   #return render_template('form_result.html',type=type,reqIDs_msgs_rcs=zip(IDs,msgs,rcs))
        print(list)
    return render_template('dashboard.html', overview=overview, budget=budget, genres=genres,
                           vote_average=vote_average, at=mn,recommendations=recommendations, posters=posters, pic=pic,
                           arr= arr)
    # return render_template('dashboard.html',verview=overview, budget=budget, genres=genres,
    #                        vote_average=vote_average, at=mn,lallu = zip(recommendations, posters), pic=pic,
    #                        arr= arr)

@app.template_global(name='zip')
def _zip(*args, **kwargs): #to not overwrite builtin zip in globals
    return __builtins__.zip(*args, **kwargs)


#### add to card #####
movie_name_atc = []
overview_atc = []
pic_atc = []
cost_atc = []
movie_id_atc = []

@app.route('/add_movie/<string:recommendations>', methods=['POST'])
def add_movie(recommendations):
    check1 = in_db(recommendations)
    check2 = in_cart(recommendations)
    if (check2 == 0 or check1 == 0):
        return render_template('viewcart.html')
    else:
        mo_id = mo_details(recommendations)
        mo_ov,mtv,mz,ml = movie_overview(mo_id)
        mp = fetch_poster(mo_id)
        movie_name_atc.append(recommendations)
        overview_atc.append(mo_ov)
        pic_atc.append(mp)
        cost_atc.append("Rs.100")
        movie_id_atc.append(mo_id)
        return redirect(url_for('viewcart'))

def in_db(movie):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT Movie_Name From MOVIES WHERE Username = (%s)", (session['username'],))
    ok = cur.fetchall()
    q = []
    print(result)
    for i in ok:
        q.append(i)
    m = [d['Movie_Name'] for d in q]
    flag = 1
    for d in m:
        if (d == movie):
            flag = 0
            break
    return flag


def in_cart(movie):
    flag = 1
    for d in movie_name_atc:
        if (d == movie):
            flag = 0
            break
    return flag


@app.route('/viewcart')
def viewcart():
    at = True
    mname = movie_name_atc
    mov = overview_atc
    mpc = pic_atc
    c = cost_atc
    mid = movie_id_atc
    lent = len(movie_id_atc)
    totat_cost = 100 * lent
    if lent == 0:
        at = False
    return render_template('viewcart.html', at=at, mname=mname, mov=mov, mpc=mpc, c=c, mid=mid, totat_cost=totat_cost)


# @app.route('/add_to_cart')
# def add_to_cart():
#     id_atc = mo_details(session["mn"])
#     pic = session["pc"]
#     movie_name_atc.append(session["mn"])
#     overview_atc.append(session["ov"])
#     pic_atc.append(pic)
#     cost_atc.append("Rs.100")
#     movie_id_atc.append(id_atc)
#     return redirect(url_for('dashboard'))

@app.route('/add_to_cart')
def add_to_cart():
    n = session["mn"]
    check1 = in_db(n)
    check2 = in_cart(n)
    if(check2==0 or check1 ==0):
        return render_template('viewcart.html')
    else:
        id_atc = mo_details(session["mn"])
        pic = session["pc"]
        movie_name_atc.append(session["mn"])
        overview_atc.append(session["ov"])
        pic_atc.append(pic)
        cost_atc.append("Rs.100")
        movie_id_atc.append(id_atc)
        return redirect(url_for('viewcart'))


@app.route('/delete_from_cart/<string:mname>', methods=['POST'])
def delete_from_cart(mname):
    index = movie_name_atc.index(mname)
    movie_name_atc.pop(index)
    overview_atc.pop(index)
    pic_atc.pop(index)
    cost_atc.pop(index)
    movie_id_atc.pop(index)
    return redirect(url_for('viewcart'))



#### add to cart over #######

#######  payment ############
@app.route('/payment')
@is_logged_in
def payment():
    index = len(movie_id_atc)
    ans = index * 100
    return render_template('payment.html', ans=ans)


@app.route('/make_payment')
def make_payment():
    index = len(movie_id_atc)
    l = []
    for i in range(index):
        m_name = movie_name_atc[i]
        m_id = movie_id_atc[i]
        m_overview = overview_atc[i]
        m_pic = pic_atc[i]
        username = session['username']
        a = (username, m_name, m_id, m_pic, m_overview)
        l.append(a)
    cur = mysql.connection.cursor()
    cur.executemany(
        "INSERT INTO Movies(Username, Movie_Name, Movie_Id, Movie_Pic_Link, Movie_Overview) VALUES(%s, %s, %s, %s, %s)",
        l)
    mysql.connection.commit()
    cur.close()
    movie_name_atc.clear()
    overview_atc.clear()
    pic_atc.clear()
    cost_atc.clear()
    movie_id_atc.clear()
    return redirect(url_for('dashboard'))


################## payment part is over ######################

################## show rented movies #################
@app.route('/purchasedmovies')
def purchasedmovies():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM MOVIES WHERE Username = (%s)", (session['username'],))
    ok = cur.fetchall()
    at = False
    if result > 0:
        at = True
        mysql.connection.commit()
        cur.close()
        return render_template('purchasedmovies.html', ok=ok, at=at)
    else:
        return render_template('purchasedmovies.html', at=at)


if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
