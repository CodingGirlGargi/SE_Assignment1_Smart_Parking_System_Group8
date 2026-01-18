from flask import Blueprint, render_template, request, redirect, flash, session
from db import get_connection
from psycopg2.extras import DictCursor

admin_routes = Blueprint("admin_routes", __name__)

@admin_routes.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_id = int(request.form["admin_id"])
        admin_password = request.form["admin_password"]
        ground_id = int(request.form["ground_id"])

        conn = get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)

        #Verify admin credentials
        cur.execute("""
            SELECT admin_id
            FROM admin_table
            WHERE admin_id = %s
              AND admin_password = %s
              AND ground_id = %s
        """, (admin_id, admin_password, ground_id))

        admin = cur.fetchone()

        if not admin:
            cur.close()
            conn.close()
            flash("Invalid admin credentials", "error")
            # flash works
            return redirect("/admin_login")

        # Save session
        session["admin_id"] = admin_id
        session["ground_id"] = ground_id

        # Fetch bookings
        cur.execute("""
            SELECT
                user_id,
                booking_id,
                vehicle_id,
                start_time,
                end_time
            FROM bookings_table
            WHERE ground_id = %s
            ORDER BY start_time DESC
        """, (ground_id,))

        current_bookings = cur.fetchall()

        cur.execute("""
            SELECT
                user_id,
                booking_id,
                vehicle_id,
                start_time,
                end_time
            FROM past_bookings_table
            WHERE ground_id = %s
            ORDER BY start_time DESC
        """, (ground_id,))

        past_bookings = cur.fetchall()        

        cur.close()
        conn.close()

        return render_template(
            "admin_bookings.html",
            current_bookings=current_bookings,
            past_bookings = past_bookings,
            ground_id=ground_id
        )

    return render_template("admin_login.html")


@admin_routes.route("/admin_logout")
def admin_logout():
    session.clear()
    # flash("Logged out successfully"), redirecting to a different page
    return redirect("/")
