"""
Routes and views for the Flask application.
"""

from datetime import datetime
from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from config import Config
from FlaskWebProject import app, db
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
import msal
import uuid

# Blob storage URL prefix
imageSourceUrl = (
    'https://' + app.config['BLOB_ACCOUNT'] +
    '.blob.core.windows.net/' +
    app.config['BLOB_CONTAINER'] + '/'
)

@app.route('/')
@app.route('/home')
@login_required
def home():
    posts = Post.query.all()
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files['image_path'], current_user.id, new=True)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.get(int(id))
    form = PostForm(formdata=request.form, obj=post)
    if form.validate_on_submit():
        post.save_changes(form, request.files['image_path'], current_user.id)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            app.logger.warning("Invalid login attempt (username/password)")
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        app.logger.info("admin logged in successfully (username/password)")

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)

    # Microsoft Login
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])

    return render_template(
        'login.html',
        title='Sign In',
        form=form,
        auth_url=auth_url
    )

# --- CORRECTED: Added @ symbol and forced HTTPS logic ---
@app.route(Config.REDIRECT_PATH, methods=['GET', 'POST'])
def authorized():
    # Force the redirect URI to be HTTPS to match Azure App Registration
    manual_redirect_uri = url_for('authorized', _external=True)
    if manual_redirect_uri.startswith('http://'):
        manual_redirect_uri = manual_redirect_uri.replace('http://', 'https://', 1)

    if request.args.get('state') != session.get("state"):
        app.logger.warning("OAuth state mismatch detected")
        return redirect(url_for("login"))

    if "error" in request.args:
        app.logger.warning("Microsoft login failed")
        return render_template("auth_error.html", result=request.args)

    if "code" in request.args:
        cache = _load_cache()
        msal_app = _build_msal_app(cache=cache)

        result = msal_app.acquire_token_by_authorization_code(
            request.args['code'],
            scopes=Config.SCOPE,
            redirect_uri=manual_redirect_uri # Use HTTPS manual URI
        )

        if "error" in result:
            app.logger.warning(f"Token exchange error: {result.get('error_description')}")
            return render_template("auth_error.html", result=result)

        session["user"] = result.get("id_token_claims")

        # SAFETY CHECK: Ensure the admin user exists in your local DB
        user = User.query.filter_by(username="admin").first()
        if user:
            login_user(user)
            app.logger.info("admin logged in successfully via Microsoft OAuth")
            _save_cache(cache)
        else:
            flash("User 'admin' does not exist in the local database. Please create it first.")
            return redirect(url_for('login'))

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    logout_user()
    if session.get("user"):
        session.clear()
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout"
            + "?post_logout_redirect_uri="
            + url_for("login", _external=True)
        )
    return redirect(url_for('login'))

# =========================
# MSAL helper functions (Corrected)
# =========================

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        client_id=Config.CLIENT_ID,
        client_credential=Config.CLIENT_SECRET,
        authority=authority or Config.AUTHORITY,
        token_cache=cache
    )

def _build_auth_url(authority=None, scopes=None, state=None):
    msal_app = _build_msal_app(authority=authority)
    
    # Force the initial login link to use HTTPS manual URI
    manual_redirect_uri = url_for('authorized', _external=True)
    if manual_redirect_uri.startswith('http://'):
        manual_redirect_uri = manual_redirect_uri.replace('http://', 'https://', 1)
        
    return msal_app.get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=manual_redirect_uri
    )