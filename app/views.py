from flask import render_template, flash, redirect, url_for, request, session, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import EditForm, PostForm
from models import User, ROLE_USER, ROLE_ADMIN, Post
from config import POSTS_PER_PAGE
from datetime import datetime
from oauth import OAuthSignIn
import uuid

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET', 'POST'])
@login_required
def index(page = 1):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body = form.post.data, timestamp = datetime.utcnow(), author = current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))
    posts = current_user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
    return render_template('index.html',
            title = 'Home',
            form = form,
            posts = posts)

@app.route('/users/<int:page>')
@login_required
def users(page = 1):
    users_list = User.query.paginate(page, POSTS_PER_PAGE, False)
    return render_template('users.html',
            title='List of users',
            users_list = users_list)

@app.route('/delete/<int:post_id>/<secret_id>')
@login_required
def delete_post(post_id, secret_id):
    if current_user.is_anonymous():
        return redirect(url_for('index'))
    post = Post.query.get(post_id)
    if secret_id != session.get('secret_key', None):
        abort(400)
    if post.author.id == current_user.id:
        db.session.delete(post)
        db.session.commit()
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if current_user.is_authenticated():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if current_user.is_authenticated():
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    nickname, email = oauth.callback()
    if email is None:
        flash('Authentication failed')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = email).first()
    if not user:
        user = User(nickname = User.make_unique_nickname(nickname), email = email)
        db.session.add(user)
        db.session.commit()
        db.session.add(user.follow(user))
        db.session.commit()
    session['secret_key'] = uuid.uuid4().hex
    login_user(user, True)
    return redirect(url_for('index'))

@app.route('/login')
def login():
    if current_user.is_authenticated():
        return redirect(url_for('index'))
    return render_template('login.html',
            title = 'Sign in')

@app.route('/logout')
def logout():
    session.pop('secret_key', None)
    logout_user()
    return redirect(url_for('index'))

@app.route('/delete_account/<int:id>/<secret_id>')
@login_required
def delete_account(id, secret_id):
    if not current_user.id == id:
        return redirect(url_for('index'))
    user = User.query.get(id)
    if secret_id != session.get('secret_key', None):
        abort(400)
    for post in user.posts:
        db.session.delete(post)
    db.session.delete(user)
    db.session.commit()
    logout_user()
    flash('Your account has been deleted')
    return redirect(url_for('login'))

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page = 1):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('user.html',
            title = nickname,
            user = user,
            posts = posts)

@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditForm(current_user.nickname)
    if form.validate_on_submit():
        current_user.nickname = form.nickname.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = current_user.nickname
        form.about_me.data = current_user.about_me
        return render_template('edit.html',
                form = form)

@app.route('/follow/<nickname>/<secret_id>')
@login_required
def follow(nickname, secret_id):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can\'t follow yourself!')
        return redirect(url_for('user', nickname = nickname))
    if secret_id != session.get('secret_key', None):
        abort(400)
    u = current_user.follow(user)
    if u is None:
        flash('Cannot follow ' + nickname)
        return redirect(url_for('user', nickname = nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + nickname + '!')
    return redirect(url_for('user', nickname = nickname))

@app.route('/unfollow/<nickname>/<secret_id>')
@login_required
def unfollow(nickname, secret_id):
    user = User.query.filter_by(nickname = nickname).first()
    if user == None:
        flash('User ' + nickname + ' not found')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('user', nickname = nickname))
    if secret_id != session.get('secret_key', None):
        abort(400)
    u = current_user.unfollow(user)
    if u is None:
        flash('Cannot follow ' + nickname)
        return redirect(url_for('user', nickname = nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have unfollowed ' + nickname + '!')
    return redirect(url_for('user', nickname = nickname))
