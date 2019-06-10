# -*- coding: utf-8 -*-
""" Module with the

This module has ......................:
    - ....;
"""

from flask import Flask, jsonify, render_template, request, flash, make_response
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, CategoryItem, User
import json
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import requests

# Create an instance of the Flask class with it's name
app = Flask(__name__)

# Enable CSRF protection globally for a Flask app
#csrf = CSRFProtect(app)

# Google's Client ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Name of the application at Google
APPLICATION_NAME = "Item Catalog"

# Connect to Database
engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine

# Create database session
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Connect to Google Account
@app.route('/google_connect', methods=['POST'])
def google_connect():
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
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
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
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    output = 'ok'
    return output

# Disconnect from Google Account
@app.route('/google_disconnect')
def google_disconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['google_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully disconnected!")
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        flash("Failed to disconnected!")
    return render_template('logout.html', response=response)

# Create a json with all informations about categories and items
@app.route('/catalog.json')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[cat.serialize for cat in categories])

# Create a json with all informations about users
@app.route('/users.json')
def usersJSON():
    users = session.query(User).all()
    return jsonify(users=[user.serialize for user in users])

# Show all Categories
@app.route('/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    latest_items = []
    if 'username' not in login_session:
        return render_template('categories.html', categories=categories)
    else:
        return render_template('auth_categories.html', categories=categories)

# Create a new category
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCategory():
    pass

# Edit a category
@app.route('/catalog/<category_name>/edit/', methods=['GET', 'POST'])
def editCategory(category_name):
    pass

# Delete a category
@app.route('/catalog/<category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    pass

# Show the items of the category
@app.route('/catalog/<category_name>/items/')
def showItems(category_name):
    pass

# Create a new item
@app.route('/catalog/<category_name>/items/new/', methods=['GET', 'POST'])
def newCategoryItem(category_name):
    pass

# Edit a category item
@app.route('/catalog/<category_name>/items/<item_name>/edit', methods=['GET', 'POST'])
def editCategoryItem(category_name, item_name):
    pass

# Delete a category item
@app.route('/catalog/<category_name>/items/<item_name>/delete', methods=['GET', 'POST'])
def deleteCategoryItem(category_name, item_name):
    pass

# Show specific item
@app.route('/catalog/<category_name>/<item_name>')
def showItem(category_name, item_name):
    pass

# Get User id, search the e-mail
def getUserId(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

# Get User Information
def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

# Create New User with info of Google Account
def createUser(login_session):
    newUser = User(
        name = login_session['username'],
        email = login_session['email'],
        picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

if __name__ == '__main__':
    app.secret_key = '##THIS_IS_THE_SECRET_KEY_FOR_THIS_APPLICATION##'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
