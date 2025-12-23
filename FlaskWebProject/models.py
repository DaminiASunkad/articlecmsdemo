from datetime import datetime
from FlaskWebProject import app, db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from azure.storage.blob import BlobServiceClient
import string, random
from werkzeug.utils import secure_filename
from flask import flash

# Get configuration from config.py
blob_container = app.config['BLOB_CONTAINER']
storage_url = f"https://{app.config['BLOB_ACCOUNT']}.blob.core.windows.net"

# Initialize the modern v12 Client
blob_service_client = BlobServiceClient(
    account_url=storage_url, 
    credential=app.config['BLOB_STORAGE_KEY']
)

def id_generator(size=32, chars=string.ascii_uppercase + string.digits):
    """Generates a random string for unique filenames."""
    return ''.join(random.choice(chars) for _ in range(size))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    author = db.Column(db.String(75))
    body = db.Column(db.String(800))
    image_path = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

    def save_changes(self, form, file, userId, new=False):
        self.title = form.title.data
        self.author = form.author.data
        self.body = form.body.data
        self.user_id = userId

        if file:
            filename = secure_filename(file.filename)
            fileextension = filename.rsplit('.', 1)[1]
            random_filename = id_generator()
            filename = random_filename + '.' + fileextension
            
            try:
                # v12 logic: Get a client for this specific file
                blob_client = blob_service_client.get_blob_client(container=blob_container, blob=filename)
                
                # Upload the file stream directly to Azure
                blob_client.upload_blob(file, overwrite=True)

                # If editing an existing post, delete the old image from Azure
                if self.image_path:
                    try:
                        old_blob_client = blob_service_client.get_blob_client(container=blob_container, blob=self.image_path)
                        old_blob_client.delete_blob()
                    except Exception:
                        pass # Ignore if the old file doesn't exist
                
                self.image_path = filename
            except Exception as e:
                flash(f"Blob upload failed: {str(e)}")
                
        if new:
            db.session.add(self)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Database error: {str(e)}")