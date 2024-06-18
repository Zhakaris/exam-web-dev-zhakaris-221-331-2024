from flask import render_template, flash, redirect, url_for, request, Blueprint, abort, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Book, Review, Genre, Role, Cover
from app.forms import LoginForm, RegistrationForm, BookForm, ReviewForm, RoleAssignmentForm
from functools import wraps
import os
import hashlib
import bleach

bp = Blueprint('main', __name__)

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role.name not in roles:
                if not current_user.is_authenticated:
                    return redirect(url_for('main.login', next=request.url))
                else:
                    flash('У вас недостаточно прав для выполнения данного действия.')
                    return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    title = request.args.get('title', '', type=str)
    genre_ids = request.args.getlist('genre', type=int)
    year = request.args.get('year', type=int)
    volume_from = request.args.get('volume_from', type=int)
    volume_to = request.args.get('volume_to', type=int)
    author = request.args.get('author', '', type=str)

    query = Book.query

    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))
    if genre_ids:
        query = query.filter(Book.genres.any(Genre.id.in_(genre_ids)))
    if year:
        query = query.filter(Book.year == year)
    if volume_from:
        query = query.filter(Book.pages >= volume_from)
    if volume_to:
        query = query.filter(Book.pages <= volume_to)
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))

    books = query.paginate(page=page, per_page=10)

    genres = Genre.query.all()
    years = db.session.query(Book.year).distinct().all()

    # Подсчет количества рецензий и средней оценки для каждой книги
    for book in books.items:
        reviews = Review.query.filter_by(book_id=book.id).all()
        book.reviews_count, book.average_rating = calculate_reviews_and_rating(reviews)

    return render_template('index.html', books=books, genres=genres, years=[y[0] for y in years])

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Добро пожаловать, {user.username}!', 'success')
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/add_book', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def add_book():
    form = BookForm()
    form.genres.choices = [(g.id, g.name) for g in Genre.query.all()]  # Динамическое наполнение жанров

    if form.validate_on_submit():
        cover_file = form.cover.data
        if cover_file:
            filename = secure_filename(cover_file.filename)
            cover_dir = os.path.join(current_app.root_path, 'static/covers')
            if not os.path.exists(cover_dir):
                os.makedirs(cover_dir)
            cover_path = os.path.join(cover_dir, filename)

            cover_file.save(cover_path)

            with open(cover_path, 'rb') as f:
                md5_hash = hashlib.md5(f.read()).hexdigest()

            # Проверка на существование обложки с таким же хэшем
            existing_cover = Cover.query.filter_by(md5_hash=md5_hash).first()
            if existing_cover:
                cover_id = existing_cover.id
            else:
                cover = Cover(file_name=filename, mime_type=cover_file.mimetype, md5_hash=md5_hash)
                db.session.add(cover)
                db.session.commit()
                cover_id = cover.id

            # Добавление книги
            book = Book(
                title=form.title.data,
                description=bleach.clean(form.description.data),
                year=form.year.data,
                publisher=form.publisher.data,
                author=form.author.data,
                pages=form.pages.data,
                cover_id=cover_id
            )

            selected_genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
            book.genres.extend(selected_genres)
            db.session.add(book)
            db.session.commit()

            flash('Книга была добавлена!')
            return redirect(url_for('main.index'))

    return render_template('add_book.html', title='Add Book', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, 
                    last_name=form.last_name.data,
                    first_name=form.first_name.data,
                    middle_name=form.middle_name.data,
                    role_id=3)  # По умолчанию роль "Пользователь"
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы зарегистрировались!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/book/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Администратор', 'Модератор')
def edit_book(id):
    book = Book.query.get_or_404(id)
    form = BookForm(obj=book)
    form.genres.choices = [(g.id, g.name) for g in Genre.query.all()]  # Динамическое наполнение жанров

    if form.validate_on_submit():
        book.title = form.title.data
        book.description = form.description.data
        book.year = form.year.data
        book.publisher = form.publisher.data
        book.author = form.author.data
        book.pages = form.pages.data
        book.genres = Genre.query.filter(Genre.id.in_(form.genres.data)).all()
        db.session.commit()
        flash('Книга обновлена!')
        return redirect(url_for('main.view_book', id=book.id))

    return render_template('edit_book.html', form=form, book=book)

@bp.route('/delete_book/<int:id>', methods=['POST'])
@login_required
@role_required('Администратор')
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Книга была успешно удалена.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/view_book/<int:id>')
def view_book(id):
    book = Book.query.get_or_404(id)
    reviews = Review.query.filter_by(book_id=book.id).all()

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()

    # Подсчёт количества рецензий и средней оценки
    total_reviews, average_rating = calculate_reviews_and_rating(reviews)

    return render_template('book_detail.html', title=book.title, book=book, reviews=reviews, user_review=user_review, total_reviews=total_reviews, average_rating=average_rating)

@bp.route('/assign_role', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def assign_role():
    form = RoleAssignmentForm()
    form.user.choices = [(user.id, user.username) for user in User.query.all()]
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]

    if form.validate_on_submit():
        user = User.query.get(form.user.data)
        role = Role.query.get(form.role.data)
        if user and role:
            user.role_id = role.id
            db.session.commit()
            flash(f'Роль {role.name} была добавлена для {user.username}.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Неправильный пользователь или роль.', 'danger')

    return render_template('assign_role.html', form=form)

@bp.route('/add_review/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    form = ReviewForm()
    book = Book.query.get_or_404(book_id)  # Получаем объект книги
    if form.validate_on_submit():
        review = Review(
            book_id=book_id,
            user_id=current_user.id,
            rating=form.rating.data,
            review_text=form.review_text.data  # Используем правильное имя поля
        )
        db.session.add(review)
        db.session.commit()
        book.update_rating_and_reviews()
        flash('Рецензия добавлена успешно!', 'success')
        return redirect(url_for('main.view_book', id=book_id))
    return render_template('add_review.html', title='Добавить рецензию', form=form, book=book)  # Передаем объект книги



def calculate_reviews_and_rating(reviews):
    """
    Функция для подсчета количества рецензий и средней оценки.

    :param reviews: список рецензий
    :return: кортеж (количество рецензий, средняя оценка)
    """
    if not reviews:
        return 0, 0.0

    total_reviews = len(reviews)
    total_rating = sum(review.rating for review in reviews)
    average_rating = total_rating / total_reviews if total_reviews > 0 else 0

    return total_reviews, round(average_rating, 1)
