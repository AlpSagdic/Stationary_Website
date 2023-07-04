from flask_login import LoginManager, UserMixin, login_required, current_user, logout_user, login_user
from flask import Flask, render_template, redirect, url_for, request, abort, flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ContactForm, RegisterForm, LoginForm, AddForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_bootstrap import Bootstrap
from functools import wraps
import stripe

app = Flask(__name__)
app.config["SECRET_KEY"] = "YOU_CAN_WRITE_WHATEVER_YOU_WANT"
Bootstrap(app)

stripe.api_key = "YOUR_API_KEY"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///e-commerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


#Database
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(100))


class ContactUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), unique=False, nullable=False)
    user_email = db.Column(db.String(100), unique=False, nullable=False)
    message_subject = db.Column(db.String(100), unique=False, nullable=False)
    message = db.Column(db.String(5000), unique=False, nullable=False)


class Products(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    basket = relationship("Basket", back_populates="products")


class Basket(db.Model):
    __tablename__ = "basket"
    id = db.Column(db.Integer, primary_key=True, unique=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    products = relationship("Products", back_populates="basket")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


#We used it to create the database.
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    all_products = Products.query.all()
    return render_template("index.html", products=all_products)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        user_info = ContactUser(
            user_name=form.user_name.data,
            user_email=form.user_email.data,
            message_subject=form.message_subject.data,
            message=form.message.data
        )
        db.session.add(user_info)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("contact.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That email does not exist!", "warning")
            return redirect(url_for("login"))

        elif not check_password_hash(user.password, password):
            flash("Incorrect password!", "warning")
            return redirect(url_for("login"))

        else:
            login_user(user)
            return redirect(url_for("home"))
    return render_template("login.html", form=form, current_user=current_user)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        if User.query.filter_by(email=request.form.get("email")).first():
            flash("You've already logged in!")
            return redirect(url_for("login"))

        hash_and_salted_password = generate_password_hash(
            request.form.get("password"),
            method="pbkdf2:sha256",
            salt_length=8)
        new_user = User()
        new_user.name = request.form.get("name")
        new_user.email = request.form.get("email")
        new_user.password = hash_and_salted_password
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
@admin_only
def add():
    form = AddForm()
    if form.validate_on_submit():
        product = Products()
        product.name = request.form.get("name")
        product.img_url = request.form.get("img_url")
        product.price = request.form.get("price")
        db.session.add(product)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("add.html", form=form)


@app.route("/basket-add/<int:p_id>", methods=["GET", "POST"])
def add_basket(p_id):
    product = Products.query.get(p_id)
    if not current_user.is_authenticated:
        flash("You have to login")
        return redirect(url_for("login"))
    basket = Basket()
    basket.id = p_id
    basket.product_id = p_id
    basket.user_id = current_user.id
    basket.name = product.name
    basket.price = product.price
    basket.img_url = product.img_url
    db.session.add(basket)
    db.session.commit()
    return redirect(url_for("basket"))


@app.route("/delete/<int:p_id>")
@login_required
def delete(p_id):
    product_to_delete = Basket.query.get(p_id)
    db.session.delete(product_to_delete)
    db.session.commit()
    return redirect(url_for("basket"))


@app.route("/home-delete/<int:p_id>")
@admin_only
def home_delete(p_id):
    product_delete = Products.query.get(p_id)
    db.session.delete(product_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/basket")
def basket():
    products = Basket.query.all()
    return render_template("basket.html", products=products)


@app.route('/create-checkout-session/<int:p_id>', methods=["GET", "POST"])
def create_checkout_session(p_id):
    product_to_buy = Basket.query.get(p_id)
    checkout_session = stripe.checkout.Session.create(
        line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": product_to_buy.name,
                                     "images": [product_to_buy.img_url]},
                    "unit_amount": int(f"{product_to_buy.price.strip('$')}00"),
                },
                'quantity': 1,
            }],
        mode='payment',
        success_url=f"http://127.0.0.1:5000/success/{p_id}",
        cancel_url="http://127.0.0.1:5000/cancel",
    )
    return redirect(checkout_session.url, code=303)


@app.route("/success/<int:p_id>")
@login_required
def success(p_id):
    product_bought = Basket.query.get(p_id)
    db.session.delete(product_bought)
    db.session.commit()
    return render_template("success.html", product=product_bought)


@app.route("/cancel")
@login_required
def cancel():
    return render_template("cancel.html")


if __name__ == "__main__":
    app.run(debug=True)
