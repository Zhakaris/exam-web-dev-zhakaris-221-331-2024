from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, SelectMultipleField, SelectField, FileField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=255)])
    password = PasswordField('Password', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    middle_name = StringField('Middle Name')
    submit = SubmitField('Register')

class BookForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    year = IntegerField('Год', validators=[DataRequired()])
    publisher = StringField('Издательство', validators=[DataRequired()])
    author = StringField('Автор', validators=[DataRequired()])
    pages = IntegerField('Объём (в страницах)', validators=[DataRequired()])
    cover = FileField('Обложка')
    genres = SelectMultipleField('Жанры', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Сохранить')

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating', validators=[DataRequired()])
    review_text = TextAreaField('Text', validators=[DataRequired()])
    submit = SubmitField('Add Review')

class RoleAssignmentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    role = SelectField('Role', choices=[('1', 'Администратор'), ('2', 'Модератор'), ('3', 'Пользователь')], validators=[DataRequired()])
    submit = SubmitField('Assign Role')

class ReviewForm(FlaskForm):
    rating = SelectField('Оценка', choices=[(5, 'Отлично'), 
    (4, 'Хорошо'), (3, 'Удовлетворительно'), (2, 'Неудовлетворительно'), (1, 'Плохо'), (0, 'Ужасно')], coerce=int)
    review_text = TextAreaField('Текст рецензии', validators=[DataRequired()])
    submit = SubmitField('Сохранить')


class RoleAssignmentForm(FlaskForm):
    user = SelectField('User', coerce=int, validators=[DataRequired()])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Role')