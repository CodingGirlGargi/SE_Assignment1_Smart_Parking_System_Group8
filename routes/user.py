from flask import Blueprint, render_template, request, flash, redirect, session
import re
from psycopg2.extras import DictCursor
from db import get_connection
from datetime import datetime

user_routes = Blueprint("user_routes", __name__)


@user_routes.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        user_name = request.form["user_name"]
        user_email = request.form["user_email"]
        user_password = request.form["user_password"]
        user_license_number = request.form["user_license_number"]

        # License number validation
        pattern = r'^[A-Za-z]{2}[0-9]{13}$'
        if not re.match(pattern, user_license_number):
            flash("Invalid license number format", "error")
            # this flash works!
            return redirect("/user_register")

        conn = get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        try:
            # Check if email already exists
            cur.execute("""
                SELECT user_id
                FROM user_table
                WHERE user_email = %s
            """, (user_email,))

            existing_user = cur.fetchone()

            if existing_user:
                flash("User with this email already exists", "error")
                # flash works
                cur.close()
                conn.close()
                return redirect("/user_register")

            # Insert user
            cur.execute("""
                INSERT INTO user_table (
                    user_name,
                    user_email,
                    user_password,
                    user_license_number
                )
                VALUES (%s, %s, %s, %s)
            """, (
                user_name,
                user_email,
                user_password,
                user_license_number
            ))

            conn.commit()

            # flash("Registration successful. Please login.", "success")
            return redirect("/user_login")

        except Exception as e:
            conn.rollback()
            flash("Database error during registration", "error")
            return redirect("/user_register")

        finally:
            cur.close()
            conn.close()

    return render_template("user_register.html")


@user_routes.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        user_email = request.form["user_email_login"]
        user_password = request.form["user_password_login"]

        conn = get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        # Verify user credentials
        cur.execute("""
            SELECT user_id, user_name
            FROM user_table
            WHERE user_email = %s
              AND user_password = %s
        """, (user_email, user_password))

        user = cur.fetchone()

        if not user:
            cur.close()
            conn.close()
            flash("Invalid email or password", "error")
            return redirect("/user_login")

        # Save session
        session["user_id"] = user["user_id"]
        session["user_name"] = user["user_name"]

        cur.close()
        conn.close()

        return redirect("/user_dashboard")

    return render_template("user_login.html")


@user_routes.route("/user_dashboard", methods = ["GET"])
def user_dashboard():
    if "user_id" not in session:
        # flash("Please login first", "warning")
        return redirect("/user_login")

    return render_template(
        "user_dashboard.html",
        user_id=session["user_id"],
        user_name=session["user_name"]
    )

@user_routes.route("/user_logout")
def user_logout():
    session.clear()
    # flash("Logged out successfully", "success")
    return redirect("/")

@user_routes.route("/user_vehicles", methods=["GET", "POST"])
def user_vehicles():
    if "user_id" not in session:
        # flash("Please login first", "warning")
        return redirect("/user_login")

    user_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)

    #  Handle new vehicle registration
    if request.method == "POST":
        vehicle_number = request.form["vehicle_number"].strip()

        # Count existing vehicles
        cur.execute(
            "SELECT COUNT(*) FROM vehicle_table WHERE user_id = %s",
            (user_id,)
        )
        count = cur.fetchone()[0]

        if count >= 3:
            flash("Maximum vehicle registration limit reached", "error")
        else:
            try:
                cur.execute(
                    """
                    INSERT INTO vehicle_table (user_id, vehicle_number, is_parked)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, vehicle_number, False)
                )
                conn.commit()
                flash("Vehicle registered successfully", "success")
            except Exception:
                conn.rollback()
                flash("Vehicle already registered", "error")

        cur.close()
        conn.close()
        return redirect("/user_vehicles")

    #  Fetch registered vehicles
    cur.execute(
        """
        SELECT vehicle_id, vehicle_number
        FROM vehicle_table
        WHERE user_id = %s
        ORDER BY vehicle_id
        """,
        (user_id,)
    )

    vehicles = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "user_vehicles.html",
        vehicles=vehicles
    )

@user_routes.route("/remove_vehicle/<int:vehicle_id>", methods=["POST"])
def remove_vehicle(vehicle_id):
    if "user_id" not in session:
        # flash("Please login first", "warning")
        return redirect("/user_login")

    user_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    #  Check if vehicle is currently booked
    cur.execute("""
        SELECT 1
        FROM bookings_table
        WHERE vehicle_id = %s
          AND end_time IS NULL
    """, (vehicle_id,))

    active_booking = cur.fetchone()

    if active_booking:
        cur.close()
        conn.close()
        flash(
            "This vehicle is currently booked. First release the slot and then remove the vehicle.",
            "error"
        )
        return redirect("/user_vehicles")

    #  No active booking → safe to delete
    cur.execute("""
        DELETE FROM vehicle_table
        WHERE vehicle_id = %s AND user_id = %s
    """, (vehicle_id, user_id))

    conn.commit()
    cur.close()
    conn.close()

    # flash("Vehicle removed successfully", "success")
    return redirect("/user_vehicles")



@user_routes.route("/user_past_bookings")
def user_past_bookings():
    if "user_id" not in session:
        return redirect("/user_login")

    user_id = session["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            pb.ground_id,
            pb.slot_id,
            pb.start_time,
            pb.end_time,
            v.vehicle_number
        FROM past_bookings_table pb
        JOIN vehicle_table v ON pb.vehicle_id = v.vehicle_id
        WHERE pb.user_id = %s
        ORDER BY pb.end_time DESC
    """, (user_id,))

    rows = cur.fetchall()

    past_bookings = []
    for r in rows:
        past_bookings.append({
            "ground_id": r[0],
            "slot_id": r[1],
            "start_time": r[2],
            "end_time": r[3],
            "vehicle_number": r[4]
        })

    cur.close()
    conn.close()

    return render_template(
        "user_past_bookings.html",
        past_bookings=past_bookings
    )

