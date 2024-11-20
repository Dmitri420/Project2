from flask import Flask, render_template, url_for, request, redirect, flash
from flask_migrate import Migrate
from sqlalchemy.sql.functions import current_user
from db import db, VideoGame, User, Review, bcrypt
from flask_login import LoginManager, logout_user, login_user, current_user
from forms import RegistrationForm, LoginForm, ReviewForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/images'
migrate = Migrate(app, db)

# DB extensions
db.init_app(app)
migrate = Migrate(app, db)
app.secret_key = "super secret key"

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # If the user is not logged in, redirect them to the 'login' view

# Define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Retrieves the User object by its ID


@app.route('/')
def home():
    video_games = VideoGame.query.all()  # Fetch all video games from the database
    return render_template('home.html', video_games=video_games)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/game/<int:game_id>', methods=['GET', 'POST'])
def game_page(game_id):
    video_game = VideoGame.query.get_or_404(game_id)
    form = ReviewForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        review = Review(content=form.content.data, game_id=game_id, user_id=current_user.id)
        db.session.add(review)
        db.session.commit()
        flash('Your review has been posted!', 'success')
        return redirect(url_for('game_page', game_id=game_id))
    reviews = Review.query.filter_by(game_id=game_id).all()
    return render_template('game.html', video_game=video_game, form=form, reviews=reviews)


@app.route('/add-game', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        # Collect data from the add game form
        title = request.form.get('title')
        description = request.form.get('description')
        poster_url = request.form.get('poster_url')  # Full path to the image file
        developer = request.form.get('developer')
        platforms = request.form.get('platforms')
        year = request.form.get('year')

        # Create a new VideoGame object
        new_game = VideoGame(
            title=title,
            description=description,
            poster_url=poster_url,
            developer=developer,
            platforms=platforms,
            year=year
        )

        # Add and commit to the database
        db.session.add(new_game)
        db.session.commit()

        flash('Game added successfully!')
        return redirect(url_for('home'))

    return render_template('add_game.html')

if __name__ == '__main__':
    app.run(debug=True)

