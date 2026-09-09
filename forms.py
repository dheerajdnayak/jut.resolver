from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField, RadioField, HiddenField, FloatField
from wtforms.validators import DataRequired, Length, ValidationError, Optional, NumberRange

class StudentPostForm(FlaskForm):
    jut_number = StringField('JUT #', validators=[DataRequired(), Length(max=50)])
    subject = SelectField('Subject', choices=[
        ('phy', 'Physics'),
        ('chem', 'Chemistry'),
        ('maths', 'Mathematics')
    ], validators=[DataRequired()])
    text_content = TextAreaField('Additional Text (optional)')
    image = FileField('Question Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Submit Question')

class LecturerLoginForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class LecturerSignupForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    subject = SelectField('Subject', choices=[
        ('phy', 'Physics'),
        ('chem', 'Chemistry'),
        ('maths', 'Mathematics')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_confirm(self, field):
        if field.data != self.password.data:
            raise ValidationError('Passwords must match')

class VoteForm(FlaskForm):
    post_id = HiddenField()
    option = RadioField('Select option', choices=[
        ('GRACE', 'GRACE'),
        ('1', '1)'),
        ('2', '2)'),
        ('3', '3)'),
        ('4', '4)'),
        ('NUMERICAL', 'NUMERICAL (FIB)')
    ], validators=[DataRequired()])
    numerical_value = FloatField('Numerical value (if NUMERICAL)', validators=[Optional()])
    submit = SubmitField('Submit Vote')

class ChatMessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Send')

class AdminLoginForm(FlaskForm):
    username = StringField('Admin Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# NEW: public comment form
class PublicCommentForm(FlaskForm):
    name = StringField('Your name (optional)', validators=[Length(max=100)])
    text = TextAreaField('Comment', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Post Comment')