import psycopg2
from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Item, User
from flask import session as login_session
import string
import random

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read()
)['web']['client_id']
app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route(
    '/categories/<int:category_id>/item/<int:catalog_item_id>/JSON')
def itemJSON(category_id, catalog_item_id):
    """JSON of specific item in catalog"""
    item = session.query(Item).filter_by(
        catalog_item_id=catalog_item_id
        ).one()
    return jsonify(Item=item.serialize)


@app.route(
    '/categories/<int:category_id>/items/JSON')
def itemCategoryJSON(category_id):
    """JSON of all items of a given category"""
    items = session.query(Item).filter_by(
        catalog_item_category_id=category_id
        ).all()
    return jsonify(Item=[item.serialize for item in items])


@app.route('/catalog.json')
def showCatalogJSON():
    """JSON of all items"""
    items = session.query(Item).all()
    return jsonify(Item=[item.serialize for item in items])


@app.route('/categories.json')
def categoriesJSON():
    """JSON of all categories"""
    categories = session.query(Category).all()
    return jsonify(Category=[category.serialize for category in categories])


@app.route('/login')
def showLogin():
    """show the login page"""
    state = ''.join(
        random.choice(string.ascii_uppercase+string.digits) for x in xrange(32)
        )
    login_session['state'] = state
    return render_template(
        'login.html',
        STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Gathers data from Google Sign In API
    and places it inside a session variable.
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    return output


def login_required(f):
    """
    Check if current user is loged in
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/gdisconnect')
def gdisconnect():
    """
    Disconnect current logged in google users, clean the info stored in session
    """
    access_token = login_session['access_token']

    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'),
            401
        )
        response.headers['Content-Type'] = 'application/json'
        return response

    requests.post(
        'https://accounts.google.com/o/oauth2/revoke',
        params={'token': login_session['access_token']},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )

    if login_session['access_token'] is not None:
        # reset the user's session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        return redirect(url_for('showLogin'))

    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


def getUserInfo(user_id):
    """
    Get the user from db using user_id
    """
    user = session.query(User).filter_by(user_id=user_id).one()
    return user


def getUserID(email):
    """
    Get the user is from db using a unique email
    """
    try:
        user = session.query(User).filter_by(user_email=email).one()
        return user.user_id
    except:
        return None


def createUser(login_session):
    """
    Add the new user to db if it is the first time logging in
    """
    newUser = User(
        user_name=login_session['username'],
        user_email=login_session['email']
    )
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
        user_email=login_session['email']
        ).one()
    return user.user_id


@app.route('/')
@app.route('/categories/')
def showCatalog():
    """
    Homepage of the Catalog, show a list of categories
    """
    categories = session.query(Category).all()
    return render_template(
        'home.html',
        categories=categories,
        isLogedIn='access_token' in login_session
        )


@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showItems(category_id):
    """
    Show all the items of a given category
    """
    category = session.query(Category).filter_by(category_id=category_id).one()
    items = session.query(Item).filter_by(catalog_item_category_id=category_id)
    categories = session.query(Category).all()
    isLogedIn = 'access_token' in login_session
    return render_template(
        'items_list.html',
        categories=categories,
        category=category,
        items=items,
        isLogedIn=isLogedIn)


@app.route('/categories/item/new/<int:category_id>/', methods=['GET', 'POST'])
@login_required
def newItem(category_id):
    """
    Add a new item to db if current user is valid
    """
    categories = session.query(Category).all()
    if request.method == 'POST':
        newItem = Item(
            catalog_item_name=request.form['name'],
            catalog_item_description=request.form['description'],
            catalog_item_category_id=category_id,
            user_id=login_session['user_id']
        )
        session.add(newItem)
        session.commit()

        return redirect(url_for('showItems', category_id=category_id))
    else:
        isLogedIn = 'access_token' in login_session
        return render_template(
            'new_item.html',
            isLogedIn=isLogedIn,
            categories=categories,
            category_id=category_id
        )


@app.route(
    '/categories/<int:category_id>/item/<int:catalog_item_id>/edit',
    methods=['GET', 'POST'])
@login_required
def updateItem(category_id, catalog_item_id):
    """
    Update an item's name or description if current user is valid
    """
    editedItem = session.query(Item).filter_by(
        catalog_item_id=catalog_item_id
        ).one()
    category = session.query(Category).filter_by(category_id=category_id).one()

    if (
        request.method == 'POST' and
        login_session['user_id'] == editedItem.user_id and
        'access_token' in login_session
       ):
        if request.form['name']:
            editedItem.catalog_item_name = request.form['name']
        if request.form['description']:
            editedItem.catalog_item_description = request.form['description']
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        isLogedIn = 'access_token' in login_session
        return render_template(
            'update_item.html',
            category=category,
            item=editedItem,
            isLogedIn=isLogedIn)


@app.route(
    '/categories/<int:category_id>/item/<int:catalog_item_id>/delete',
    methods=['GET'])
@login_required
def deleteItem(category_id, catalog_item_id):
    """
    Delete an item with given item id
    """
    itemToDelete = session.query(Item).filter_by(
        catalog_item_id=catalog_item_id
    ).one()
    if (
        login_session['user_id'] == itemToDelete.user_id and
        'access_token' in login_session
    ):
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return redirect(url_for('showLogin'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
