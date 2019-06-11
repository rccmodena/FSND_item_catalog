# -*- coding: utf-8 -*-
""" Module with the all the function to run the web server

This module has 16 functions:
    - showLogin();
    - google_connect();
    - google_disconnect();
    - catalogJSON();
    - showCategories();
    - newCategory();
    - editCategory(category_name);
    - deleteCategory(category_name);
    - showItems(category_name);
    - newCategoryItem(category_name);
    - showItem(category_name, item_title);
    - editCategoryItem(category_name, item_title);
    - deleteCategoryItem(category_name, item_title);
    - getUserId(email);
    - getUserInfo(user_id);
    - createUser(login_session);

Running this file will start the web server.
"""

from flask import Flask, jsonify, render_template, request
from flask import flash, make_response, redirect, url_for
from flask_wtf.csrf import CSRFProtect
from models import app, db, Category, CategoryItem, User
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import json
import httplib2
import requests

# Google's Client ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

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
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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
    # Verify if there is a token
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token={token}'
    url = url.format(token=login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    # Verify if the account was successfuly disconnected
    if result['status'] == '200':
        # delete the information about the user in the login_session
        del login_session['access_token']
        del login_session['google_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully disconnected!")
    else:
        # delete the information about the user in the login_session
        del login_session['access_token']
        del login_session['google_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        flash("Failed to disconnected!")
    return render_template('logout.html', response=response)


# Create a json with all informations about categories and items
@app.route('/catalog.json')
def catalogJSON():
    catalog = {'Category': []}
    categories = Category.query.all()
    for category in categories:
        categ_items = category.serialize
        items = CategoryItem.query.filter_by(cat_id=category.id).all()
        categ_items['Items'] = [item.serialize for item in items]
        catalog['Category'].append(categ_items)
    return jsonify(catalog)


# Show all Categories
@app.route('/')
def showCategories():
    categories = Category.query.order_by(Category.name.asc()).all()

    # Create a list of dictionaries with 5 latest item created.
    latest_items = []
    for item in CategoryItem.query.order_by(CategoryItem.id.desc()).limit(5):
        latest_items.append(
            {'Title': item.title,
             'Category': Category.query.filter_by(
                id=item.cat_id).first().name})

    # Verify if a user not is logged
    if 'username' not in login_session:
        return render_template(
            'categories.html',
            categories=categories,
            latest_items=latest_items)

    # Enable CRUD operations
    else:
        return render_template(
            'auth_categories.html',
            categories=categories,
            latest_items=latest_items)


# Create a new category
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCategory():
    # Verify if a user is logged
    if 'username' not in login_session:
        return redirect('/login')

    # Execute if is a POST method
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'],
            user_id=login_session['user_id'])
        db.session.add(newCategory)
        db.session.commit()
        flash('New Category %s Successfully Created!' % newCategory.name)
        return redirect(url_for('showCategories'))

    # Execute if is a GET method
    else:
        return render_template('new_category.html')


# Edit a category
@app.route('/catalog/<category_name>/edit/', methods=['GET', 'POST'])
def editCategory(category_name):
    # Verify if a user is logged
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = Category.query.filter_by(name=category_name).first()

    # Verify if the category was created by the current user
    if editedCategory.user_id != login_session['user_id']:
        return render_template(
            'not_authorized.html',
            msg='You are not authorized to edit this category!')

    # Execute if is a POST method
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            db.session.commit()
            flash('Category Successfully Edited %s!' % editedCategory.name)
        return redirect(url_for(
            'showItems', category_name=editedCategory.name))

    # Execute if is a GET method
    else:
        return render_template('edit_category.html', category=editedCategory)


# Delete a category
@app.route('/catalog/<category_name>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_name):
    # Verify if a user is logged
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = Category.query.filter_by(name=category_name).first()

    # Verify if the category was created by the current user
    if categoryToDelete.user_id != login_session['user_id']:
        return render_template(
            'not_authorized.html',
            msg='You are not authorized to delete this category!')

    # Execute if is a POST method
    if request.method == 'POST':
        db.session.delete(categoryToDelete)
        db.session.commit()
        flash('%s Successfully Deleted' % categoryToDelete.name)
        return redirect(url_for('showCategories'))

    # Execute if is a GET method
    else:
        return render_template(
            'delete_category.html', category=categoryToDelete)


# Show the items of the category
@app.route('/catalog/<category_name>/items/')
def showItems(category_name):
    categories = Category.query.order_by(Category.name.asc()).all()
    category = Category.query.filter_by(name=category_name).first()
    category_items = CategoryItem.query.filter_by(
        cat_id=category.id).order_by(CategoryItem.title.asc()).all()

    # Verify if a user not is logged
    if 'username' not in login_session:
        return render_template(
            'items.html',
            categories=categories,
            category=category,
            category_items=category_items)

    # Enable CRUD operations
    else:
        return render_template(
            'auth_items.html',
            categories=categories,
            category=category,
            category_items=category_items)


# Create a new item
@app.route('/catalog/<category_name>/items/new/', methods=['GET', 'POST'])
def newCategoryItem(category_name):
    # Verify if a user is logged
    if 'username' not in login_session:
        return redirect('/login')
    categories = Category.query.order_by(Category.name.asc()).all()

    # Execute if is a POST method
    if request.method == 'POST':
        category = Category.query.filter_by(
            name=request.form['select_category']).first()
        newCategoryItem = CategoryItem(
            title=request.form['title'],
            description=request.form['description'],
            cat_id=category.id,
            user_id=login_session['user_id'])
        db.session.add(newCategoryItem)
        db.session.commit()
        flash('New Item %s Successfully Created!' % newCategoryItem.title)
        return redirect(url_for('showItems', category_name=category.name))

    # Execute if is a GET method
    else:
        category = Category.query.filter_by(name=category_name).first()
        return render_template(
            'new_item.html',
            categories=categories,
            category=category)


# Show specific item
@app.route('/catalog/<category_name>/<item_title>')
def showItem(category_name, item_title):
    category = Category.query.filter_by(name=category_name).first()
    item = CategoryItem.query.filter_by(
        title=item_title, cat_id=category.id).first()

    # Verify if a user not is logged
    if 'username' not in login_session:
        return render_template('item.html', category=category, item=item)

    # Enable CRUD operations
    else:
        return render_template('auth_item.html', category=category, item=item)


# Edit a category item
@app.route(
    '/catalog/<category_name>/items/<item_title>/edit',
    methods=['GET', 'POST'])
def editCategoryItem(category_name, item_title):
    # Verify if a user is logged
    if 'username' not in login_session:
        return redirect('/login')
    categories = Category.query.order_by(Category.name.asc()).all()
    editedItem = CategoryItem.query.filter_by(title=item_title).first()

    # Verify if the item was created by the current user
    if editedItem.user_id != login_session['user_id']:
        return render_template(
            'not_authorized.html',
            msg='You are not authorized to edit this item!')

    # Execute if is a POST method
    if request.method == 'POST':
        category = Category.query.filter_by(
            name=request.form['select_category']).first()
        editedItem.title = request.form['title']
        editedItem.description = request.form['description']
        editedItem.cat_id = category.id
        db.session.commit()
        flash('Item Successfully Edited %s!' % editedItem.title)
        return redirect(url_for('showItems', category_name=category.name))

    # Execute if is a GET method
    else:
        category = Category.query.filter_by(name=category_name).first()
        return render_template(
            'edit_item.html',
            item=editedItem,
            category=category,
            categories=categories)


# Delete a category item
@app.route(
    '/catalog/<category_name>/items/<item_title>/delete',
    methods=['GET', 'POST'])
def deleteCategoryItem(category_name, item_title):
    # Verify if a user is logged
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = CategoryItem.query.filter_by(title=item_title).first()
    category = Category.query.filter_by(name=category_name).first()

    # Verify if the item was created by the current user
    if itemToDelete.user_id != login_session['user_id']:
        return render_template(
            'not_authorized.html',
            msg='You are not authorized to delete this item!')

    # Execute if is a POST method
    if request.method == 'POST':
        db.session.delete(itemToDelete)
        db.session.commit()
        flash('%s Successfully Deleted' % itemToDelete.title)
        return redirect(url_for(
            'showItems',
            category_name=category_name,
            item_title=itemToDelete.title))

    # Execute if is a GET method
    else:
        return render_template(
            'delete_item.html',
            item=itemToDelete,
            category=category)


# Get User id, search the e-mail
def getUserId(email):
    try:
        user = User.query.filter_by(email=email).first()
        return user.id
    except:
        return None


# Get User Information
def getUserInfo(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user


# Create New User with info of Google Account
def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    db.session.add(newUser)
    db.session.commit()
    user = User.query.filter_by(email=login_session['email']).first()
    return user.id


# If run this module will start the server.
if __name__ == '__main__':
    app.secret_key = '##THIS_IS_THE_SECRET_KEY_FOR_THIS_APPLICATION##'
    app.debug = False
    app.run(host='0.0.0.0', port=8000)
