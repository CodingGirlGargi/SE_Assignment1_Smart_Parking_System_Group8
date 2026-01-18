from flask import Blueprint, render_template, request, redirect, session, url_for
from datetime import datetime
import psycopg2.extras
from db import get_connection

user_bookings = Blueprint("user_bookings", __name__)

LOCATION_DATA = {
    "Himachal Pradesh": {
        "Mandi": ["Mandi Mela Ground", "Mandi Temple Ground"],
        "Shimla": ["Shimla Church Road", "Town Hall"]
    },
    "Telangana": {
        "Hyderabad": ["Cyber City Ground", "Gurudwara Ground"],
        "Warangal": ["Ramappa Temple Ground"]
    }
}

@user_bookings.route("/user_current_bookings", methods=["GET", "POST"])
def current_bookings():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Current bookings
    cur.execute("""
        SELECT b.booking_id,b.start_time, s.slot_name, v.vehicle_number, b.ground_id
        FROM bookings_table b
        JOIN ground_slot_table s ON b.slot_id = s.slot_id
        JOIN vehicle_table v ON b.vehicle_id = v.vehicle_id
        WHERE b.user_id=%s AND b.end_time IS NULL
    """, (user_id,))
    current_bookings = cur.fetchall()

    can_book = len(current_bookings) < 3
    # Vehicles not parked
    cur.execute("""
        SELECT vehicle_id, vehicle_number
        FROM vehicle_table
        WHERE user_id=%s AND is_parked=false
    """, (user_id,))
    vehicles = cur.fetchall()

    states = LOCATION_DATA.keys()
    cities = []
    localities = []
    slots = []

    selected_vehicle_id = request.form.get("vehicle_id") or request.args.get("vehicle_id")
    selected_state = request.form.get("state") or request.args.get("state")
    selected_city = request.form.get("city") or request.args.get("city")
    selected_locality = request.form.get("locality") or request.args.get("locality")


    if selected_state:
        cities = LOCATION_DATA[selected_state].keys()

    if selected_state and selected_city:
        localities = LOCATION_DATA[selected_state][selected_city]

    if selected_state and selected_city and selected_locality:
        cur.execute("""
            SELECT ground_id
            FROM ground_table
            WHERE ground_state=%s
              AND ground_city=%s
              AND ground_locality=%s
        """, (selected_state, selected_city, selected_locality))
        ground = cur.fetchone()

        if ground:
            cur.execute("""
                SELECT s.slot_id, s.slot_name, s.is_occupied,
                       b.user_id AS booked_by
                FROM ground_slot_table s
                LEFT JOIN bookings_table b
                  ON s.slot_id=b.slot_id AND b.end_time IS NULL
                WHERE s.ground_id=%s
            """, (ground["ground_id"],))
            slots = cur.fetchall()

    conn.close()

    return render_template(
    "user_current_bookings.html",
    current_bookings=current_bookings,
    vehicles=vehicles,
    states=states,
    cities=cities,
    localities=localities,
    slots=slots,
    selected_vehicle_id=selected_vehicle_id,
    selected_state=selected_state,
    selected_city=selected_city,
    selected_locality=selected_locality,
    user_id=user_id,
    can_book = can_book
)


@user_bookings.route("/book_slot", methods=["POST"])
def book_slot():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    slot_id = request.form["slot_id"]
    vehicle_id = request.form["vehicle_id"]

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Get ground_id from slot
        cur.execute("""
            SELECT ground_id
            FROM ground_slot_table
            WHERE slot_id = %s
        """, (slot_id,))
        result = cur.fetchone()

        if not result:
            conn.close()
            return redirect(url_for("user_bookings.current_bookings"))

        ground_id = result[0]

        # Prevent double booking
        cur.execute("""
            SELECT 1
            FROM bookings_table
            WHERE slot_id = %s AND end_time IS NULL
        """, (slot_id,))
        if cur.fetchone():
            conn.close()
            return redirect(url_for("user_bookings.current_bookings"))

        # 🔹 Mark slot occupied
        cur.execute("""
            UPDATE ground_slot_table
            SET is_occupied = TRUE
            WHERE slot_id = %s
        """, (slot_id,))

        # Mark vehicle parked
        cur.execute("""
            UPDATE vehicle_table
            SET is_parked = TRUE
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        # 🔹 Insert booking (ground_id INCLUDED)
        cur.execute("""
            INSERT INTO bookings_table
                (ground_id, user_id, vehicle_id, slot_id, start_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (ground_id, user_id, vehicle_id, slot_id, datetime.now()))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Booking error:", e)

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("user_bookings.current_bookings"))

@user_bookings.route("/end_booking/<int:booking_id>", methods=["POST"])
def end_booking(booking_id):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Get booking details
        cur.execute("""
            SELECT booking_id, user_id, ground_id, slot_id, vehicle_id, start_time
            FROM bookings_table
            WHERE booking_id = %s
        """, (booking_id,))
        booking = cur.fetchone()

        if not booking:
            conn.close()
            return redirect(url_for("user_bookings.current_bookings"))

        (
            booking_id,
            user_id,
            ground_id,
            slot_id,
            vehicle_id,
            start_time
        ) = booking

        end_time = datetime.now()

        # Insert into past_bookings_table
        cur.execute("""
            INSERT INTO past_bookings_table
            (booking_id, user_id, ground_id, slot_id, vehicle_id, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            booking_id,
            user_id,
            ground_id,
            slot_id,
            vehicle_id,
            start_time,
            end_time
        ))

        # Delete from current bookings
        cur.execute("""
            DELETE FROM bookings_table
            WHERE booking_id = %s
        """, (booking_id,))

        # Free the parking slot
        cur.execute("""
            UPDATE ground_slot_table
            SET is_occupied = FALSE
            WHERE slot_id = %s
        """, (slot_id,))

        #  Update vehicle status
        cur.execute("""
            UPDATE vehicle_table
            SET is_parked = FALSE
            WHERE vehicle_id = %s
        """, (vehicle_id,))

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()

    return redirect(url_for("user_bookings.current_bookings"))


