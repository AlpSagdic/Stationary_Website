from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Email
from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm


class ContactForm(FlaskForm):
    user_name = StringField("What's Your Name?", validators=[DataRequired()])
    user_email = EmailField("What's Your Email Address?", validators=[Email()])
    message_subject = StringField("What's Your Subject?", validators=[DataRequired()])
    message = CKEditorField("What's Your Message?", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Let me in!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class AddForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired()])
    img_url = StringField("IMG Url", validators=[DataRequired()])
    price = StringField("Price '$' ", validators=[DataRequired()])
    submit = SubmitField("Add New Product")
