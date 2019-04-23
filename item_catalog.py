from flask import Flask, render_template, request, redirect, jsonify, \
 url_for,  flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool
from database_setup import Category, Book, User, Base
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open(
                 'client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database
engine = create_engine('sqlite:///books_catalog.db',
                       connect_args={'check_same_thread': False})

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('user is connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    return redirect('/catalog')

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except():
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Fail to revoke token.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if login_session['provider'] == 'google':
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']

    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['provider']

    return redirect(url_for('showCatalog'))


@app.route('/catalog/JSON')
def showCategoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])


# JSON API to show category info
@app.route('/catalog/<int:catalog_id>/JSON')
@app.route('/catalog/<int:catalog_id>/books/JSON')
def showCategoryJSON(catalog_id):
    books = session.query(Book).filter_by(category_id=catalog_id).all()
    return jsonify(books=[book.serialize for book in books])


# JSON API to show book info
@app.route('/catalog/<int:catalog_id>/books/<int:book_id>/JSON')
def showBookJSON(catalog_id, book_id):
    book = session.query(Book).filter_by(id=book_id).first()
    return jsonify(book=[book.serialize])


@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Category).all()
    return render_template('catalogs.html', categories=categories)


@app.route('/catalog/<int:category_id>/books')
def showBooks(category_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Book).filter_by(category_id=category_id).order_by(
                                                        asc(Book.name))
    return render_template('items.html', items=items,
                           categories=categories, category=category)


@app.route('/catalog/<int:category_id>/books/<int:item_id>')
def showBookInfo(category_id, item_id):
    items = session.query(Book).filter_by(category_id=category_id).all()
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Book).filter_by(id=item_id).one()
    return render_template('iteminfo.html', item=item,
                           items=items, category=category)


@app.route('/catalog/<int:category_id>/genre/new', methods=['GET', 'POST'])
def newBook(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newitem = Book(name=request.form['name'],
                       description=request.form['desc'],
                       category_id=category_id,
                       user_id=login_session['user_id'])
        session.add(newitem)
        session.commit()
        return redirect(url_for('showBooks', category_id=category_id))

    else:
        return render_template('newitem.html', category=category)


@app.route('/catalog/<int:category_id>/book/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editBook(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    book = session.query(Book).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            book.name = request.form['name']
        if request.form['desc']:
            book.description = request.form['desc']
        session.add(book)
        session.commit()
        return redirect(url_for('showBooks', category_id=category_id))

    else:
        return render_template('edititem.html', book=book)


@app.route('/catalog/<int:category_id>/book/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteBook(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')

    book = session.query(Book).filter_by(id=item_id).one()

    # Get creator of book
    creator = getUserInfo(book.user_id)

    # Check if logged in user is creator of book
    if creator.id != login_session['user_id']:
        return redirect('/login')

    if request.method == 'POST':
        session.delete(book)
        session.commit()
        return redirect(url_for('showBooks', category_id=category_id))
    else:
        return render_template('deleteitem.html', book=book)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
