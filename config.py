import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'super-mega-secret-key'

OAUTH_CREDENTIALS = {
    'facebook': {
        'id': '558983587537942',
        'secret': 'a81cff040b37a9be6cc4f1dde64aed26'
    },
    'google': {
        'id': '2993980776-9iv8c93asdlgnmh9v0knhsvl24jvrv98.apps.googleusercontent.com',
        'secret': 'jUvNT7IGcGqvHTrG_z1k3tYI'
    }
}

if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

ADMINS = ['ankimv@gmail.com']
POSTS_PER_PAGE = 10
