from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    
    # Corrected: Added the widget=TextArea() to ensure it renders as a box, not a single line
    body = TextAreaField('Body', validators=[DataRequired()], widget=TextArea())
    
    # Note: FileAllowed is used here. 
    # If you want to FORCE an image upload, add FileRequired() to the list below.
    image_path = FileField('Image', validators=[
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    
    submit = SubmitField('Save')