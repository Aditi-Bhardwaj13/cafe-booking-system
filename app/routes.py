from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import Booking, CafeTable, User

main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template("dashboard.html", bookings=bookings)


@main_bp.route("/booking", methods=["GET", "POST"])
@login_required
def booking():
    tables = CafeTable.query.filter_by(is_available=True).all()

    if request.method == "POST":
        table_id = request.form.get("table_id", type=int)
        booking_date = request.form.get("booking_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        if not table_id or not booking_date or not start_time or not end_time:
            flash("Please complete all booking details.", "danger")
            return render_template("booking.html", tables=tables)

        if end_time <= start_time:
            flash("End time must be later than start time.", "danger")
            return render_template("booking.html", tables=tables)

        booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
        start_obj = datetime.strptime(start_time, "%H:%M").time()
        end_obj = datetime.strptime(end_time, "%H:%M").time()

        existing = Booking.query.filter(
            Booking.table_id == table_id,
            Booking.booking_date == booking_date_obj,
            Booking.status != "cancelled",
            ((Booking.start_time <= start_obj) & (Booking.end_time > start_obj)) |
            ((Booking.start_time < end_obj) & (Booking.end_time >= end_obj))
        ).first()

        if existing:
            flash("This table is already booked for that time period.", "danger")
            return render_template("booking.html", tables=tables)

        new_booking = Booking(
            user_id=current_user.id,
            table_id=table_id,
            booking_date=booking_date_obj,
            start_time=start_obj,
            end_time=end_obj,
            status="pending",
        )
        db.session.add(new_booking)
        db.session.commit()
        flash("Booking created successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("booking.html", tables=tables)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists.", "danger")
            return render_template("register.html")

        user = User(username=username, email=email, role="customer")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful.", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))
