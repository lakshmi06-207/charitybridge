from dotenv import load_dotenv
import os
import json
import re
import secrets
import smtplib
import uuid
import threading
import webbrowser
from io import BytesIO
from email.message import EmailMessage
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    send_file,
    abort
)

import qrcode
import razorpay
import mysql.connector
from mysql.connector import Error

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from werkzeug.utils import secure_filename
ALLOWED_RECEIPT_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "pdf"
}

# Load environment variables from .env
load_dotenv(override=True)

print("Loaded .env path:", os.path.abspath(".env"))
print("Key ID prefix:", os.getenv("RAZORPAY_KEY_ID", "")[:8])
print("Secret length:", len(os.getenv("RAZORPAY_KEY_SECRET", "")))

# CharityBridge payment configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "").strip()
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
RAZORPAY_WEBHOOK_SECRET = os.getenv(
    "RAZORPAY_WEBHOOK_SECRET", ""
).strip()


# Keep payment testing enabled
PAYMENT_TEST_MODE = (
    os.getenv("PAYMENT_TEST_MODE", "true").strip().lower() == "true"
)

razorpay_client = None

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    )
    print("Razorpay package:", "OK")
print("Razorpay Key ID loaded:", bool(RAZORPAY_KEY_ID))
print("Razorpay Secret loaded:", bool(RAZORPAY_KEY_SECRET))
print("Razorpay client ready:", razorpay_client is not None)
print("Loaded .env path:", os.path.abspath(".env"))
print("Key ID prefix:", os.getenv("RAZORPAY_KEY_ID", "")[:8])
print("Secret length:", len(os.getenv("RAZORPAY_KEY_SECRET", "")))
# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)
PAYMENT_RECEIPT_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "payment_receipts"
)

os.makedirs(PAYMENT_RECEIPT_FOLDER, exist_ok=True)

app.secret_key = "charitybridge_secret_key"


# ============================================================
# DATABASE CONNECTION
# ============================================================

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "varsha06@207"
MYSQL_DATABASE = "charitybridge"


class ReconnectableDB:
    """
    Keeps the existing db variable used by all existing routes.

    Automatically creates a fresh MySQL connection whenever
    the previous connection was closed or unavailable.
    """

    def __init__(self):
        self._connection = None
        self._connect()

    def _connect(self):
        self._connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            autocommit=False,
            use_pure=True
        )

    def _ensure_connection(self):
        try:
            if (
                self._connection is None
                or not self._connection.is_connected()
            ):
                self._connect()

        except Exception:
            self._connect()

    def is_connected(self):
        try:
            return (
                self._connection is not None
                and self._connection.is_connected()
            )

        except Exception:
            return False

    def cursor(self, *args, **kwargs):
        self._ensure_connection()

        return self._connection.cursor(
            *args,
            **kwargs
        )

    def commit(self):
        self._ensure_connection()

        return self._connection.commit()

    def rollback(self):
        self._ensure_connection()

        return self._connection.rollback()

    def close(self):
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception:
                pass

    def get_connection(self):
        """
        Return the active MySQL connection.
        Reconnect automatically if needed.
        """
        self._ensure_connection()
        return self._connection

    def __getattr__(self, name):
        self._ensure_connection()

        return getattr(
            self._connection,
            name
        )


    def __getattr__(self, name):

        self._ensure_connection()

        return getattr(
            self._connection,
            name
        )



try:
    db = ReconnectableDB()

    if db.is_connected():
        print("========================================")
        print("MySQL Connected Successfully!")
        print("Database: charitybridge")
        print("========================================")

except Error as e:
    db = None

    print("========================================")
    print("MySQL Connection Failed!")
    print("Error:", e)
    print("========================================")


def ensure_payment_tables():
    """Create a separate table for tracking payment verification."""
    if db is None:
        print("Database unavailable. Payment table not checked.")
        return

    cursor = None

    try:
        cursor = db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_payment_records (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                request_id INT NOT NULL,
                helper_id INT NOT NULL,
                gateway_order_id VARCHAR(100) NULL,
                gateway_payment_id VARCHAR(100) NULL,
                amount_paise BIGINT NOT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'created',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP NULL,
                UNIQUE KEY uq_gateway_payment_id (gateway_payment_id),
                INDEX idx_payment_request (request_id),
                INDEX idx_payment_helper (helper_id),
                INDEX idx_payment_status (status)
            )
        """)

        db.commit()
        print("Payment records table is ready.")

    except Exception as e:
        print("Payment table setup failed:", e)

    finally:
        if cursor:
            cursor.close()


# ============================================================
# DASHBOARD + COMMUNITY + CHAT SUPPORT TABLES
# SAFE DATABASE SETUP AND MIGRATIONS
# ============================================================

def ensure_dashboard_support_tables():

    connection = db

    if connection is None:
        print("Database unavailable. Support tables not checked.")
        return

    cursor = None

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                is_read TINYINT(1) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_cb_notifications_user (user_id),
                INDEX idx_cb_notifications_read (user_id, is_read)
            )
        """)
                # ----------------------------------------------------
        # VOLUNTEER INTERESTS AND FOUNDER INSTRUCTIONS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_volunteer_interests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id INT NOT NULL,
                volunteer_id INT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                founder_instructions TEXT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_volunteer_interest
                    (request_id, volunteer_id),
                INDEX idx_interest_volunteer (volunteer_id),
                INDEX idx_interest_request (request_id),
                INDEX idx_interest_status (status)
            )
        """)


        # ----------------------------------------------------
        # PRIVATE MESSAGES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_private_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                message TEXT NULL,
                media_path VARCHAR(500) NULL,
                media_type VARCHAR(30) NULL,
                is_read TINYINT(1) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_cb_messages_sender (sender_id),
                INDEX idx_cb_messages_receiver (receiver_id),
                INDEX idx_cb_messages_conversation
                    (sender_id, receiver_id, created_at)
            )
        """)

        # ----------------------------------------------------
        # COMMUNITY POSTS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_community_posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                content TEXT NULL,
                image_path VARCHAR(500) NULL,
                video_path VARCHAR(500) NULL,
                audio_path VARCHAR(500) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_cb_posts_user (user_id),
                INDEX idx_cb_posts_created (created_at)
            )
        """)

        # ----------------------------------------------------
        # COMMUNITY FOLLOWS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_community_follows (
                id INT AUTO_INCREMENT PRIMARY KEY,
                follower_id INT NOT NULL,
                following_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_follow (follower_id, following_id),
                INDEX idx_cb_follow_follower (follower_id),
                INDEX idx_cb_follow_following (following_id)
            )
        """)

        # ----------------------------------------------------
        # COMMUNITY POST LIKES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_community_post_likes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_post_like (post_id, user_id),
                INDEX idx_cb_likes_post (post_id),
                INDEX idx_cb_likes_user (user_id)
            )
        """)

        # ----------------------------------------------------
        # COMMUNITY POST COMMENTS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_community_post_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT NOT NULL,
                user_id INT NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_cb_comments_post (post_id),
                INDEX idx_cb_comments_user (user_id)
            )
        """)

        # ----------------------------------------------------
        # COMMUNITY POST SHARES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_community_post_shares (
                id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_post_share (post_id, user_id),
                INDEX idx_cb_shares_post (post_id),
                INDEX idx_cb_shares_user (user_id)
            )
        """)

        # ----------------------------------------------------
        # USER THEME / BACKGROUND PREFERENCE
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_user_theme_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                theme_name VARCHAR(50) NOT NULL DEFAULT 'aurora',
                background_color VARCHAR(30) NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_theme (user_id)
            )
        """)

        # ----------------------------------------------------
        # SAFE MIGRATIONS FOR EXISTING TABLES
        # Add only columns that are missing.
        # Never drop tables or existing columns.
        # ----------------------------------------------------

        migrations = {
            "cb_community_posts": {
                "video_path": "VARCHAR(500) NULL",
                "audio_path": "VARCHAR(500) NULL",
            },
            "cb_private_messages": {
                "media_path": "VARCHAR(500) NULL",
                "media_type": "VARCHAR(30) NULL",
                "is_read": "TINYINT(1) NOT NULL DEFAULT 0",
            },
        }

        for table_name, columns in migrations.items():

            cursor.execute(
                f"SHOW COLUMNS FROM `{table_name}`"
            )

            existing_columns = {
                row[0] for row in cursor.fetchall()
            }

            for column_name, definition in columns.items():

                if column_name not in existing_columns:

                    cursor.execute(
                        f"ALTER TABLE `{table_name}` "
                        f"ADD COLUMN `{column_name}` {definition}"
                    )

                    print(
                        f"Added missing column: "
                        f"{table_name}.{column_name}"
                    )

        connection.commit()

        print("========================================")
        print("CharityBridge support tables ready!")
        print("Community posts and shares checked!")
        print("Private message schema checked!")
        print("========================================")

    except Error as e:

        try:
            connection.rollback()
        except Exception:
            pass

        print("Support table setup error:", e)

    except Exception as e:

        try:
            connection.rollback()
        except Exception:
            pass

        print("Unexpected support table setup error:", e)

    finally:

        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass



# ============================================================
# EMAIL / OTP SETTINGS
# ============================================================

GMAIL_SENDER = os.getenv(
    "GMAIL_SENDER",
    "lakshmisubramani021@gmail.com"
)

GMAIL_APP_PASSWORD = os.getenv(
    "GMAIL_APP_PASSWORD",
    ""
)
# ============================================================
# HOME / LANDING PAGE
# ============================================================

@app.route("/")
def home():

    connection = db

    if connection is None:

        return render_template(
            "index.html",
            donations_count=0,
            lives_impacted=0,
            volunteers_count=0,
            cities_count=0,
            total_amount=0
        )

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        # ====================================================
        # TOTAL SUCCESSFUL MONEY DONATIONS
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM money_donations
            WHERE status = 'Success'
        """)

        result = cursor.fetchone()

        donations_count = (
            result["total"]
            if result
            else 0
        )


        # ====================================================
        # TOTAL MONEY DONATED
        # ====================================================

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM money_donations
            WHERE status = 'Success'
        """)

        result = cursor.fetchone()

        total_amount = (
            result["total"]
            if result
            else 0
        )


        # ====================================================
        # PEOPLE / HELP REQUESTS IMPACTED
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM help_requests
        """)

        result = cursor.fetchone()

        lives_impacted = (
            result["total"]
            if result
            else 0
        )


        # ====================================================
        # TOTAL VOLUNTEERS
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM volunteers
        """)

        result = cursor.fetchone()

        volunteers_count = (
            result["total"]
            if result
            else 0
        )


        # ====================================================
        # TOTAL REGISTERED USERS
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
        """)

        result = cursor.fetchone()

        cities_count = (
            result["total"]
            if result
            else 0
        )


        return render_template(
            "index.html",
            donations_count=donations_count,
            lives_impacted=lives_impacted,
            volunteers_count=volunteers_count,
            cities_count=cities_count,
            total_amount=total_amount
        )

    except Error as e:

        print(
            "Home page database error:",
            e
        )

        return render_template(
            "index.html",
            donations_count=0,
            lives_impacted=0,
            volunteers_count=0,
            cities_count=0,
            total_amount=0
        )

    finally:

        cursor.close()


# ============================================================
# ABOUT US PAGE
# ============================================================

@app.route("/about")
def about():

    return render_template(
        "about.html"
    )


# ============================================================
# MISSION PAGE
# ============================================================

@app.route("/mission")
def mission():

    return redirect(
        url_for("about")
    )


# ============================================================
# HOW IT WORKS PAGE
# ============================================================

@app.route("/how")
@app.route("/how-it-works")
def how_it_works():

    return render_template(
        "how-it-works.html"
    )

# ============================================================
# COMMUNITY PAGE
# REAL USERS + REAL POSTS + REAL LIKES + COMMENTS + SHARES
# ============================================================

@app.route("/community")
def community():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    try:

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # ====================================================
        # CURRENT LOGGED-IN USER
        # ====================================================

        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.email_verified,
                u.created_at,

                up.location,
                up.profile_image,
                up.profession

            FROM users u

            LEFT JOIN user_profiles up
                ON u.id = up.user_id

            WHERE u.id = %s

            LIMIT 1
        """, (user_id,))

        current_user = cursor.fetchone()

        if not current_user:

            session.clear()

            return redirect(
                url_for("login")
            )

        # ====================================================
        # COMMUNITY MEMBERS
        # ====================================================

        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.email_verified,
                u.created_at,

                up.location,
                up.profile_image,
                up.profession

            FROM users u

            LEFT JOIN user_profiles up
                ON u.id = up.user_id

            ORDER BY u.name ASC
        """)

        community_users = cursor.fetchall()

        # ====================================================
        # TOTAL USERS
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total_users
            FROM users
        """)

        result = cursor.fetchone()

        total_users = (
            int(result["total_users"])
            if result
            else 0
        )

        # ====================================================
        # REAL COMMUNITY POSTS
        # ====================================================

        cursor.execute("""
            SELECT

                p.id,
                p.user_id,
                p.content,

                p.image_path,
                p.video_path,
                p.audio_path,

                p.created_at,

                u.name,
                u.role,
                u.email_verified,

                up.profile_image,
                up.location,
                up.profession,

                (
                    SELECT COUNT(*)
                    FROM cb_community_post_likes l
                    WHERE l.post_id = p.id
                ) AS like_count,

                (
                    SELECT COUNT(*)
                    FROM cb_community_post_comments c
                    WHERE c.post_id = p.id
                ) AS comment_count,

                (
                    SELECT COUNT(*)
                    FROM cb_community_post_shares s
                    WHERE s.post_id = p.id
                ) AS share_count,

                (
                    SELECT COUNT(*)
                    FROM cb_community_post_likes ml
                    WHERE ml.post_id = p.id
                      AND ml.user_id = %s
                ) AS liked_by_me,

                (
                    SELECT COUNT(*)
                    FROM cb_community_post_shares ms
                    WHERE ms.post_id = p.id
                      AND ms.user_id = %s
                ) AS shared_by_me

            FROM cb_community_posts p

            INNER JOIN users u
                ON p.user_id = u.id

            LEFT JOIN user_profiles up
                ON p.user_id = up.user_id

            ORDER BY p.created_at DESC
        """, (
            user_id,
            user_id
        ))

        posts = cursor.fetchall()

        # ====================================================
        # FORMAT REAL POST DATA
        # ====================================================

        for post in posts:

            post["like_count"] = int(
                post.get("like_count") or 0
            )

            post["comment_count"] = int(
                post.get("comment_count") or 0
            )

            post["share_count"] = int(
                post.get("share_count") or 0
            )

            post["liked_by_me"] = bool(
                post.get("liked_by_me")
            )

            post["shared_by_me"] = bool(
                post.get("shared_by_me")
            )

            # Format date/time for display

            if post.get("created_at"):

                post["created_at_display"] = (
                    post["created_at"].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                )

            else:

                post["created_at_display"] = ""

        # ====================================================
        # PAGE
        # ====================================================

        return render_template(
            "community.html",

            current_user=current_user,

            community_users=community_users,

            posts=posts,

            total_users=total_users
        )

    except Exception as e:

        print(
            "COMMUNITY PAGE ERROR:",
            e
        )

        return render_template(
            "community.html",

            current_user={
                "id": user_id,

                "name": session.get(
                    "user_name",
                    "User"
                ),

                "email": session.get(
                    "email",
                    ""
                ),

                "role": session.get(
                    "role",
                    "user"
                ),

                "email_verified": 0,

                "profile_image": None,

                "location": None,

                "profession": None
            },

            community_users=[],

            posts=[],

            total_users=0
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()

      # ============================================================
# CREATE COMMUNITY POST
# IMAGE + VIDEO + AUDIO + CAPTION
# ============================================================

@app.route(
    "/community/post/create",
    methods=["POST"]
)
def create_community_post():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login to create a post."
        }), 401

    conn = None
    cursor = None

    try:

        conn = db.get_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        # ====================================================
        # CAPTION
        # ====================================================

        content = request.form.get(
            "content",
            ""
        ).strip()

        # ====================================================
        # FILES
        # ====================================================

        image = request.files.get(
            "image"
        )

        video = request.files.get(
            "video"
        )

        audio = request.files.get(
            "audio"
        )

        image_path = None
        video_path = None
        audio_path = None

        # ====================================================
        # UPLOAD FOLDER
        # ====================================================

        upload_folder = os.path.join(
            app.root_path,
            "static",
            "uploads",
            "community"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        # ====================================================
        # ALLOWED FILE TYPES
        # ====================================================

        allowed_images = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp"
        }

        allowed_videos = {
            ".mp4",
            ".webm",
            ".mov",
            ".avi",
            ".mkv"
        }

        allowed_audio = {
            ".mp3",
            ".wav",
            ".ogg",
            ".m4a",
            ".aac"
        }

        # ====================================================
        # IMAGE
        # ====================================================

        if image and image.filename:

            from werkzeug.utils import secure_filename

            filename = secure_filename(
                image.filename
            )

            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension not in allowed_images:

                return jsonify({
                    "success": False,
                    "message":
                        "Unsupported image format."
                }), 400

            unique_filename = (
                f"{secrets.token_hex(16)}"
                f"{extension}"
            )

            file_path = os.path.join(
                upload_folder,
                unique_filename
            )

            image.save(file_path)

            image_path = (
                "uploads/community/"
                + unique_filename
            )

        # ====================================================
        # VIDEO
        # ====================================================

        if video and video.filename:

            from werkzeug.utils import secure_filename

            filename = secure_filename(
                video.filename
            )

            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension not in allowed_videos:

                return jsonify({
                    "success": False,
                    "message":
                        "Unsupported video format."
                }), 400

            unique_filename = (
                f"{secrets.token_hex(16)}"
                f"{extension}"
            )

            file_path = os.path.join(
                upload_folder,
                unique_filename
            )

            video.save(file_path)

            video_path = (
                "uploads/community/"
                + unique_filename
            )

        # ====================================================
        # AUDIO
        # ====================================================

        if audio and audio.filename:

            from werkzeug.utils import secure_filename

            filename = secure_filename(
                audio.filename
            )

            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension not in allowed_audio:

                return jsonify({
                    "success": False,
                    "message":
                        "Unsupported audio format."
                }), 400

            unique_filename = (
                f"{secrets.token_hex(16)}"
                f"{extension}"
            )

            file_path = os.path.join(
                upload_folder,
                unique_filename
            )

            audio.save(file_path)

            audio_path = (
                "uploads/community/"
                + unique_filename
            )

        # ====================================================
        # CHECK POST CONTENT
        # ====================================================

        has_media = (
            image_path
            or video_path
            or audio_path
        )

        if not content and not has_media:

            return jsonify({
                "success": False,
                "message":
                    "Please write a caption or select media."
            }), 400

        # ====================================================
        # SAVE REAL POST
        # ====================================================

        cursor.execute("""
            INSERT INTO cb_community_posts
            (
                user_id,
                content,
                image_path,
                video_path,
                audio_path
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            user_id,
            content if content else None,
            image_path,
            video_path,
            audio_path
        ))

        conn.commit()

        post_id = cursor.lastrowid

        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "message":
                "Post shared successfully.",

            "post_id":
                post_id
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "CREATE COMMUNITY POST ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message":
                "Unable to create the post."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
            
# ============================================================
# DELETE COMMUNITY POST — OWNER ONLY
# Deletes the post, related interactions, and uploaded media
# ============================================================

@app.route(
    "/community/post/<int:post_id>/delete",
    methods=["POST"]
)
def delete_community_post(post_id):
    import os

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = None
    cursor = None
    media_paths = []

    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # Only the owner can delete the post.
        cursor.execute("""
            SELECT user_id, image_path, video_path, audio_path
            FROM cb_community_posts
            WHERE id = %s
            LIMIT 1
        """, (post_id,))

        post = cursor.fetchone()

        if not post:
            return jsonify({
                "success": False,
                "message": "Post not found."
            }), 404

        if int(post["user_id"]) != int(user_id):
            return jsonify({
                "success": False,
                "message": "You can only delete your own posts."
            }), 403

        # Remember uploaded files; remove them after the DB commit.
        for column in ("image_path", "video_path", "audio_path"):
            stored_path = post.get(column)

            if stored_path:
                normalized = stored_path.replace("\\", "/").lstrip("/")

                if normalized.startswith("uploads/community/"):
                    filename = os.path.basename(normalized)
                    full_path = os.path.join(
                        app.root_path,
                        "static",
                        "uploads",
                        "community",
                        filename
                    )
                    media_paths.append(full_path)

        # Remove related records first.
        cursor.execute("""
            DELETE FROM cb_community_post_likes
            WHERE post_id = %s
        """, (post_id,))

        cursor.execute("""
            DELETE FROM cb_community_post_comments
            WHERE post_id = %s
        """, (post_id,))

        cursor.execute("""
            DELETE FROM cb_community_post_shares
            WHERE post_id = %s
        """, (post_id,))

        # Delete the post itself.
        cursor.execute("""
            DELETE FROM cb_community_posts
            WHERE id = %s AND user_id = %s
        """, (post_id, user_id))

        if cursor.rowcount != 1:
            raise Exception("Post could not be deleted.")

        conn.commit()

        # Remove media files after the database deletion succeeds.
        for path in media_paths:
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError as file_error:
                print("MEDIA FILE CLEANUP ERROR:", file_error, flush=True)

        return jsonify({
            "success": True,
            "message": "Post deleted successfully.",
            "post_id": post_id
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("DELETE COMMUNITY POST ERROR:", repr(e), flush=True)

        return jsonify({
            "success": False,
            "message": "Unable to delete the post. Check the server terminal."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

        # ============================================================
# LIKE / UNLIKE COMMUNITY POST
# ============================================================

@app.route("/community/post/<int:post_id>/like", methods=["POST"])
def like_community_post(post_id):

    # --------------------------------------------------------
    # USER MUST BE LOGGED IN
    # --------------------------------------------------------
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "Please login to like this post."
        }), 401

    connection = db

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection unavailable."
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # CHECK WHETHER POST EXISTS
        # ----------------------------------------------------
        cursor.execute("""
            SELECT id
            FROM cb_community_posts
            WHERE id = %s
            LIMIT 1
        """, (post_id,))

        post = cursor.fetchone()

        if not post:
            return jsonify({
                "success": False,
                "message": "Post not found."
            }), 404

        # ----------------------------------------------------
        # CHECK WHETHER USER ALREADY LIKED
        # ----------------------------------------------------
        cursor.execute("""
            SELECT id
            FROM cb_community_post_likes
            WHERE post_id = %s
              AND user_id = %s
            LIMIT 1
        """, (post_id, user_id))

        existing_like = cursor.fetchone()

        # ----------------------------------------------------
        # UNLIKE
        # ----------------------------------------------------
        if existing_like:

            cursor.execute("""
                DELETE FROM cb_community_post_likes
                WHERE post_id = %s
                  AND user_id = %s
            """, (post_id, user_id))

            liked = False

        # ----------------------------------------------------
        # LIKE
        # ----------------------------------------------------
        else:

            cursor.execute("""
                INSERT INTO cb_community_post_likes
                (
                    post_id,
                    user_id
                )
                VALUES
                (
                    %s,
                    %s
                )
            """, (post_id, user_id))

            liked = True

        connection.commit()

        # ----------------------------------------------------
        # GET REAL LIKE COUNT
        # ----------------------------------------------------
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM cb_community_post_likes
            WHERE post_id = %s
        """, (post_id,))

        result = cursor.fetchone()

        like_count = (
            result["total"]
            if result
            else 0
        )

        return jsonify({
            "success": True,
            "liked": liked,
            "like_count": like_count
        })

    except Error as e:

        connection.rollback()

        print(
            "Community like error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to update the like."
        }), 500

    except Exception as e:

        connection.rollback()

        print(
            "Community like unexpected error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to update the like."
        }), 500

    finally:
        cursor.close()
        # ============================================================
# LOAD COMMUNITY POST COMMENTS
# ============================================================

@app.route("/community/post/<int:post_id>/comments", methods=["GET"])
def get_community_comments(post_id):

    connection = db

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection unavailable."
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # CHECK POST
        # ----------------------------------------------------
        cursor.execute("""
            SELECT id
            FROM cb_community_posts
            WHERE id = %s
            LIMIT 1
        """, (post_id,))

        post = cursor.fetchone()

        if not post:
            return jsonify({
                "success": False,
                "message": "Post not found."
            }), 404

        # ----------------------------------------------------
        # GET REAL COMMENTS
        # ----------------------------------------------------
        cursor.execute("""
            SELECT
                c.id,
                c.post_id,
                c.user_id,
                c.comment,
                c.created_at,

                u.name,
                u.role,
                u.email_verified,

                up.profile_image

            FROM cb_community_post_comments c

            INNER JOIN users u
                ON c.user_id = u.id

            LEFT JOIN user_profiles up
                ON u.id = up.user_id

            WHERE c.post_id = %s

            ORDER BY c.created_at ASC
        """, (post_id,))

        comments = cursor.fetchall()

        # ----------------------------------------------------
        # CONVERT DATETIME FOR JSON
        # ----------------------------------------------------
        for comment in comments:

            if comment.get("created_at"):
                comment["created_at"] = (
                    comment["created_at"].strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                )

        return jsonify({
            "success": True,
            "comments": comments,
            "comment_count": len(comments)
        })

    except Error as e:

        print(
            "Load community comments error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to load comments."
        }), 500

    except Exception as e:

        print(
            "Load community comments unexpected error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to load comments."
        }), 500

    finally:
        cursor.close()
        # ============================================================
# FOLLOW / UNFOLLOW COMMUNITY USER
# ============================================================

@app.route("/community/follow/<int:user_id>", methods=["POST"])
def follow_community_user(user_id):

    # --------------------------------------------------------
    # USER MUST BE LOGGED IN
    # --------------------------------------------------------
    logged_in_user_id = session.get("user_id")

    if not logged_in_user_id:
        return jsonify({
            "success": False,
            "message": "Please login to follow users."
        }), 401

    # --------------------------------------------------------
    # USER CANNOT FOLLOW THEMSELVES
    # --------------------------------------------------------
    if int(logged_in_user_id) == int(user_id):
        return jsonify({
            "success": False,
            "message": "You cannot follow yourself."
        }), 400

    connection = db

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection unavailable."
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # CHECK TARGET USER EXISTS
        # ----------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                name
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        # ----------------------------------------------------
        # CHECK EXISTING FOLLOW
        # ----------------------------------------------------
        cursor.execute("""
            SELECT id
            FROM cb_community_follows
            WHERE follower_id = %s
              AND following_id = %s
            LIMIT 1
        """, (
            logged_in_user_id,
            user_id
        ))

        existing_follow = cursor.fetchone()

        # ----------------------------------------------------
        # UNFOLLOW
        # ----------------------------------------------------
        if existing_follow:

            cursor.execute("""
                DELETE FROM cb_community_follows
                WHERE follower_id = %s
                  AND following_id = %s
            """, (
                logged_in_user_id,
                user_id
            ))

            connection.commit()

            return jsonify({
                "success": True,
                "following": False,
                "message": f"You unfollowed {target_user['name']}."
            })

        # ----------------------------------------------------
        # FOLLOW
        # ----------------------------------------------------
        cursor.execute("""
            INSERT INTO cb_community_follows
            (
                follower_id,
                following_id
            )
            VALUES
            (
                %s,
                %s
            )
        """, (
            logged_in_user_id,
            user_id
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "following": True,
            "message": f"You are now following {target_user['name']}."
        })

    except Error as e:

        connection.rollback()

        print(
            "Community follow database error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to update follow status."
        }), 500

    except Exception as e:

        connection.rollback()

        print(
            "Community follow error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to update follow status."
        }), 500

    finally:
        cursor.close()
       

     # ============================================================
# COMMUNITY PROFILE
# REAL USER PROFILE
# PHONE = FOUNDER ONLY
# ============================================================

@app.route("/community/profile/<int:user_id>")
def community_profile(user_id):

    connection = db

    if connection is None:
        return "Database connection unavailable", 500

    cursor = connection.cursor(dictionary=True)

    try:

        # ====================================================
        # LOGGED-IN USER
        # ====================================================

        logged_in_user_id = session.get("user_id")

        logged_in_role = str(
            session.get("role", "")
        ).strip().lower()

        is_founder = (
            logged_in_role == "founder"
        )

        # ====================================================
        # GET REAL PROFILE
        # ====================================================

        if is_founder:

            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    u.email,
                    u.phone,
                    u.role,
                    u.email_verified,
                    u.created_at,

                    up.location,
                    up.gender,
                    up.qualification,
                    up.profession,
                    up.bio,
                    up.profile_image

                FROM users u

                LEFT JOIN user_profiles up
                    ON u.id = up.user_id

                WHERE u.id = %s

                LIMIT 1
            """, (user_id,))

        else:

            cursor.execute("""
                SELECT
                    u.id,
                    u.name,
                    u.email,
                    NULL AS phone,
                    u.role,
                    u.email_verified,
                    u.created_at,

                    up.location,
                    up.gender,
                    up.qualification,
                    up.profession,
                    up.bio,
                    up.profile_image

                FROM users u

                LEFT JOIN user_profiles up
                    ON u.id = up.user_id

                WHERE u.id = %s

                LIMIT 1
            """, (user_id,))

        profile_user = cursor.fetchone()

        # ====================================================
        # USER NOT FOUND
        # ====================================================

        if not profile_user:
            return "Community member not found", 404

        # ====================================================
        # FOLLOW STATUS
        # ====================================================

        is_following = False

        if (
            logged_in_user_id
            and logged_in_user_id != user_id
        ):

            cursor.execute("""
                SELECT id
                FROM cb_community_follows
                WHERE follower_id = %s
                  AND following_id = %s
                LIMIT 1
            """, (
                logged_in_user_id,
                user_id
            ))

            is_following = bool(
                cursor.fetchone()
            )

        # ====================================================
        # FOLLOWER COUNT
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM cb_community_follows
            WHERE following_id = %s
        """, (user_id,))

        follower_result = cursor.fetchone()

        followers_count = (
            int(follower_result["total"])
            if follower_result
            else 0
        )

        # ====================================================
        # FOLLOWING COUNT
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM cb_community_follows
            WHERE follower_id = %s
        """, (user_id,))

        following_result = cursor.fetchone()

        following_count = (
            int(following_result["total"])
            if following_result
            else 0
        )

        # ====================================================
        # REAL POSTS BY THIS USER
        # ====================================================

        cursor.execute("""
            SELECT
                p.id,
                p.user_id,
                p.content,
                p.image_path,
                p.video_path,
                p.audio_path,
                p.created_at,

                u.name,
                u.role,

                up.profile_image,
                up.location,

                (
                    SELECT COUNT(*)
                    FROM cb_community_post_likes l
                    WHERE l.post_id = p.id
                ) AS like_count,

                (
                    SELECT COUNT(*)
                    FROM cb_community_post_comments c
                    WHERE c.post_id = p.id
                ) AS comment_count

            FROM cb_community_posts p

            INNER JOIN users u
                ON p.user_id = u.id

            LEFT JOIN user_profiles up
                ON u.id = up.user_id

            WHERE p.user_id = %s

            ORDER BY p.created_at DESC
        """, (user_id,))

        community_posts = cursor.fetchall()

        # ====================================================
        # CHECK USER'S LIKES
        # ====================================================

        for post in community_posts:

            post["liked_by_me"] = False

            if logged_in_user_id:

                cursor.execute("""
                    SELECT id
                    FROM cb_community_post_likes
                    WHERE post_id = %s
                      AND user_id = %s
                    LIMIT 1
                """, (
                    post["id"],
                    logged_in_user_id
                ))

                if cursor.fetchone():
                    post["liked_by_me"] = True

        # ====================================================
        # PROFILE PAGE
        # ====================================================

        return render_template(
            "community_profile.html",

            profile_user=profile_user,

            community_posts=community_posts,

            is_founder=is_founder,

            is_following=is_following,

            followers_count=followers_count,

            following_count=following_count,

            logged_in_user_id=logged_in_user_id
        )

    except Error as e:

        print(
            "Community profile database error:",
            e
        )

        return (
            "Unable to load community profile",
            500
        )

    finally:

        cursor.close()
        # ============================================================
# SHARE COMMUNITY POST
# REAL DATABASE SHARE
# ============================================================

@app.route(
    "/community/post/<int:post_id>/share",
    methods=["POST"]
)
def share_community_post(post_id):

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Please login to share this post."
        }), 401

    conn = None
    cursor = None

    try:

        conn = db.get_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        # ====================================================
        # CHECK POST
        # ====================================================

        cursor.execute("""
            SELECT id
            FROM cb_community_posts
            WHERE id = %s
            LIMIT 1
        """, (post_id,))

        post = cursor.fetchone()

        if not post:

            return jsonify({
                "success": False,
                "message": "Post not found."
            }), 404

        # ====================================================
        # CHECK WHETHER THIS USER ALREADY SHARED
        # ====================================================

        cursor.execute("""
            SELECT id
            FROM cb_community_post_shares
            WHERE post_id = %s
              AND user_id = %s
            LIMIT 1
        """, (
            post_id,
            user_id
        ))

        existing_share = cursor.fetchone()

        # ====================================================
        # UNSHARE
        # ====================================================

        if existing_share:

            cursor.execute("""
                DELETE FROM cb_community_post_shares

                WHERE post_id = %s
                  AND user_id = %s
            """, (
                post_id,
                user_id
            ))

            shared = False

        # ====================================================
        # SHARE
        # ====================================================

        else:

            cursor.execute("""
                INSERT INTO cb_community_post_shares
                (
                    post_id,
                    user_id
                )

                VALUES
                (
                    %s,
                    %s
                )
            """, (
                post_id,
                user_id
            ))

            shared = True

        conn.commit()

        # ====================================================
        # REAL SHARE COUNT
        # ====================================================

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM cb_community_post_shares
            WHERE post_id = %s
        """, (post_id,))

        result = cursor.fetchone()

        share_count = (
            int(result["total"])
            if result
            else 0
        )

        return jsonify({

            "success": True,

            "shared": shared,

            "share_count":
                share_count
        })

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            "COMMUNITY SHARE ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message":
                "Unable to update the share."
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
# ============================================================
# CONTACT PAGE
# ============================================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# ============================================================
# TERMS & CONDITIONS
# ============================================================

@app.route("/terms")
def terms():

    return render_template(
        "terms.html"
    )


# ============================================================
# PRIVACY POLICY
# ============================================================

@app.route("/privacy")
def privacy():

    return render_template(
        "privacy.html"
    )


# ============================================================
# SEND EMAIL OTP USING GMAIL
# ============================================================

def send_email_otp(receiver_email, otp):

    if not GMAIL_APP_PASSWORD:
        print("GMAIL_APP_PASSWORD is not configured.")
        return False

    try:

        message = EmailMessage()

        message["From"] = GMAIL_SENDER
        message["To"] = receiver_email
        message["Subject"] = "CharityBridge - Email Verification OTP"

        message.set_content(
            f"""
CharityBridge - Email Verification

Hello,

Thank you for registering with CharityBridge.

Your email verification OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not create a CharityBridge account, please ignore this email.

Regards,
CharityBridge Team
"""
        )

        with smtplib.SMTP("smtp.gmail.com", 587) as server:

            server.starttls()

            server.login(
                GMAIL_SENDER,
                GMAIL_APP_PASSWORD
            )

            server.send_message(message)

        print(
            "OTP email sent successfully to:",
            receiver_email
        )

        return True

    except Exception as e:

        print(
            "OTP email error:",
            e
        )

        return False
    
# ============================================================
# SEND PASSWORD RESET OTP USING GMAIL
# Separate from registration OTP
# ============================================================

def send_password_reset_otp(receiver_email, otp):

    if not GMAIL_APP_PASSWORD:
        print("GMAIL_APP_PASSWORD is not configured.")
        return False

    try:

        message = EmailMessage()

        message["From"] = GMAIL_SENDER
        message["To"] = receiver_email
        message["Subject"] = "CharityBridge - Password Reset OTP"

        message.set_content(
            f"""
CharityBridge - Password Reset

Hello,

We received a request to reset your CharityBridge account password.

Your password reset OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request a password reset, please ignore this email.

Do not share this OTP with anyone.

Regards,
CharityBridge Team
"""
        )

        with smtplib.SMTP("smtp.gmail.com", 587) as server:

            server.starttls()

            server.login(
                GMAIL_SENDER,
                GMAIL_APP_PASSWORD
            )

            server.send_message(message)

        print(
            "Password reset OTP sent successfully to:",
            receiver_email
        )

        return True

    except Exception as e:

        print(
            "Password reset email error:",
            e
        )

        return False

    
    
# ============================================================
# SEND VOLUNTEER WORKFLOW EMAIL
# Separate from the login OTP email function
# ============================================================

def send_volunteer_workflow_email(receiver_email, subject, message_text):

    if not GMAIL_APP_PASSWORD:
        print("GMAIL_APP_PASSWORD is not configured.")
        return False

    try:
        message = EmailMessage()

        message["From"] = GMAIL_SENDER
        message["To"] = receiver_email
        message["Subject"] = subject

        message.set_content(
            f"""
CharityBridge - Volunteer Connection

Hello,

{message_text}

Regards,
CharityBridge Team
"""
        )

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(
                GMAIL_SENDER,
                GMAIL_APP_PASSWORD
            )
            server.send_message(message)

        print("Volunteer workflow email sent successfully.")
        return True

    except Exception as e:
        print("Volunteer workflow email error:", e)
        return False

    # ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # ========================================================
    # ONLY THIS EMAIL CAN BE FOUNDER
    # ========================================================
    FOUNDER_EMAIL = "lakshmisubramani021@gmail.com"

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        # IMPORTANT:
        # Role is NOT taken from the registration form.
        # Flask decides the role automatically.
        if email == FOUNDER_EMAIL.lower():
            role = "Founder"
        else:
            role = "user"

        otp = request.form.get(
            "otp",
            ""
        ).strip()

        # ====================================================
        # OTP VERIFICATION
        # ====================================================

        if otp:

            pending_user_id = session.get(
                "pending_registration_user_id"
            )

            pending_email = session.get(
                "pending_registration_email"
            )

            if not pending_user_id or not pending_email:
                flash(
                    "OTP session expired. Please register again.",
                    "error"
                )
                return redirect(
                    url_for("register")
                )

            if not otp.isdigit() or len(otp) != 6:
                flash(
                    "Please enter a valid 6-digit OTP.",
                    "error"
                )
                return render_template(
                    "register.html",
                    otp_required=True
                )

            connection = db

            if connection is None:
                flash(
                    "Database connection failed.",
                    "error"
                )
                return redirect(
                    url_for("register")
                )

            cursor = connection.cursor(
                dictionary=True
            )

            try:
                cursor.execute(
                    """
                    SELECT
                        id,
                        otp_hash,
                        expires_at,
                        attempts
                    FROM email_otps
                    WHERE user_id = %s
                    AND used_at IS NULL
                    AND purpose = 'verification'
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (pending_user_id,)
                )
                               

              

                otp_record = cursor.fetchone()

                if not otp_record:
                    flash(
                        "OTP not found. Please register again.",
                        "error"
                    )
                    return redirect(
                        url_for("register")
                    )

                if otp_record["attempts"] >= 5:
                    flash(
                        "Too many incorrect OTP attempts. Please register again.",
                        "error"
                    )
                    return redirect(
                        url_for("register")
                    )

                if datetime.now() > otp_record["expires_at"]:
                    flash(
                        "OTP has expired. Please register again to receive a new OTP.",
                        "error"
                    )
                    return redirect(
                        url_for("register")
                    )

                if not check_password_hash(
                    otp_record["otp_hash"],
                    otp
                ):

                    cursor.execute(
                        """
                        UPDATE email_otps
                        SET attempts = attempts + 1
                        WHERE id = %s
                        """,
                        (otp_record["id"],)
                    )

                    connection.commit()

                    remaining = (
                        4 -
                        otp_record["attempts"]
                    )

                    flash(
                        f"Incorrect OTP. {max(remaining, 0)} attempts remaining.",
                        "error"
                    )

                    return render_template(
                        "register.html",
                        otp_required=True
                    )

                # ============================================
                # VERIFY EMAIL
                # ============================================

                cursor.execute(
                    """
                    UPDATE users
                    SET
                        email_verified = 1,
                        role = %s
                    WHERE id = %s
                    AND email = %s
                    """,
                    (
                        role,
                        pending_user_id,
                        pending_email
                    )
                )

                cursor.execute(
                    """
                    UPDATE email_otps
                    SET used_at = NOW()
                    WHERE id = %s
                    """,
                    (otp_record["id"],)
                )

                connection.commit()

                session.pop(
                    "pending_registration_user_id",
                    None
                )

                session.pop(
                    "pending_registration_email",
                    None
                )

                flash(
                    "Email verified successfully. Registration completed. Please login.",
                    "success"
                )

                return redirect(
                    url_for("login")
                )

            except Error as e:

                connection.rollback()

                print(
                    "OTP verification error:",
                    e
                )

                flash(
                    "OTP verification failed.",
                    "error"
                )

                return render_template(
                    "register.html",
                    otp_required=True
                )

            finally:

                cursor.close()

                # Do NOT close shared ReconnectableDB connection.

        # ====================================================
        # BASIC VALIDATION
        # ====================================================

        if not name or not email or not password or not phone:

            flash(
                "Please fill all required fields.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        # ====================================================
        # EMAIL FORMAT VALIDATION
        # ====================================================

        email_pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

        if not re.match(
            email_pattern,
            email
        ):

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        # ====================================================
        # PHONE VALIDATION
        # ====================================================

        phone_digits = re.sub(
            r"\D",
            "",
            phone
        )

        if (
            len(phone_digits) < 10
            or len(phone_digits) > 15
        ):

            flash(
                "Please enter a valid phone number.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        # ====================================================
        # PASSWORD VALIDATION
        # ====================================================

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        # ====================================================
        # DATABASE CONNECTION
        # ====================================================

        connection = db

        if connection is None:

            flash(
                "Database connection failed.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            # =================================================
            # CHECK EXISTING EMAIL
            # =================================================

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    email_verified
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cursor.fetchone()

            # =================================================
            # IF EMAIL ALREADY VERIFIED
            # =================================================

            if (
                existing_user
                and int(
                    existing_user.get(
                        "email_verified",
                        0
                    )
                ) == 1
            ):

                flash(
                    "Email already registered. Please login.",
                    "error"
                )

                return redirect(
                    url_for("login")
                )

            # =================================================
            # HASH PASSWORD
            # =================================================

            hashed_password = generate_password_hash(
                password
            )

            # =================================================
            # CREATE OR UPDATE UNVERIFIED USER
            # =================================================

            if existing_user:

                user_id = existing_user["id"]

                cursor.execute(
                    """
                    UPDATE users
                    SET
                        name = %s,
                        password = %s,
                        phone = %s,
                        role = %s,
                        email_verified = 0
                    WHERE id = %s
                    """,
                    (
                        name,
                        hashed_password,
                        phone_digits,
                        role,
                        user_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO users
                    (
                        name,
                        email,
                        password,
                        phone,
                        role,
                        email_verified
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        0
                    )
                    """,
                    (
                        name,
                        email,
                        hashed_password,
                        phone_digits,
                        role
                    )
                )

                user_id = cursor.lastrowid

            # =================================================
            # GENERATE 6-DIGIT OTP
            # =================================================

            otp = f"{secrets.randbelow(1000000):06d}"

            # =================================================
            # HASH OTP
            # =================================================

            otp_hash = generate_password_hash(
                otp
            )

            expires_at = datetime.now() + timedelta(
                minutes=10
            )

            # =================================================
            # REMOVE OLD UNUSED OTPS
            # =================================================
            cursor.execute(
    """
    DELETE FROM email_otps
    WHERE user_id = %s
    AND used_at IS NULL
    AND purpose = 'verification'
    """,
    (user_id,)
)

            # =================================================
            # SAVE NEW OTP
            # =================================================

            cursor.execute(
                """
                INSERT INTO email_otps
                (
                    user_id,
                    otp_hash,
                    expires_at,
                    attempts
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    0
                )
                """,
                (
                    user_id,
                    otp_hash,
                    expires_at
                )
            )

            connection.commit()

            # =================================================
            # SEND OTP EMAIL
            # =================================================

            email_sent = send_email_otp(
                email,
                otp
            )

            if not email_sent:

                connection.rollback()

                flash(
                    "Unable to send OTP email. Please check email configuration.",
                    "error"
                )

                return redirect(
                    url_for("register")
                )

            # =================================================
            # STORE PENDING USER IN SESSION
            # =================================================

            session[
                "pending_registration_user_id"
            ] = user_id

            session[
                "pending_registration_email"
            ] = email

            flash(
                "A 6-digit OTP has been sent to your email. Please enter it to verify your account.",
                "success"
            )

            return render_template(
                "register.html",
                otp_required=True
            )

        except Error as e:

            connection.rollback()

            print(
                "Registration error:",
                e
            )

            flash(
                "Registration failed.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        finally:

            cursor.close()

            # Do NOT close shared ReconnectableDB connection.

    return render_template(
        "register.html",
        otp_required=False
    )

# ============================================================
# FORGOT PASSWORD - SEND RESET OTP
# ============================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        if not email:
            flash("Please enter your registered email address.", "error")
            return render_template("forgot_password.html")

        connection = db

        if connection is None:
            flash("Database connection failed.", "error")
            return render_template("forgot_password.html")

        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute(
                """
                SELECT id, email
                FROM users
                WHERE email = %s
                AND email_verified = 1
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user:
                flash(
                    "If this email is registered, password reset instructions will be sent.",
                    "success"
                )
                return render_template("forgot_password.html")

            user_id = user["id"]

            # Generate 6-digit OTP
            otp = f"{secrets.randbelow(1000000):06d}"

            # Hash OTP
            otp_hash = generate_password_hash(otp)

            expires_at = datetime.now() + timedelta(minutes=10)

            # Delete only previous unused password-reset OTPs
            cursor.execute(
                """
                DELETE FROM email_otps
                WHERE user_id = %s
                AND used_at IS NULL
                AND purpose = 'password_reset'
                """,
                (user_id,)
            )

            # Save new password-reset OTP
            cursor.execute(
                """
                INSERT INTO email_otps
                (
                    user_id,
                    otp_hash,
                    expires_at,
                    attempts,
                    purpose
                )
                VALUES (%s, %s, %s, 0, 'password_reset')
                """,
                (
                    user_id,
                    otp_hash,
                    expires_at
                )
            )

            connection.commit()

            # Send password-reset email
            email_sent = send_password_reset_otp(
                email,
                otp
            )

            if not email_sent:

                cursor.execute(
                    """
                    UPDATE email_otps
                    SET used_at = NOW()
                    WHERE user_id = %s
                    AND purpose = 'password_reset'
                    AND used_at IS NULL
                    """,
                    (user_id,)
                )

                connection.commit()

                flash(
                    "Unable to send OTP. Please try again later.",
                    "error"
                )

                return render_template("forgot_password.html")

            # Store pending reset information
            session["password_reset_user_id"] = user_id
            session.pop("password_reset_verified", None)

            flash(
                "A password-reset OTP has been sent to your registered email.",
                "success"
            )

            return redirect(
                url_for("verify_reset_otp")
            )

        except Error as e:

            connection.rollback()

            print("Forgot password error:", e)

            flash(
                "Something went wrong. Please try again.",
                "error"
            )

            return render_template("forgot_password.html")

        finally:

            cursor.close()

    return render_template("forgot_password.html")
@app.route("/verify-reset-otp", methods=["GET", "POST"])
def verify_reset_otp():

    user_id = session.get("password_reset_user_id")

    if not user_id:
        flash("Please request a password reset first.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        otp = request.form.get("otp", "").strip()

        if not otp:
            flash("Please enter the OTP.", "error")
            return render_template("verify_reset_otp.html")

        connection = db

        if connection is None:
            flash("Database connection failed.", "error")
            return render_template("verify_reset_otp.html")

        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT id, otp_hash, expires_at, attempts
                FROM email_otps
                WHERE user_id = %s
                AND purpose = 'password_reset'
                AND used_at IS NULL
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,)
            )

            otp_record = cursor.fetchone()

            if not otp_record:
                flash("OTP not found. Please request a new OTP.", "error")
                return render_template("verify_reset_otp.html")

            if otp_record["attempts"] >= 5:
                flash("Too many attempts. Please request a new OTP.", "error")
                return render_template("verify_reset_otp.html")

            if otp_record["expires_at"] < datetime.now():
                flash("OTP expired. Please request a new OTP.", "error")
                return render_template("verify_reset_otp.html")

            if not check_password_hash(otp_record["otp_hash"], otp):
                cursor.execute(
                    """
                    UPDATE email_otps
                    SET attempts = attempts + 1
                    WHERE id = %s
                    """,
                    (otp_record["id"],)
                )
                connection.commit()

                flash("Incorrect OTP. Please try again.", "error")
                return render_template("verify_reset_otp.html")

            session["password_reset_verified"] = True

            flash("OTP verified successfully.", "success")

            return redirect(url_for("reset_password"))

        except Error as e:
            connection.rollback()
            print("Reset OTP verification error:", e)
            flash("Something went wrong. Please try again.", "error")
            return render_template("verify_reset_otp.html")

        finally:
            cursor.close()

    return render_template("verify_reset_otp.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    user_id = session.get("password_reset_user_id")

    if not user_id or not session.get("password_reset_verified"):
        flash("Please verify your password reset OTP first.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not new_password or not confirm_password:
            flash("Please fill in both password fields.", "error")
            return render_template("reset_password.html")

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("reset_password.html")

        if len(new_password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return render_template("reset_password.html")

        connection = db

        if connection is None:
            flash("Database connection failed.", "error")
            return render_template("reset_password.html")

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                UPDATE users
                SET password = %s
                WHERE id = %s
                """,
                (generate_password_hash(new_password), user_id)
            )

            cursor.execute(
                """
                UPDATE email_otps
                SET used_at = NOW()
                WHERE user_id = %s
                AND purpose = 'password_reset'
                AND used_at IS NULL
                """,
                (user_id,)
            )

            connection.commit()

            session.pop("password_reset_user_id", None)
            session.pop("password_reset_verified", None)

            flash("Your password has been reset successfully. Please log in.", "success")

            return redirect(url_for("login"))

        except Error as e:
            connection.rollback()
            print("Password reset error:", e)
            flash("Unable to reset password. Please try again.", "error")
            return render_template("reset_password.html")

        finally:
            cursor.close()

    return render_template("reset_password.html")




# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        connection = db

        if connection is None:

            flash(
                "Database connection failed.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()


            if (
                user
                and check_password_hash(
                    user["password"],
                    password
                )
            ):

                if user["email_verified"] != 1:

                    flash(
                        "Please verify your email with the OTP before logging in.",
                        "error"
                    )

                    return redirect(
                        url_for("register")
                    )
                    
                # SAVE THE LOGGED-IN USER IN THE SESSION
                session.clear()

                session["user_id"] = user["id"]
                session["user_name"] = user.get("name") or "Community Member"
                session["user_email"] = user.get("email") or ""
                session["role"] = user.get("role") or "user"



              

                return redirect(
                    url_for("dashboard")
                )

            else:

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("login")
                )

        except Error as e:

            print(
                "Login error:",
                e
            )

            flash(
                "Login failed.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        finally:

            cursor.close()

            # Do not close ReconnectableDB.


    return render_template(
        "login.html"
    )
# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    user_name = session.get(
        "user_name",
        "Community Member"
    )

    user_role = session.get(
        "role",
        "user"
    )

    user_email = ""

    # ========================================================
    # DEFAULT VALUES
    # ========================================================

    total_users = 0
    total_volunteers = 0
    total_help_requests = 0

    successful_donations = 0
    total_donation_amount = 0

    my_donations = 0
    my_donation_amount = 0

    my_help_requests = 0
    my_volunteer_activity = 0

    pending_requests = 0
    accepted_requests = 0

    my_requests = []
    recent_responses = []

    unread_notifications = 0
    recent_notifications = []

    unread_messages = 0
    chat_messages = []

    # ========================================================
    # REAL GRAPH DATA
    # ========================================================

    impact_labels = []
    impact_values = []

    connection = db

    if connection is not None:

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            # =================================================
            # CURRENT USER
            # =================================================

            cursor.execute("""
                SELECT
                    name,
                    email,
                    role
                FROM users
                WHERE id = %s
                LIMIT 1
            """, (user_id,))

            current_user = cursor.fetchone()

            if current_user:

                user_name = (
                    current_user.get("name")
                    or user_name
                )

                user_email = (
                    current_user.get("email")
                    or ""
                )

                user_role = (
                    current_user.get("role")
                    or user_role
                )

            # =================================================
            # TOTAL USERS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM users
            """)

            result = cursor.fetchone()

            total_users = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # TOTAL VOLUNTEERS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM volunteers
            """)

            result = cursor.fetchone()

            total_volunteers = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # TOTAL HELP REQUESTS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM help_requests
            """)

            result = cursor.fetchone()

            total_help_requests = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # SUCCESSFUL DONATIONS
            # =================================================

            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(amount), 0) AS amount
                FROM money_donations
                WHERE status = 'Success'
            """)

            result = cursor.fetchone()

            if result:

                successful_donations = (
                    result["total"]
                    or 0
                )

                total_donation_amount = (
                    result["amount"]
                    or 0
                )

            # =================================================
            # MY DONATIONS
            # =================================================

            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(amount), 0) AS amount
                FROM money_donations
                WHERE user_id = %s
                AND status = 'Success'
            """, (user_id,))

            result = cursor.fetchone()

            if result:

                my_donations = (
                    result["total"]
                    or 0
                )

                my_donation_amount = (
                    result["amount"]
                    or 0
                )

            # =================================================
            # MY HELP REQUESTS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM help_requests
                WHERE user_id = %s
            """, (user_id,))

            result = cursor.fetchone()

            my_help_requests = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # MY VOLUNTEER ACTIVITY
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM volunteers
                WHERE user_id = %s
            """, (user_id,))

            result = cursor.fetchone()

            my_volunteer_activity = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # GLOBAL PENDING REQUESTS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM help_requests
                WHERE status = 'Pending'
            """)

            result = cursor.fetchone()

            pending_requests = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # GLOBAL ACCEPTED REQUESTS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM help_requests
                WHERE status = 'Accepted'
            """)

            result = cursor.fetchone()

            accepted_requests = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # MY RECENT REQUESTS
            # =================================================

            cursor.execute("""
                SELECT
                    hr.id,
                    hr.user_id,
                    hr.request_type,
                    hr.description,
                    hr.location,
                    hr.status,
                    hr.created_at,
                    u.name AS requester_name,
                    u.phone AS requester_phone
                FROM help_requests hr
                JOIN users u
                    ON hr.user_id = u.id
                WHERE hr.user_id = %s
                ORDER BY hr.id DESC
                LIMIT 5
            """, (user_id,))

            my_requests = cursor.fetchall()

            # =================================================
            # RECENT SUPPORT RESPONSES
            # =================================================

            cursor.execute("""
                SELECT
                    md.id,
                    md.amount,
                    md.payment_method,
                    md.status,
                    md.transaction_id,
                    md.created_at,
                    u.id AS donor_id,
                    u.name AS donor_name
                FROM money_donations md
                JOIN users u
                    ON md.user_id = u.id
                WHERE md.status = 'Success'
                ORDER BY md.created_at DESC
                LIMIT 5
            """)

            recent_responses = cursor.fetchall()

            # =================================================
            # UNREAD NOTIFICATIONS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM cb_notifications
                WHERE user_id = %s
                AND is_read = 0
            """, (user_id,))

            result = cursor.fetchone()

            unread_notifications = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # RECENT NOTIFICATIONS
            # =================================================

            cursor.execute("""
                SELECT
                    id,
                    title,
                    message,
                    is_read,
                    created_at
                FROM cb_notifications
                WHERE user_id = %s
                ORDER BY id DESC
                LIMIT 8
            """, (user_id,))

            recent_notifications = cursor.fetchall()

            # =================================================
            # PRIVATE CHAT UNREAD COUNT
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM cb_private_messages
                WHERE receiver_id = %s
                AND is_read = 0
            """, (user_id,))

            result = cursor.fetchone()

            unread_messages = (
                result["total"]
                if result
                else 0
            )

            # =================================================
            # REAL IMPACT GRAPH DATA
            #
            # Uses successful donations from the database.
            # Each point represents the number of successful
            # donations for that month.
            # =================================================

            cursor.execute("""
                SELECT
                    DATE_FORMAT(
                        MIN(created_at),
                        '%b'
                    ) AS month,
                    COUNT(*) AS total
                FROM money_donations
                WHERE status = 'Success'
                GROUP BY
                    YEAR(created_at),
                    MONTH(created_at)
                ORDER BY
                    YEAR(created_at),
                    MONTH(created_at)
                LIMIT 6
            """)


            impact_rows = cursor.fetchall()

            impact_labels = [
                row["month"]
                for row in impact_rows
                if row.get("month")
            ]

            impact_values = [
                int(row["total"] or 0)
                for row in impact_rows
            ]

        except Error as e:

            print(
                "Dashboard database error:",
                e
            )

        finally:

            cursor.close()

    # ========================================================
    # FOUNDER / ADMIN CHECK
    # ========================================================

    is_founder = (
        str(user_role).strip().lower()
        in [
            "founder",
            "admin"
        ]
    )

    # ========================================================
    # DASHBOARD TEMPLATE
    # ========================================================

    return render_template(
        "dashboard.html",

        user_name=user_name,

        user_email=user_email,

        user_role=user_role,

        total_users=total_users,

        total_volunteers=total_volunteers,

        total_help_requests=total_help_requests,

        successful_donations=successful_donations,

        total_donation_amount=total_donation_amount,

        my_donations=my_donations,

        my_donation_amount=my_donation_amount,

        my_help_requests=my_help_requests,

        my_volunteer_activity=my_volunteer_activity,

        pending_requests=pending_requests,

        accepted_requests=accepted_requests,

        my_requests=my_requests,

        recent_responses=recent_responses,

        unread_notifications=unread_notifications,

        recent_notifications=recent_notifications,

        unread_messages=unread_messages,

        chat_messages=chat_messages,

        is_founder=is_founder,
        impact_labels=impact_labels,
        impact_values=impact_values
)

# ============================================================
# ELDERLY CARE SUPPORT MODULE
# ============================================================

@app.route("/elderly-care", methods=["GET", "POST"])
def elderly_care():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    help_types = [
        "Grocery Assistance",
        "Medicine Collection",
        "Hospital Visit",
        "Household Tasks",
        "Companionship",
        "Other"
    ]

    error_message = ""
    success_message = ""
    my_requests = []
    all_requests = []

    connection = db

    if connection is None:
        error_message = "Database connection is unavailable."
        return render_template(
            "elderly_care.html",
            help_types=help_types,
            my_requests=[],
            error_message=error_message,
            success_message=success_message
        )

    cursor = connection.cursor(dictionary=True)

    try:
        # Create the module's table if it doesn't exist.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cb_elderly_care_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                help_type VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                area VARCHAR(150) NOT NULL,
                preferred_time VARCHAR(100) DEFAULT NULL,
                status VARCHAR(30) NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_elderly_user (user_id),
                INDEX idx_elderly_status (status)
            )
        """)
        connection.commit()

        if request.method == "POST":
            help_type = request.form.get("help_type", "").strip()
            description = request.form.get("description", "").strip()
            area = request.form.get("area", "").strip()
            preferred_time = request.form.get("preferred_time", "").strip()

            if help_type not in help_types:
                error_message = "Please select a valid type of help."

            elif not description or not area:
                error_message = "Please enter the task details and general area."

            elif len(description) > 3000 or len(area) > 150:
                error_message = "Please shorten the details or area."

            else:
                cursor.execute("""
                    INSERT INTO cb_elderly_care_requests
                    (
                        user_id,
                        help_type,
                        description,
                        area,
                        preferred_time
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    user_id,
                    help_type,
                    description,
                    area,
                    preferred_time or None
                ))

                connection.commit()
                return redirect(url_for("elderly_care", submitted="1"))

        if request.args.get("submitted") == "1":
            success_message = "Your elderly care request was submitted successfully."

        # Show only requests submitted by the current user.
        cursor.execute("""
            SELECT
                id,
                help_type,
                description,
                area,
                preferred_time,
                status,
                created_at
            FROM cb_elderly_care_requests
            WHERE user_id = %s
            ORDER BY id DESC
        """, (user_id,))

        my_requests = cursor.fetchall()
                
        # Show elderly care requests submitted by all users
        cursor.execute("""
            SELECT
                id,
                user_id,
                help_type,
                description,
                area,
                preferred_time,
                status,
                created_at
            FROM cb_elderly_care_requests
            ORDER BY id DESC
        """)

        all_requests = cursor.fetchall()


        

    except Error as e:
        connection.rollback()
        print("Elderly Care database error:", e)
        error_message = "We couldn't process your request. Please try again."

    finally:
        cursor.close()

    return render_template(
    "elderly_care.html",
    help_types=help_types,
    my_requests=my_requests,
    all_requests=all_requests,
    error_message=error_message,
    success_message=success_message
)
    


# ============================================================
# NOTIFICATIONS PAGE
# ============================================================

@app.route("/notifications", methods=["GET"])
def notifications():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    user_name = session.get(
        "user_name",
        "Community Member"
    )

    unread_notifications = 0
    recent_notifications = []

    connection = db

    if connection is not None:
        cursor = connection.cursor(dictionary=True)

        try:
            # Get the logged-in user's name
            cursor.execute("""
                SELECT name
                FROM users
                WHERE id = %s
                LIMIT 1
            """, (user_id,))

            current_user = cursor.fetchone()

            if current_user and current_user.get("name"):
                user_name = current_user["name"]

            # Count unread notifications
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM cb_notifications
                WHERE user_id = %s
                AND is_read = 0
            """, (user_id,))

            result = cursor.fetchone()

            if result:
                unread_notifications = result.get("total", 0) or 0

            # Get this user's notifications
            cursor.execute("""
                SELECT
                    id,
                    title,
                    message,
                    is_read,
                    created_at
                FROM cb_notifications
                WHERE user_id = %s
                ORDER BY id DESC
            """, (user_id,))

            recent_notifications = cursor.fetchall()

        except Error as e:
            print("Notifications database error:", e)

        finally:
            cursor.close()

    return render_template(
        "notifications.html",
        user_name=user_name,
        unread_notifications=unread_notifications,
        recent_notifications=recent_notifications
    )


# ============================================================
# MARK ONE NOTIFICATION AS READ
# ============================================================

@app.route("/notifications/read/<int:notification_id>", methods=["POST"])
def mark_notification_read(notification_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("dashboard"))

    cursor = connection.cursor()

    try:
        # Only the notification's intended recipient can mark it read.
        cursor.execute("""
            UPDATE cb_notifications
            SET is_read = 1
            WHERE id = %s
              AND user_id = %s
        """, (
            notification_id,
            session["user_id"]
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        app.logger.exception("Mark notification as read failed")
        flash("Unable to update notification.", "error")

    finally:
        cursor.close()

    return redirect(url_for("dashboard"))

# ============================================================
# FOUNDER SENDS A PRIVATE MESSAGE TO ONE VOLUNTEER
# ============================================================

@app.route("/founder/send-volunteer-message", methods=["POST"])
def founder_send_volunteer_message():

    if "user_id" not in session:
        return redirect(url_for("login"))

    role = str(session.get("role", "")).strip().lower()

    if role not in ("founder", "admin"):
        flash("Only the Founder can message volunteers.", "error")
        return redirect(url_for("dashboard"))

    volunteer_user_id = request.form.get("volunteer_user_id", type=int)
    message_text = request.form.get("message", "").strip()

    if not volunteer_user_id or not message_text:
        flash("Select a volunteer and enter a message.", "error")
        return redirect(url_for("founder_food_deliveries"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("dashboard"))

    cursor = connection.cursor(dictionary=True)

    try:
        # Confirm that the recipient is a registered volunteer.
        cursor.execute("""
            SELECT u.id, u.name
            FROM users u
            JOIN volunteers v ON v.user_id = u.id
            WHERE u.id = %s
            LIMIT 1
        """, (volunteer_user_id,))

        volunteer = cursor.fetchone()

        if not volunteer:
            flash("The selected volunteer was not found.", "error")
            return redirect(url_for("founder_food_deliveries"))

        # Save the notification only for the selected volunteer.
        cursor.execute("""
            INSERT INTO cb_notifications (user_id, title, message)
            VALUES (%s, %s, %s)
        """, (
            volunteer_user_id,
            "Message from the Founder",
            message_text
        ))

        connection.commit()

        flash(
            f"Your message was sent to {volunteer['name']}.",
            "success"
        )

    except Exception:
        connection.rollback()
        app.logger.exception("Founder-to-volunteer message failed")
        flash("Unable to send the message. Please try again.", "error")

    finally:
        cursor.close()

    return redirect(url_for("founder_food_deliveries"))


# ============================================================
# FOUNDER FOOD DELIVERY PAGE
# ============================================================

@app.route("/founder/food-deliveries")
def founder_food_deliveries():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_role = str(session.get("role", "")).strip().lower()

    if user_role not in ("founder", "admin"):
        flash("Only the Founder can manage food deliveries.", "error")
        return redirect(url_for("dashboard"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("dashboard"))

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                hr.id AS request_id,
                hr.user_id AS requester_id,
                hr.description,
                hr.location,
                hr.quantity,
                hr.status AS request_status,
                hr.created_at,
                requester.name AS requester_name,
                requester.phone AS requester_phone
            FROM help_requests hr
            JOIN users requester
                ON requester.id = hr.user_id
            WHERE LOWER(hr.request_type) = 'food'
            ORDER BY hr.created_at DESC
        """)

        food_requests = cursor.fetchall()

        cursor.execute("""
            SELECT
                v.id AS volunteer_id,
                v.user_id,
                v.availability,
                v.skills,
                u.name,
                u.phone
            FROM volunteers v
            JOIN users u
                ON u.id = v.user_id
            WHERE LOWER(v.availability) = 'available'
            ORDER BY u.name
        """)

        available_volunteers = cursor.fetchall()

        cursor.execute("""
            SELECT
                d.id AS delivery_id,
                d.request_id,
                d.volunteer_id,
                d.status AS delivery_status,
                d.assigned_at,
                d.delivered_at,
                d.verified_at,
                requester.name AS requester_name,
                volunteer_user.name AS volunteer_name,
                volunteer_user.phone AS volunteer_phone
            FROM cb_food_deliveries d
            JOIN help_requests hr
                ON hr.id = d.request_id
            JOIN users requester
                ON requester.id = hr.user_id
            JOIN volunteers v
                ON v.id = d.volunteer_id
            JOIN users volunteer_user
                ON volunteer_user.id = v.user_id
            ORDER BY d.assigned_at DESC
        """)

        deliveries = cursor.fetchall()

        return render_template(
            "founder_food_deliveries.html",
            food_requests=food_requests,
            available_volunteers=available_volunteers,
            deliveries=deliveries
        )

    except Exception:
        app.logger.exception("Founder food delivery page failed")
        flash("Unable to load food deliveries.", "error")
        return redirect(url_for("dashboard"))

    finally:
        cursor.close()

# ============================================================
# ASSIGN A VOLUNTEER TO A FOOD REQUEST
# ============================================================

@app.route("/founder/food-deliveries/assign", methods=["POST"])
def assign_food_volunteer():
    if "user_id" not in session:
        return redirect(url_for("login"))

    role = str(session.get("role", "")).strip().lower()

    if role not in ("founder", "admin"):
        flash("Only the Founder can assign volunteers.", "error")
        return redirect(url_for("dashboard"))

    request_id = request.form.get("request_id", type=int)
    volunteer_id = request.form.get("volunteer_id", type=int)
    pickup_details = request.form.get("pickup_details", "").strip()

    if not request_id or not volunteer_id:
        flash("Select a food request and a volunteer.", "error")
        return redirect(url_for("founder_food_deliveries"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("dashboard"))

    cursor = connection.cursor(dictionary=True)

    try:
        # Confirm that this is a real food request.
        cursor.execute("""
            SELECT id, user_id, description
            FROM help_requests
            WHERE id = %s
              AND LOWER(request_type) = 'food'
            LIMIT 1
        """, (request_id,))

        food_request = cursor.fetchone()

        if not food_request:
            flash("Food request not found.", "error")
            return redirect(url_for("founder_food_deliveries"))

        # Confirm that the volunteer is registered and available.
        cursor.execute("""
            SELECT id, user_id
            FROM volunteers
            WHERE id = %s
              AND LOWER(availability) = 'available'
            LIMIT 1
        """, (volunteer_id,))

        volunteer = cursor.fetchone()

        if not volunteer:
            flash("This volunteer is not available.", "error")
            return redirect(url_for("founder_food_deliveries"))

        # Prevent duplicate active assignments for this request.
        cursor.execute("""
            SELECT id
            FROM cb_food_deliveries
            WHERE request_id = %s
              AND LOWER(status) NOT IN ('cancelled', 'rejected')
            LIMIT 1
        """, (request_id,))

        existing = cursor.fetchone()

        if existing:
            flash(
                "This food request already has a delivery assignment.",
                "error"
            )
            return redirect(url_for("founder_food_deliveries"))

        # Save the assignment using the volunteers.id value.
        cursor.execute("""
            INSERT INTO cb_food_deliveries
                (request_id, volunteer_id, assigned_by,
                 status, pickup_details)
            VALUES (%s, %s, %s, 'assigned', %s)
        """, (
            request_id,
            volunteer_id,
            int(session["user_id"]),
            pickup_details or None
        ))

        # Notify the requester.
        cursor.execute("""
            INSERT INTO cb_notifications
                (user_id, title, message)
            VALUES (%s, %s, %s)
        """, (
            food_request["user_id"],
            "Food Delivery Volunteer Assigned",
            "A volunteer has been assigned to your food request "
            f"#{request_id}. Please check your Food Delivery details."
        ))

        # Notify the volunteer.
        cursor.execute("""
            INSERT INTO cb_notifications
                (user_id, title, message)
            VALUES (%s, %s, %s)
        """, (
            volunteer["user_id"],
            "New Food Delivery Assignment",
            f"You have been assigned to food request #{request_id}."
        ))

        connection.commit()

        flash("Volunteer assigned successfully.", "success")

    except Exception:
        connection.rollback()
        app.logger.exception("Food volunteer assignment failed")
        flash("Unable to assign the volunteer. Please try again.", "error")

    finally:
        cursor.close()

    return redirect(url_for("founder_food_deliveries"))


       # ============================================================
# PROFILE PAGE
# ============================================================

@app.route("/profile")
def profile_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = None
    cursor = None

    upi_id = ""
    upi_qr_image = ""

    try:
        conn = db

        if conn is None:
            flash("Database connection failed.", "error")
            return redirect(url_for("dashboard"))

        cursor = conn.cursor(dictionary=True)

        # ---------------------------------------------------------
        # USER BASIC INFORMATION
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                phone,
                role
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            flash("User profile not found.", "error")
            return redirect(url_for("dashboard"))

        # ---------------------------------------------------------
        # USER PROFILE INFORMATION
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                location,
                gender,
                qualification,
                profession,
                bio,
                profile_image,
                upi_id,
                upi_qr_image
            FROM user_profiles
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        profile = cursor.fetchone()

        if profile:

            upi_id = profile.get("upi_id") or ""
            upi_qr_image = profile.get("upi_qr_image") or ""

            user_location = profile.get("location") or ""
            user_gender = profile.get("gender") or ""
            user_qualification = profile.get("qualification") or ""
            user_profession = profile.get("profession") or ""
            user_bio = profile.get("bio") or ""
            profile_image = profile.get("profile_image") or ""

        else:

            user_location = ""
            user_gender = ""
            user_qualification = ""
            user_profession = ""
            user_bio = ""
            profile_image = ""

        # ---------------------------------------------------------
        # DONATION TOTAL
        # ---------------------------------------------------------

        total_donations = 0
        donation_amount = 0

        try:

            cursor.execute("""
                SELECT
                    COUNT(*) AS total_count,
                    COALESCE(SUM(amount), 0) AS total_amount
                FROM money_donations
                WHERE user_id = %s
                  AND LOWER(COALESCE(status, '')) = 'success'
            """, (user_id,))

            donation_data = cursor.fetchone() or {}

            total_donations = int(
                donation_data.get("total_count") or 0
            )

            donation_amount = float(
                donation_data.get("total_amount") or 0
            )

        except Exception as donation_error:

            print(
                "Profile donation query skipped:",
                donation_error
            )

        # ---------------------------------------------------------
        # ITEM DONATIONS
        # ---------------------------------------------------------

        items_donated = 0

        try:

            cursor.execute("""
                SELECT COUNT(*) AS total_items
                FROM item_donations
                WHERE user_id = %s
            """, (user_id,))

            item_data = cursor.fetchone() or {}

            items_donated = int(
                item_data.get("total_items") or 0
            )

        except Exception as item_error:

            print(
                "Profile item donation query skipped:",
                item_error
            )

        # ---------------------------------------------------------
        # HELP REQUESTS
        # ---------------------------------------------------------

        help_requests = []

        try:

            cursor.execute("""
                SELECT
                    id,
                    request_type,
                    amount,
                    description,
                    location,
                    status,
                    created_at
                FROM help_requests
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
            """, (user_id,))

            help_requests = cursor.fetchall() or []

        except Exception as request_error:

            print(
                "Profile help request query skipped:",
                request_error
            )

        # ---------------------------------------------------------
        # PEOPLE HELPED
        # ---------------------------------------------------------

        people_helped = 0

        try:

            cursor.execute("""
                SELECT COUNT(DISTINCT hr.user_id) AS people_helped
                FROM cb_request_responses rr
                JOIN help_requests hr
                    ON hr.id = rr.request_id
                WHERE rr.helper_id = %s
                  AND LOWER(COALESCE(rr.status, '')) = 'accepted'
                  AND hr.user_id <> %s
            """, (user_id, user_id))

            helped_data = cursor.fetchone() or {}

            people_helped = int(
                helped_data.get("people_helped") or 0
            )

        except Exception as helped_error:

            print(
                "Profile people-helped query skipped:",
                helped_error
            )

        # ---------------------------------------------------------
        # RESPONSE HISTORY
        # ---------------------------------------------------------

        response_history = []

        try:

            cursor.execute("""
                SELECT
                    rr.id,
                    rr.request_id,
                    rr.status,
                    rr.message,
                    rr.created_at,
                    hr.request_type,
                    hr.amount,
                    hr.description,
                    hr.location
                FROM cb_request_responses rr
                LEFT JOIN help_requests hr
                    ON hr.id = rr.request_id
                WHERE rr.helper_id = %s
                ORDER BY rr.created_at DESC, rr.id DESC
            """, (user_id,))

            response_history = cursor.fetchall() or []

        except Exception as response_error:

            print(
                "Profile response history query skipped:",
                response_error
            )

        # ---------------------------------------------------------
        # RECENT ACTIVITY
        # ---------------------------------------------------------

        recent_activity = []

        try:

            cursor.execute("""
                SELECT
                    id,
                    request_type,
                    amount,
                    description,
                    status,
                    created_at
                FROM help_requests
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 10
            """, (user_id,))

            recent_activity = cursor.fetchall() or []

        except Exception as activity_error:

            print(
                "Profile recent activity query skipped:",
                activity_error
            )

        # ---------------------------------------------------------
        # DONATION GRAPH
        # ---------------------------------------------------------

        donation_graph = []

        try:

            cursor.execute("""
                SELECT
                    DATE(created_at) AS donation_date,
                    COALESCE(SUM(amount), 0) AS daily_amount
                FROM money_donations
                WHERE user_id = %s
                  AND LOWER(COALESCE(status, '')) = 'success'
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at) ASC
            """, (user_id,))

            donation_graph = cursor.fetchall() or []

        except Exception as graph_error:

            print(
                "Profile donation graph query skipped:",
                graph_error
            )

        # ---------------------------------------------------------
        # RENDER PROFILE
        # ---------------------------------------------------------

        return render_template(
            "profile.html",

            # Complete user object
            user=user,

            # Basic information
            user_name=user.get("name") or "",
            user_email=user.get("email") or "",
            user_phone=user.get("phone") or "",
            user_role=user.get("role") or "",

            # Profile information
            user_location=user_location,
            user_gender=user_gender,
            user_qualification=user_qualification,
            user_profession=user_profession,
            user_bio=user_bio,

            # Profile image
            profile_image=profile_image,

            # UPI information
            upi_id=upi_id,
            upi_qr_image=upi_qr_image,

            # Impact
            total_donations=total_donations,
            donation_amount=donation_amount,
            items_donated=items_donated,
            people_helped=people_helped,

            # Activity
            help_requests=help_requests,
            response_history=response_history,
            recent_activity=recent_activity,

            # Graph
            donation_graph=donation_graph
        )

    except Exception as e:

        print("PROFILE DATABASE ERROR:", e)

        try:
            if conn:
                conn.rollback()
        except Exception:
            pass

        flash(
            "Unable to load your profile.",
            "error"
        )

        return redirect(url_for("dashboard"))

    finally:

        if cursor:

            try:
                cursor.close()
            except Exception:
                pass


# ============================================================
# SAVE UPI ID + UPLOAD UPI QR CODE
# ============================================================

@app.route("/profile/save-upi", methods=["POST"])
def save_upi_id():

    # ---------------------------------------------------------
    # LOGIN CHECK
    # ---------------------------------------------------------

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # ---------------------------------------------------------
    # FORM DATA
    # ---------------------------------------------------------

    upi_id = request.form.get("upi_id", "").strip()

    qr_file = request.files.get("upi_qr_image")

    allowed_extensions = {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }

    qr_filename = None
    conn = None
    cursor = None

    try:

        # =====================================================
        # VALIDATE UPI ID
        # =====================================================

        if upi_id:

            if len(upi_id) > 100:

                flash(
                    "UPI ID is too long.",
                    "error"
                )

                return redirect(
                    url_for("profile_page")
                )

            if "@" not in upi_id:

                flash(
                    "Please enter a valid UPI ID, for example name@upi.",
                    "error"
                )

                return redirect(
                    url_for("profile_page")
                )

        # =====================================================
        # UPLOAD QR IMAGE
        # =====================================================

        if qr_file and qr_file.filename:

            original_filename = qr_file.filename.strip()

            # -------------------------------------------------
            # CHECK EXTENSION
            # -------------------------------------------------

            if "." not in original_filename:

                flash(
                    "Please upload a valid QR image.",
                    "error"
                )

                return redirect(
                    url_for("profile_page")
                )

            extension = (
                original_filename
                .rsplit(".", 1)[1]
                .lower()
            )

            if extension not in allowed_extensions:

                flash(
                    "QR image must be PNG, JPG, JPEG or WEBP.",
                    "error"
                )

                return redirect(
                    url_for("profile_page")
                )

            # =================================================
            # CREATE UPLOAD DIRECTORY
            # =================================================

            upload_folder = os.path.join(
                app.root_path,
                "static",
                "images",
                "upi_qr"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            # =================================================
            # UNIQUE QR FILE NAME
            # =================================================

            qr_filename = (
                f"upi_qr_{user_id}_"
                f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                f".{extension}"
            )

            qr_path = os.path.join(
                upload_folder,
                qr_filename
            )

            # =================================================
            # SAVE QR IMAGE
            # =================================================

            qr_file.save(qr_path)

        # =====================================================
        # DATABASE CONNECTION
        # =====================================================

        db_connection = ReconnectableDB()

        conn = db_connection.get_connection()

        if conn is None:

            raise Exception(
                "Database connection failed."
            )

        cursor = conn.cursor(
            dictionary=True
        )

        # =====================================================
        # CHECK EXISTING PROFILE
        # =====================================================

        cursor.execute("""
            SELECT
                id,
                upi_id,
                upi_qr_image
            FROM user_profiles
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        profile = cursor.fetchone()

        # =====================================================
        # UPDATE EXISTING PROFILE
        # =====================================================

        if profile:

            old_qr_image = (
                profile.get("upi_qr_image")
                or ""
            )

            # -------------------------------------------------
            # NEW QR IMAGE UPLOADED
            # -------------------------------------------------

            if qr_filename:

                cursor.execute("""
                    UPDATE user_profiles
                    SET
                        upi_id = %s,
                        upi_qr_image = %s
                    WHERE user_id = %s
                """, (
                    upi_id or None,
                    qr_filename,
                    user_id
                ))

                # ---------------------------------------------
                # DELETE OLD QR IMAGE
                # ---------------------------------------------

                if old_qr_image:

                    old_qr_path = os.path.join(
                        app.root_path,
                        "static",
                        "images",
                        "upi_qr",
                        old_qr_image
                    )

                    try:

                        if os.path.exists(
                            old_qr_path
                        ):

                            os.remove(
                                old_qr_path
                            )

                    except Exception as delete_error:

                        print(
                            "OLD QR DELETE ERROR:",
                            delete_error
                        )

            # -------------------------------------------------
            # ONLY UPI ID UPDATED
            # -------------------------------------------------

            else:

                cursor.execute("""
                    UPDATE user_profiles
                    SET
                        upi_id = %s
                    WHERE user_id = %s
                """, (
                    upi_id or None,
                    user_id
                ))

        # =====================================================
        # CREATE NEW PROFILE
        # =====================================================

        else:

            cursor.execute("""
                INSERT INTO user_profiles
                (
                    user_id,
                    upi_id,
                    upi_qr_image
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
            """, (
                user_id,
                upi_id or None,
                qr_filename
            ))

        # =====================================================
        # COMMIT
        # =====================================================

        conn.commit()

        flash(
            "Payment details saved successfully.",
            "success"
        )

    # =========================================================
    # ERROR HANDLING
    # =========================================================

    except Exception as e:

        print(
            "SAVE UPI / QR ERROR:",
            e
        )

        # -----------------------------------------------------
        # ROLLBACK DATABASE
        # -----------------------------------------------------

        try:

            if conn:
                conn.rollback()

        except Exception as rollback_error:

            print(
                "UPI ROLLBACK ERROR:",
                rollback_error
            )

        # -----------------------------------------------------
        # DELETE NEW QR IF DATABASE FAILED
        # -----------------------------------------------------

        if qr_filename:

            try:

                failed_file = os.path.join(
                    app.root_path,
                    "static",
                    "images",
                    "upi_qr",
                    qr_filename
                )

                if os.path.exists(
                    failed_file
                ):

                    os.remove(
                        failed_file
                    )

            except Exception as cleanup_error:

                print(
                    "QR CLEANUP ERROR:",
                    cleanup_error
                )

        flash(
            "Unable to save your payment details.",
            "error"
        )

    # =========================================================
    # CLOSE CURSOR
    # =========================================================

    finally:

        if cursor:

            try:
                cursor.close()

            except Exception as cursor_error:

                print(
                    "UPI CURSOR CLOSE ERROR:",
                    cursor_error
                )

    # =========================================================
    # RETURN TO PROFILE
    # =========================================================

    return redirect(
        url_for("profile_page")
    )



# ============================================================
# CHARITYBRIDGE PAYMENT HISTORY
# ============================================================

@app.route("/payment/history")
def payment_history():

    if "user_id" not in session:
        flash("Please log in to view payment history.", "error")
        return redirect(url_for("login"))

    user_id = int(session["user_id"])
    conn = None
    cursor = None
    payments = []

    try:
        conn = db.get_connection()

        if conn is None:
            flash("Database connection failed.", "error")
            return redirect(url_for("dashboard"))

        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                MAX(p.id) AS id,
                p.request_id,
                p.helper_id,

                MAX(p.gateway_order_id) AS gateway_order_id,
                MAX(p.gateway_payment_id) AS gateway_payment_id,
                SUM(p.amount_paise) AS amount_paise,

                CASE
                    WHEN SUM(
                        CASE
                            WHEN LOWER(p.status) = 'verified'
                            THEN 1 ELSE 0
                        END
                    ) = COUNT(*) THEN 'verified'

                    WHEN SUM(
                        CASE
                            WHEN LOWER(p.status) IN (
                                'requester_confirmed',
                                'verified'
                            )
                            THEN 1 ELSE 0
                        END
                    ) = COUNT(*) THEN 'requester_confirmed'

                    ELSE 'reported'
                END AS status,

                MIN(p.created_at) AS created_at,
                COALESCE(
    MAX(
        CASE
            WHEN LOWER(p.status) IN (
                'requester_confirmed',
                'verified'
            )
            THEN p.verified_at
        END
    ),
    (
        SELECT MAX(r.recipient_decided_at)
        FROM cb_payment_receipts r
        INNER JOIN cb_payment_records p2
            ON p2.id = r.payment_id
        WHERE p2.request_id = p.request_id
          AND p2.helper_id = p.helper_id
          AND r.recipient_decision = 'confirmed'
    )
) AS verified_at,
                COUNT(*) AS record_count,

                hr.user_id AS requester_id,
                hr.request_type,
                hr.amount AS requested_amount,

                helper.name AS helper_name,
                requester.name AS requester_name,

                (
                    SELECT p2.id
                    FROM cb_payment_records p2
                    WHERE p2.request_id = p.request_id
                      AND p2.helper_id = p.helper_id
                    ORDER BY p2.created_at DESC, p2.id DESC
                    LIMIT 1
                ) AS payment_id,

                (
                    SELECT r.id
                    FROM cb_payment_receipts r
                    INNER JOIN cb_payment_records p2
                        ON p2.id = r.payment_id
                    WHERE p2.request_id = p.request_id
                      AND p2.helper_id = p.helper_id
                    ORDER BY p2.created_at DESC, p2.id DESC
                    LIMIT 1
                ) AS receipt_id,

                (
                    SELECT r.recipient_decision
                    FROM cb_payment_receipts r
                    INNER JOIN cb_payment_records p2
                        ON p2.id = r.payment_id
                    WHERE p2.request_id = p.request_id
                      AND p2.helper_id = p.helper_id
                    ORDER BY p2.created_at DESC, p2.id DESC
                    LIMIT 1
                ) AS receipt_decision,

                (
                    SELECT r.recipient_note
                    FROM cb_payment_receipts r
                    INNER JOIN cb_payment_records p2
                        ON p2.id = r.payment_id
                    WHERE p2.request_id = p.request_id
                      AND p2.helper_id = p.helper_id
                    ORDER BY p2.created_at DESC, p2.id DESC
                    LIMIT 1
                ) AS recipient_note,

                (
                    SELECT r.recipient_decided_at
                    FROM cb_payment_receipts r
                    INNER JOIN cb_payment_records p2
                        ON p2.id = r.payment_id
                    WHERE p2.request_id = p.request_id
                      AND p2.helper_id = p.helper_id
                    ORDER BY p2.created_at DESC, p2.id DESC
                    LIMIT 1
                ) AS recipient_decided_at,

                (
                    SELECT r.receipt_filename
                    FROM cb_payment_receipts r
                    INNER JOIN cb_payment_records p2
                        ON p2.id = r.payment_id
                    WHERE p2.request_id = p.request_id
                      AND p2.helper_id = p.helper_id
                    ORDER BY r.uploaded_at DESC, r.id DESC
                    LIMIT 1
                ) AS receipt_filename

                

            FROM cb_payment_records p

            INNER JOIN help_requests hr
                ON hr.id = p.request_id

            LEFT JOIN users helper
                ON helper.id = p.helper_id

            LEFT JOIN users requester
                ON requester.id = hr.user_id

            WHERE p.helper_id = %s
               OR hr.user_id = %s

            GROUP BY
                p.request_id,
                p.helper_id,
                hr.user_id,
                hr.request_type,
                hr.amount,
                helper.name,
                requester.name

            ORDER BY MAX(p.created_at) DESC, p.request_id DESC
        """, (user_id, user_id))

        payments = cursor.fetchall() or []

        # ----------------------------------------------------
        # PREPARE VALUES FOR THE TEMPLATE
        # ----------------------------------------------------

        for payment in payments:

            payment["is_helper"] = (
                int(payment["helper_id"]) == user_id
            )

            payment["is_requester"] = (
                int(payment["requester_id"]) == user_id
            )

            payment["amount_display"] = (
                f"₹{int(payment['amount_paise'] or 0) / 100:,.2f}"
            )

            payment["receipt_decision"] = (
                payment.get("receipt_decision") or "pending"
            )

        return render_template(
            "payment_history.html",
            payments=payments,
            current_user_id=user_id
        )

    except Exception:
        app.logger.exception("Payment history page failed")
        print("PAYMENT HISTORY ERROR:", repr(__import__("sys").exc_info()[1]))

        flash(
            "Unable to load payment history. Please check the "
            "payment receipt table and try again.",
            "error"
        )

        return render_template(
            "payment_history.html",
            payments=[],
            current_user_id=user_id
        )

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()

# ============================================================
# DYNAMIC PAYMENT QR FOR A HELP OFFER
# ============================================================

@app.route("/response/payment-qr/<int:response_id>")
def payment_qr_for_response(response_id):
    if "user_id" not in session:
        return "Please log in first.", 401

    helper_id = session["user_id"]
    conn = None
    cursor = None

    try:
        db_connection = ReconnectableDB()
        conn = db_connection.get_connection()

        if conn is None:
            return "Database connection failed.", 503

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                cr.id AS response_id,
                hr.id AS request_id,
                hr.request_type,
                hr.amount,
                u.name AS requester_name,
                up.upi_id AS requester_upi_id
            FROM cb_request_responses cr
            INNER JOIN help_requests hr
                ON cr.request_id = hr.id
            INNER JOIN users u
                ON hr.user_id = u.id
            LEFT JOIN user_profiles up
                ON hr.user_id = up.user_id
            WHERE cr.id = %s
              AND cr.helper_id = %s
            LIMIT 1
            """,
            (response_id, helper_id)
        )

        payment = cursor.fetchone()

        if not payment:
            return "Help offer not found.", 404

        if str(payment.get("request_type") or "").lower() != "money":
            return "QR payment is only available for money requests.", 400

        upi_id = (payment.get("requester_upi_id") or "").strip()

        if not upi_id or "@" not in upi_id:
            return "The requester has not saved a valid UPI ID.", 400

        try:
            amount = float(payment["amount"])
        except (TypeError, ValueError):
            return "Invalid payment amount.", 400

        if amount <= 0:
            return "Payment amount must be greater than zero.", 400

        from urllib.parse import urlencode

        upi_params = {
            "pa": upi_id,
            "pn": payment.get("requester_name") or "CharityBridge User",
            "am": f"{amount:.2f}",
            "cu": "INR",
            "tn": f"CharityBridge Help Request #{payment['request_id']}"
        }

        upi_payment_uri = "upi://pay?" + urlencode(upi_params)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4
        )

        qr.add_data(upi_payment_uri)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        image_buffer = BytesIO()
        qr_image.save(image_buffer, format="PNG")
        image_buffer.seek(0)

        return send_file(
            image_buffer,
            mimetype="image/png",
            max_age=0
        )

    except Exception as e:
        print("DYNAMIC PAYMENT QR ERROR:", e)
        return "Unable to generate the payment QR.", 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass



# ============================================================
# PAY NOW - OPEN REQUESTER'S UPI PAYMENT
# ============================================================

@app.route("/response/pay-now/<int:request_id>")
def pay_now(request_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    helper_id = session["user_id"]

    try:
        db_connection = ReconnectableDB()
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)

        # ----------------------------------------------------
        # GET MONEY REQUEST + REQUESTER UPI DETAILS
        # ----------------------------------------------------
        cursor.execute("""
            SELECT
                hr.id,
                hr.user_id,
                hr.request_type,
                hr.amount,
                hr.description,
                hr.location,
                hr.status,

                u.name AS requester_name,
                upi.upi_id AS requester_upi_id

            FROM help_requests hr

            JOIN users u
                ON u.id = hr.user_id

            LEFT JOIN user_profiles upi
                ON upi.user_id = hr.user_id

            WHERE hr.id = %s
            LIMIT 1
        """, (request_id,))

        help_request = cursor.fetchone()

        if not help_request:
            cursor.close()
            flash("Help request not found.", "error")
            return redirect(url_for("response_page"))

        # ----------------------------------------------------
        # ONLY MONEY REQUESTS CAN USE PAY NOW
        # ----------------------------------------------------
        if str(help_request.get("request_type", "")).lower() != "money":
            cursor.close()
            flash("Online payment is available only for Money requests.", "error")
            return redirect(url_for("response_page"))

        # ----------------------------------------------------
        # CHECK AMOUNT
        # ----------------------------------------------------
        amount = help_request.get("amount")

        if amount is None:
            cursor.close()
            flash("This request does not have a payment amount.", "error")
            return redirect(url_for("response_page"))

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            cursor.close()
            flash("Invalid payment amount.", "error")
            return redirect(url_for("response_page"))

        if amount <= 0:
            cursor.close()
            flash("Payment amount must be greater than ₹0.", "error")
            return redirect(url_for("response_page"))

        # ----------------------------------------------------
        # CHECK REQUESTER UPI ID
        # ----------------------------------------------------
        requester_upi = (
            help_request.get("requester_upi_id") or ""
        ).strip()

        if not requester_upi:
            cursor.close()

            flash(
                "The requester has not added a UPI ID yet.",
                "error"
            )

            return redirect(url_for("response_page"))

        # ----------------------------------------------------
        # REQUESTER NAME
        # ----------------------------------------------------
        requester_name = (
            help_request.get("requester_name")
            or "CharityBridge User"
        ).strip()

        # ----------------------------------------------------
        # CREATE UPI PAYMENT LINK
        # ----------------------------------------------------
        from urllib.parse import urlencode

        upi_params = {
            "pa": requester_upi,
            "pn": requester_name,
            "am": f"{amount:.2f}",
            "cu": "INR",
            "tn": f"CharityBridge Help Request #{request_id}"
        }

        upi_link = "upi://pay?" + urlencode(upi_params)

        cursor.close()

        # ----------------------------------------------------
        # SHOW PAYMENT PAGE
        # ----------------------------------------------------
        return render_template(
            "payment.html",
            request_id=request_id,
            requester_name=requester_name,
            requester_upi=requester_upi,
            amount=f"{amount:.2f}",
            upi_link=upi_link
        )

    except Exception as e:

        print("PAY NOW ERROR:", e)

        try:
            conn.rollback()
        except Exception:
            pass

        flash(
            "Unable to start the payment.",
            "error"
        )

        return redirect(url_for("response_page"))




@app.route("/profile/upload-image", methods=["POST"])
def upload_profile_image():

    print("UPLOAD ROUTE REACHED", flush=True)
    print("SESSION USER:", session.get("user_id"), flush=True)
    print("UPLOADED FILES:", list(request.files.keys()), flush=True)

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    file = request.files.get("profile_image")

    if not file or not file.filename:
        flash("Please select a profile photo.", "error")
        return redirect(url_for("profile_page"))

    conn = None
    cursor = None
    saved_filepath = None

    try:
        original_name = secure_filename(file.filename)
        extension = original_name.rsplit(".", 1)[-1].lower()

        if "." not in original_name or extension not in {
            "png", "jpg", "jpeg", "webp"
        }:
            flash("Please upload PNG, JPG, JPEG or WEBP.", "error")
            return redirect(url_for("profile_page"))

        upload_folder = os.path.join(
            app.root_path, "static", "uploads", "profile"
        )
        os.makedirs(upload_folder, exist_ok=True)

        filename = f"user_{user_id}.{extension}"
        filepath = os.path.join(upload_folder, filename)

        file.save(filepath)
        saved_filepath = filepath

        image_url = url_for(
            "static",
            filename=f"uploads/profile/{filename}"
        )

        conn = db.get_connection() if db is not None else None
        if conn is None:
            raise Exception("Database connection failed")

        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id FROM user_profiles WHERE user_id = %s LIMIT 1",
            (user_id,)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE user_profiles
                SET profile_image = %s
                WHERE user_id = %s
                """,
                (image_url, user_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO user_profiles (user_id, profile_image)
                VALUES (%s, %s)
                """,
                (user_id, image_url)
            )

        conn.commit()
        saved_filepath = None

        cursor.execute(
            "SELECT profile_image FROM user_profiles WHERE user_id = %s",
            (user_id,)
        )
        print("VERIFIED SAVED IMAGE:", cursor.fetchone(), flush=True)

        flash("Profile picture updated successfully.", "success")

    except Exception as e:
        print("PROFILE IMAGE ERROR:", repr(e), flush=True)

        if conn:
            try:
                conn.rollback()
            except Exception:
                pass

        if saved_filepath and os.path.isfile(saved_filepath):
            try:
                os.remove(saved_filepath)
            except OSError:
                pass

        flash("Unable to save profile picture. Check the terminal error.", "error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("profile_page"))


@app.route("/profile/save", methods=["POST"])
def save_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # ---------------------------------------------------------
    # GET FORM DATA
    # ---------------------------------------------------------

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    location = request.form.get("location", "").strip()
    gender = request.form.get("gender", "").strip()
    qualification = request.form.get("qualification", "").strip()
    profession = request.form.get("profession", "").strip()
    bio = request.form.get("bio", "").strip()

    # Name and email are required
    if not name or not email:
        return redirect(url_for("profile_page"))

    conn = None
    cursor = None

    try:
        # -----------------------------------------------------
        # DATABASE CONNECTION
        # -----------------------------------------------------

        db_connection = ReconnectableDB()
        conn = db_connection.get_connection()

        cursor = conn.cursor(dictionary=True)

        # -----------------------------------------------------
        # UPDATE USERS TABLE
        # -----------------------------------------------------

        cursor.execute(
            """
            UPDATE users
            SET
                name = %s,
                email = %s,
                phone = %s
            WHERE id = %s
            """,
            (
                name,
                email,
                phone if phone else None,
                user_id
            )
        )

        # -----------------------------------------------------
        # CHECK WHETHER USER PROFILE ALREADY EXISTS
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM user_profiles
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        existing = cursor.fetchone()

        # -----------------------------------------------------
        # UPDATE EXISTING PROFILE
        #
        # IMPORTANT:
        # profile_image, upi_id and upi_qr_image are NOT touched.
        # -----------------------------------------------------

        if existing:

            cursor.execute(
                """
                UPDATE user_profiles
                SET
                    location = %s,
                    gender = %s,
                    qualification = %s,
                    profession = %s,
                    bio = %s
                WHERE user_id = %s
                """,
                (
                    location if location else None,
                    gender if gender else None,
                    qualification if qualification else None,
                    profession if profession else None,
                    bio if bio else None,
                    user_id
                )
            )

        # -----------------------------------------------------
        # CREATE NEW PROFILE
        # -----------------------------------------------------

        else:

            cursor.execute(
                """
                INSERT INTO user_profiles
                (
                    user_id,
                    location,
                    gender,
                    qualification,
                    profession,
                    bio
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user_id,
                    location if location else None,
                    gender if gender else None,
                    qualification if qualification else None,
                    profession if profession else None,
                    bio if bio else None
                )
            )

        # -----------------------------------------------------
        # SAVE EVERYTHING
        # -----------------------------------------------------

        conn.commit()

        # -----------------------------------------------------
        # KEEP SESSION DATA UPDATED
        # -----------------------------------------------------

        session["user_name"] = name
        session["user_email"] = email

        print(
            f"PROFILE UPDATED SUCCESSFULLY: user_id={user_id}"
        )

    except Exception as e:

        print("SAVE PROFILE ERROR:", e)

        if conn:
            try:
                conn.rollback()
            except Exception:
                pass

    finally:

        if cursor:
            try:
                cursor.close()
            except Exception:
                pass

        if conn:
            try:
                conn.close()
            except Exception:
                pass

    return redirect(url_for("profile_page"))



# ============================================================
# RESPONSE PAGE
# ============================================================

@app.route("/response", methods=["GET", "POST"])
def response_page():

    # ------------------------------------------------------------
    # LOGIN CHECK
    # ------------------------------------------------------------

   
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_user_id = session["user_id"]

    connection = None
    cursor = None

    try:
        connection = db.get_connection()

        if connection is None:
            flash("Database connection failed.", "error")
            return redirect(url_for("dashboard"))

        cursor = connection.cursor(dictionary=True)

        # ========================================================
        # SEND HELP OFFER
        # ========================================================

        if request.method == "POST":

            request_id = request.form.get(
                "request_id",
                ""
            ).strip()

            message = request.form.get(
                "message",
                ""
            ).strip()

            # ----------------------------------------------------
            # VALIDATE REQUEST ID
            # ----------------------------------------------------

            if not request_id.isdigit():

                flash(
                    "Invalid help request.",
                    "error"
                )

                return redirect(
                    url_for("response_page")
                )

            request_id = int(request_id)

            # ----------------------------------------------------
            # CHECK THAT REQUEST EXISTS
            # ----------------------------------------------------

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    request_type,
                    amount,
                    description,
                    location,
                    status
                FROM help_requests
                WHERE id = %s
                LIMIT 1
                """,
                (request_id,)
            )

            help_request = cursor.fetchone()

            if not help_request:

                flash(
                    "Help request not found.",
                    "error"
                )

                return redirect(
                    url_for("response_page")
                )

            # ----------------------------------------------------
            # ONLY PENDING REQUESTS CAN RECEIVE HELP
            # ----------------------------------------------------

            if (
                str(
                    help_request.get("status") or ""
                ).lower()
                != "pending"
            ):

                flash(
                    "This help request is no longer available.",
                    "error"
                )

                return redirect(
                    url_for("response_page")
                )

            # ----------------------------------------------------
            # PREVENT DUPLICATE HELP OFFERS
            # ----------------------------------------------------

            cursor.execute(
                """
                SELECT id
                FROM cb_request_responses
                WHERE request_id = %s
                AND helper_id = %s
                LIMIT 1
                """,
                (
                    request_id,
                    current_user_id
                )
            )

            already_responded = cursor.fetchone()

            if already_responded:

                flash(
                    "You have already offered help for this request.",
                    "info"
                )

                return redirect(
                    url_for("response_page")
                )

            # ----------------------------------------------------
            # SAVE HELP OFFER
            # ----------------------------------------------------

            cursor.execute(
                """
                INSERT INTO cb_request_responses
                (
                    request_id,
                    helper_id,
                    status,
                    message
                )
                VALUES
                (
                    %s,
                    %s,
                    'Pending',
                    %s
                )
                """,
                (
                    request_id,
                    current_user_id,
                    message
                )
            )

            connection.commit()

            flash(
                "Your help offer has been sent successfully.",
                "success"
            )

            return redirect(
                url_for("response_page")
            )

        # ========================================================
        # GET ALL PENDING HELP REQUESTS
        # ========================================================

        cursor.execute(
            """
            SELECT
                hr.id,
                hr.user_id,
                hr.request_type,
                hr.amount,
                hr.description,
                hr.location,
                hr.status,
                hr.created_at,

                u.name AS requester_name,
                u.email AS requester_email,

                up.upi_id AS requester_upi_id,
                up.upi_qr_image AS requester_upi_qr_image

            FROM help_requests hr

            LEFT JOIN users u
                ON hr.user_id = u.id

            LEFT JOIN user_profiles up
                ON hr.user_id = up.user_id

            
WHERE LOWER(
    COALESCE(
        hr.status,
        'Pending'
    )
) = 'pending'

AND hr.user_id != %s

AND NOT EXISTS (
    SELECT 1
    FROM cb_request_responses cr
    WHERE cr.request_id = hr.id
      AND cr.helper_id = %s
)
                      ORDER BY
                hr.created_at DESC,
                hr.id DESC
            """,
            (current_user_id, current_user_id)
        )

        requests_data = cursor.fetchall() or []

        # CHECK WHICH REQUESTS CURRENT USER ALREADY RESPONDED TO
        
        cursor.execute(
            """
            SELECT
                

    cr.id,
    cr.request_id,
    cr.helper_id,
    cr.status,
    cr.message,
    cr.created_at,
    
cr.payment_status,
cr.payment_confirmed_at,
cr.payment_message_sent,

EXISTS (
    SELECT 1
    FROM cb_payment_records p
    WHERE p.request_id = cr.request_id
      AND p.helper_id = cr.helper_id
) AS has_payment_report,

(
    SELECT p.id
    FROM cb_payment_records p
    WHERE p.request_id = cr.request_id
      AND p.helper_id = cr.helper_id
    ORDER BY p.created_at DESC, p.id DESC
    LIMIT 1
) AS payment_id,

(
    SELECT p.status
    FROM cb_payment_records p
    WHERE p.request_id = cr.request_id
      AND p.helper_id = cr.helper_id
    ORDER BY p.created_at DESC, p.id DESC
    LIMIT 1
) AS payment_record_status,

(
    SELECT r.id
    FROM cb_payment_receipts r
    INNER JOIN cb_payment_records p
        ON p.id = r.payment_id
    WHERE p.request_id = cr.request_id
      AND p.helper_id = cr.helper_id
    ORDER BY r.uploaded_at DESC, r.id DESC
    LIMIT 1
) AS receipt_id,

(
    SELECT r.recipient_decision
    FROM cb_payment_receipts r
    INNER JOIN cb_payment_records p
        ON p.id = r.payment_id
    WHERE p.request_id = cr.request_id
      AND p.helper_id = cr.helper_id
    ORDER BY r.uploaded_at DESC, r.id DESC
    LIMIT 1
) AS receipt_decision,




                hr.request_type,
hr.amount,
hr.description,
hr.location,
hr.upi_qr_image,

                u.name AS requester_name,

                up.upi_id AS requester_upi_id,
               up.upi_qr_image AS requester_upi_qr_image
            FROM cb_request_responses cr

            INNER JOIN help_requests hr
                ON cr.request_id = hr.id

            LEFT JOIN users u
                ON hr.user_id = u.id

            LEFT JOIN user_profiles up
                ON hr.user_id = up.user_id

            WHERE cr.helper_id = %s

            ORDER BY cr.created_at DESC
            """,
            (current_user_id,)
        )

       
        responses = cursor.fetchall() or []

        # TEMPORARY DEBUG CHECK
        for response in responses:
            print(
                "PAYMENT CHECK:",
                response.get("request_id"),
                response.get("helper_id"),
                response.get("has_payment_report")
            )

        responded_request_ids = {
            int(row["request_id"])
            for row in responses
            if row.get("request_id") is not None
        }
            # Hide responses that already have a payment report
              # Count verified helped requests before hiding payment reports
        helped_responses = sum(
            1
            for row in responses
            if str(
                row.get("payment_record_status") or ""
            ).strip().lower() == "verified"
        )

        # Hide responses that already have a payment report
        # Keep responded_request_ids unchanged to prevent duplicate offers
        responses = [
            response
            for response in responses
            if not response.get("has_payment_report")
        ]
        # Format requested amounts for My Help Offers.
        for response in responses:
            response["amount_display"] = ""

            if response.get("amount") is not None:
                try:
                    amount_value = float(response["amount"])

                    if amount_value > 0:
                        response["amount_display"] = (
                            f"₹{amount_value:,.2f}"
                        )

                except (ValueError, TypeError):
                    response["amount_display"] = ""

            response["requester_name"] = (
                response.get("requester_name")
                or "CharityBridge User"
            )

            response["requester_upi_id"] = (
                response.get("requester_upi_id") or ""
            )

            response["requester_upi_qr_image"] = (
                response.get("requester_upi_qr_image") or ""
            )


        # ========================================================
        # FORMAT REQUEST DATA FOR response.html
        # ========================================================

        for item in requests_data:

            item["amount_display"] = ""

            if item.get("amount") is not None:

                try:

                    amount_value = float(
                        item["amount"]
                    )

                    if amount_value > 0:

                        item["amount_display"] = (
                            f"₹{amount_value:,.2f}"
                        )

                except (
                    ValueError,
                    TypeError
                ):

                    item["amount_display"] = ""

            item["already_responded"] = (
                int(item["id"])
                in responded_request_ids
            )

            item["requester_name"] = (
                item.get("requester_name")
                or "CharityBridge User"
            )

            item["requester_email"] = (
                item.get("requester_email")
                or ""
            )

            item["requester_upi_id"] = (
                item.get("requester_upi_id")
                or ""
            )

            item["requester_upi_qr_image"] = (
                item.get("requester_upi_qr_image")
                or ""
            )

            item["request_type"] = (
                item.get("request_type")
                or "Other"
            )

            item["description"] = (
                item.get("description")
                or "Help requested."
            )

            item["location"] = (
                item.get("location")
                or "Location not provided"
            )

        
        # ========================================================
        # COUNTS
        # ========================================================
                # Count all pending help requests from other users
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM help_requests hr
            WHERE LOWER(COALESCE(hr.status, 'Pending')) = 'pending'
              AND hr.user_id != %s
        """, (current_user_id,))

        count_result = cursor.fetchone()
        total_requests = int(count_result["total"] or 0)

        total_responses = len(responses)
        pending_responses = sum(
            1
            for row in responses
            if str(row.get("status") or "").lower() == "pending"
        )

        accepted_responses = sum(
            1
            for row in responses
            if str(row.get("status") or "").lower() == "accepted"
        )
        


        # ========================================================
        # NOTIFICATIONS
        # ========================================================

    
        notifications = []

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    title,
                    message,
                    is_read,
                    created_at
                FROM cb_notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (current_user_id,)
            )

            notifications = (
                cursor.fetchall() or []
            )

        except Exception as notification_error:

            print(
                "Response notification query skipped:",
                notification_error
            )


        # ========================================================
        # USER INFORMATION
        # ========================================================

        user_name = session.get(
            "user_name",
            ""
        )

        user_email = session.get(
            "user_email",
            ""
        )

        avatar_url = ""

        try:

            cursor.execute(
                """
                SELECT
                    name,
                    email
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (current_user_id,)
            )

            user_data = cursor.fetchone()

            if user_data:

                user_name = (
                    user_data.get("name")
                    or user_name
                )

                user_email = (
                    user_data.get("email")
                    or user_email
                )

        except Exception as user_error:

            print(
                "Response user query skipped:",
                user_error
            )

        # ========================================================
        # PROFILE IMAGE
        # ========================================================

        try:

            cursor.execute(
                """
                SELECT
                    profile_image
                FROM user_profiles
                WHERE user_id = %s
                LIMIT 1
                """,
                (current_user_id,)
            )

            profile_data = cursor.fetchone()

            if profile_data:

                avatar_url = (
                    profile_data.get(
                        "profile_image"
                    )
                    or ""
                )

        except Exception as profile_error:

            print(
                "Response profile image query skipped:",
                profile_error
            )

        # ========================================================
        # RENDER RESPONSE PAGE
        # ========================================================

        return render_template(
            "response.html",

            requests=requests_data,
            help_requests=requests_data,

            responses=responses,
            notifications=notifications,

            total_requests=total_requests,
            total_responses=total_responses,
            pending_responses=pending_responses,
            accepted_responses=accepted_responses,

            current_user_id=current_user_id,

            user_name=user_name,
            user_email=user_email,
            helped_responses=helped_responses,
            avatar_url=avatar_url
        )

    # ============================================================
    # DATABASE ERROR
    # ============================================================

    
    except Error as e:

        app.logger.exception(
            "Response page database error"
        )

        if connection:
            try:
                connection.rollback()
            except Exception:
                pass

        flash(
            f"Database error loading responses: {e}",
            "error"
        )

        return redirect(url_for("dashboard"))

    except Exception as e:

        app.logger.exception(
            "Unexpected response page error"
        )

        if connection:
            try:
                connection.rollback()
            except Exception:
                pass

        flash(
            f"Error loading responses: {e}",
            "error"
        )

        return redirect(url_for("dashboard"))

    # ============================================================
    # CLOSE CURSOR
    # ============================================================

    finally:

        cursor.close()




# ============================================================
# REQUESTS OVERVIEW + CREATE REQUEST PAGE
# ============================================================

@app.route("/request", methods=["GET", "POST"])
def request_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("dashboard"))

    cursor = connection.cursor(dictionary=True)

    upload_folder = os.path.join(
        app.root_path,
        "static",
        "images",
        "upi_qr"
    )

    allowed_extensions = {"png", "jpg", "jpeg", "webp"}

    try:
        os.makedirs(upload_folder, exist_ok=True)

        # ====================================================
        # CREATE REQUEST
        # ====================================================

        if request.method == "POST":

            request_type = request.form.get(
                "request_type", ""
            ).strip()

            description = request.form.get(
                "description", ""
            ).strip()

            location = request.form.get(
                "location", ""
            ).strip()

            quantity_text = request.form.get(
                "quantity", "1"
            ).strip()

            amount_text = request.form.get(
                "amount", ""
            ).strip()

            allowed_types = {
                "Food", "Blood", "Clothes",
                "Furniture", "Money", "Other"
            }

            if request_type not in allowed_types:
                flash("Please select a valid help category.", "error")
                return redirect(url_for("request_page"))

            if not description or not location:
                flash(
                    "Please enter your location and describe the help you need.",
                    "error"
                )
                return redirect(url_for("request_page"))

            # -----------------------------------------------
            # AMOUNT OR QUANTITY
            # -----------------------------------------------

            amount = None
            quantity = None

            try:
                if request_type == "Money":
                    amount = float(amount_text)

                    if amount <= 0 or not amount < float("inf"):
                        raise ValueError
                else:
                    quantity = int(quantity_text)

                    if quantity <= 0:
                        raise ValueError

            except (ValueError, TypeError, OverflowError):
                flash(
                    "Enter a valid amount or quantity.",
                    "error"
                )
                return redirect(url_for("request_page"))

            # -----------------------------------------------
            # OPTIONAL UPI QR IMAGE
            # -----------------------------------------------

            qr_image = None
            uploaded_file = request.files.get("upi_qr_image")

            if request_type == "Money" and uploaded_file:
                if uploaded_file.filename:
                    safe_name = secure_filename(
                        uploaded_file.filename
                    )

                    if (
                        "." not in safe_name
                        or safe_name.rsplit(".", 1)[1].lower()
                        not in allowed_extensions
                    ):
                        flash(
                            "Upload a QR image in PNG, JPG, JPEG, or WEBP format.",
                            "error"
                        )
                        return redirect(url_for("request_page"))

                    extension = safe_name.rsplit(".", 1)[1].lower()
                    qr_image = f"{uuid.uuid4().hex}.{extension}"

                    uploaded_file.save(
                        os.path.join(upload_folder, qr_image)
                    )

            # -----------------------------------------------
            # SAVE TO DATABASE
            # -----------------------------------------------

            cursor.execute("""
                INSERT INTO help_requests
                (
                    user_id,
                    request_type,
                    amount,
                    description,
                    location,
                    status,
                    upi_qr_image
                )
                VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
            """, (
                user_id,
                request_type,
                amount,
                description,
                location,
                qr_image
            ))

            connection.commit()

            flash(
                "Your help request has been submitted successfully.",
                "success"
            )

            return redirect(url_for("request_page"))

        # ====================================================
        # GET USER REQUESTS
        # ====================================================

        cursor.execute("""
            SELECT
                hr.id,
                hr.user_id,
                hr.request_type,
                hr.amount,
                hr.description,
                hr.location,
                hr.status,
                hr.created_at,
                hr.upi_qr_image,
                u.name AS requester_name,
                u.phone AS requester_phone
            FROM help_requests hr
            JOIN users u ON hr.user_id = u.id
            WHERE hr.user_id = %s
            ORDER BY hr.created_at DESC, hr.id DESC
        """, (user_id,))

        requests_data = cursor.fetchall() or []

        # ====================================================
        # REQUEST COUNTS
        # ====================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(status = 'Pending'), 0) AS pending,
                COALESCE(SUM(status = 'Accepted'), 0) AS accepted
            FROM help_requests
            WHERE user_id = %s
        """, (user_id,))

        counts = cursor.fetchone() or {}

        total_requests = int(counts.get("total") or 0)
        pending_requests = int(counts.get("pending") or 0)
        accepted_requests = int(counts.get("accepted") or 0)

        # ====================================================
        # USER INFORMATION
        # ====================================================

        user_name = session.get("user_name", "")
        user_email = session.get("user_email", "")
        user_verified = False
        avatar_url = ""

        cursor.execute("""
            SELECT name, email, email_verified
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        user_data = cursor.fetchone()

        if user_data:
            user_name = user_data.get("name") or user_name
            user_email = user_data.get("email") or user_email
            user_verified = bool(user_data.get("email_verified"))

        cursor.execute("""
            SELECT profile_image
            FROM user_profiles
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        profile_data = cursor.fetchone()

        if profile_data:
            avatar_url = profile_data.get("profile_image") or ""

        # ====================================================
        # RENDER PAGE
        # ====================================================

        return render_template(
            "request.html",
            help_requests=requests_data,
            requests=requests_data,
            total_requests=total_requests,
            pending_requests=pending_requests,
            accepted_requests=accepted_requests,
            user_name=user_name,
            user_email=user_email,
            user_verified=user_verified,
            avatar_url=avatar_url
        )

    
    except Error as e:

        print("Response page database error:", repr(e))

        if connection is not None:
            try:
                connection.rollback()
            except Exception as rollback_error:
                print("Response rollback error:", repr(rollback_error))

        flash("Unable to load help requests.", "error")
        return redirect(url_for("dashboard"))

    except Exception as e:

        import traceback

        print("Response page error:", repr(e))
        traceback.print_exc()

        if connection is not None:
            try:
                connection.rollback()
            except Exception as rollback_error:
                print("Response rollback error:", repr(rollback_error))

        flash("Something went wrong while loading responses.", "error")
        return redirect(url_for("dashboard"))

    finally:

        if cursor is not None:
            try:
                cursor.close()
            except Exception as close_error:
                print("Response cursor close error:", repr(close_error))


@app.route("/my-impact")
@app.route("/myimpact")
def my_impact_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("dashboard"))

    cursor = connection.cursor(dictionary=True)

    try:
        # ---------------------------------------------------------
        # 1. CHECK LOGGED-IN USER
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.email_verified,
                u.created_at,
                up.profile_image
            FROM users u
            LEFT JOIN user_profiles up
                ON up.user_id = u.id
            WHERE u.id = %s
        """, (user_id,))

        founder = cursor.fetchone()

        if not founder:
            flash("User account not found.", "error")
            return redirect(url_for("login"))

        # ---------------------------------------------------------
        # 2. FOUNDER-ONLY PROTECTION
        # ---------------------------------------------------------
        if str(founder.get("role") or "").strip().lower() != "founder":
            flash("Founder analytics are available only to founders.", "error")
            return redirect(url_for("dashboard"))

        # ---------------------------------------------------------
        # 3. BASIC COMMUNITY TOTALS
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
        """)
        total_users = (cursor.fetchone() or {}).get("total", 0)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE email_verified = 1
        """)
        verified_users = (cursor.fetchone() or {}).get("total", 0)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM volunteers
        """)
        total_volunteers = (cursor.fetchone() or {}).get("total", 0)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM help_requests
        """)
        total_help_requests = (cursor.fetchone() or {}).get("total", 0)

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM donations
        """)
        total_item_donations = (cursor.fetchone() or {}).get("total", 0)

        cursor.execute("""
            SELECT
                COALESCE(SUM(amount), 0) AS total
            FROM money_donations
            WHERE LOWER(COALESCE(status, '')) IN ('success', 'successful', 'completed')
        """)
        total_money_donated = (cursor.fetchone() or {}).get(
            "total", 0
        )

        # ---------------------------------------------------------
        # 4. USER GROWTH
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                DATE_FORMAT(created_at, '%Y-%m') AS month,
                COUNT(*) AS total
            FROM users
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month ASC
        """)
        user_growth_rows = cursor.fetchall()

        user_growth_labels = [
            row["month"] for row in user_growth_rows
        ]

        user_growth_values = [
            int(row["total"] or 0)
            for row in user_growth_rows
        ]

        # ---------------------------------------------------------
        # 5. MONEY DONATION GROWTH
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                DATE_FORMAT(created_at, '%Y-%m') AS month,
                COALESCE(SUM(amount), 0) AS total
            FROM money_donations
            WHERE LOWER(COALESCE(status, '')) IN
                  ('success', 'successful', 'completed')
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month ASC
        """)
        money_growth_rows = cursor.fetchall()

        money_growth_labels = [
            row["month"] for row in money_growth_rows
        ]

        money_growth_values = [
            float(row["total"] or 0)
            for row in money_growth_rows
        ]

        # ---------------------------------------------------------
        # 6. ITEM DONATION CATEGORY DISTRIBUTION
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                item_type,
                COUNT(*) AS total
            FROM donations
            GROUP BY item_type
            ORDER BY total DESC
        """)
        donation_category_rows = cursor.fetchall()

        donation_category_labels = [
            row["item_type"] or "Other"
            for row in donation_category_rows
        ]

        donation_category_values = [
            int(row["total"] or 0)
            for row in donation_category_rows
        ]

        # ---------------------------------------------------------
        # 7. HELP REQUEST STATUS
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS total
            FROM help_requests
            GROUP BY status
            ORDER BY total DESC
        """)
        request_status_rows = cursor.fetchall()

        request_status_labels = [
            row["status"] or "Unknown"
            for row in request_status_rows
        ]

        request_status_values = [
            int(row["total"] or 0)
            for row in request_status_rows
        ]

        # ---------------------------------------------------------
        # 8. MONTHLY COMMUNITY ACTIVITY
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                month,
                SUM(donations_count) AS donations_count,
                SUM(requests_count) AS requests_count,
                SUM(volunteers_count) AS volunteers_count
            FROM (
                SELECT
                    DATE_FORMAT(created_at, '%Y-%m') AS month,
                    COUNT(*) AS donations_count,
                    0 AS requests_count,
                    0 AS volunteers_count
                FROM donations
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')

                UNION ALL

                SELECT
                    DATE_FORMAT(created_at, '%Y-%m') AS month,
                    0 AS donations_count,
                    COUNT(*) AS requests_count,
                    0 AS volunteers_count
                FROM help_requests
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')

                UNION ALL

                SELECT
                    DATE_FORMAT(created_at, '%Y-%m') AS month,
                    0 AS donations_count,
                    0 AS requests_count,
                    COUNT(*) AS volunteers_count
                FROM volunteers
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ) activity
            GROUP BY month
            ORDER BY month ASC
        """)
        activity_rows = cursor.fetchall()

        activity_labels = [
            row["month"] for row in activity_rows
        ]

        activity_donations = [
            int(row["donations_count"] or 0)
            for row in activity_rows
        ]

        activity_requests = [
            int(row["requests_count"] or 0)
            for row in activity_rows
        ]

        activity_volunteers = [
            int(row["volunteers_count"] or 0)
            for row in activity_rows
        ]

        # ---------------------------------------------------------
        # 9. CURRENT FOUNDER INFORMATION
        # ---------------------------------------------------------
        founder_name = founder.get("name") or "Founder"
        founder_email = founder.get("email") or ""
        founder_avatar = founder.get("profile_image") or ""
        founder_verified = bool(founder.get("email_verified"))
        founder_joined = founder.get("created_at")

        return render_template(
            "myimpact.html",

            # Founder
            founder_name=founder_name,
            founder_email=founder_email,
            founder_avatar=founder_avatar,
            founder_verified=founder_verified,
            founder_joined=founder_joined,

            # Main totals
            total_users=total_users,
            verified_users=verified_users,
            total_volunteers=total_volunteers,
            total_help_requests=total_help_requests,
            total_item_donations=total_item_donations,
            total_money_donated=float(total_money_donated or 0),

            # User growth
            user_growth_labels=user_growth_labels,
            user_growth_values=user_growth_values,

            # Money growth
            money_growth_labels=money_growth_labels,
            money_growth_values=money_growth_values,

            # Donation categories
            donation_category_labels=donation_category_labels,
            donation_category_values=donation_category_values,

            # Request status
            request_status_labels=request_status_labels,
            request_status_values=request_status_values,

            # Community activity
            activity_labels=activity_labels,
            activity_donations=activity_donations,
            activity_requests=activity_requests,
            activity_volunteers=activity_volunteers
        )

    except Exception as e:
        print("Founder My Impact error:", e)
        flash("Unable to load founder analytics.", "error")
        return redirect(url_for("dashboard"))

    finally:
        cursor.close()

# ============================================================
# FOUNDER ANALYTICS
# ============================================================

@app.route("/founder/analytics")
def founder_analytics():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    user_role = str(
        session.get(
            "role",
            "user"
        )
    ).lower()

    if user_role not in [
        "founder",
        "admin"
    ]:

        return redirect(
            url_for("dashboard")
        )


    connection = db


    total_users = 0
    total_volunteers = 0
    total_help_requests = 0
    successful_donations = 0
    total_donation_amount = 0


    if connection is not None:

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            # =================================================
            # TOTAL USERS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM users
            """)

            result = cursor.fetchone()

            if result:

                total_users = (
                    result["total"]
                    or 0
                )


            # =================================================
            # TOTAL VOLUNTEERS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM volunteers
            """)

            result = cursor.fetchone()

            if result:

                total_volunteers = (
                    result["total"]
                    or 0
                )


            # =================================================
            # TOTAL HELP REQUESTS
            # =================================================

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM help_requests
            """)

            result = cursor.fetchone()

            if result:

                total_help_requests = (
                    result["total"]
                    or 0
                )


            # =================================================
            # SUCCESSFUL MONEY DONATIONS
            # =================================================

            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(amount), 0) AS amount
                FROM money_donations
                WHERE status = 'Success'
            """)

            result = cursor.fetchone()

            if result:

                successful_donations = (
                    result["total"]
                    or 0
                )

                total_donation_amount = (
                    result["amount"]
                    or 0
                )

        except Error as e:

            print(
                "Founder analytics database error:",
                e
            )

        finally:

            cursor.close()


    return render_template(
        "founder_analytics.html",

        user_name=session.get(
            "user_name",
            "Founder"
        ),

        total_users=total_users,

        total_volunteers=total_volunteers,

        total_help_requests=total_help_requests,

        successful_donations=successful_donations,

        total_donation_amount=total_donation_amount
    )


# ============================================================
# MY DONATIONS
# ============================================================

@app.route("/my_donations")
def my_donations():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    connection = db

    if connection is None:

        flash(
            "Database connection failed.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT *
            FROM donations
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,)
        )

        donations = cursor.fetchall()

        return render_template(
            "my_donations.html",
            donations=donations
        )

    except Error as e:

        print(
            "My donations error:",
            e
        )

        flash(
            "Unable to load donations.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        cursor.close()


# ============================================================
# REQUEST HELP
# ============================================================

@app.route(
    "/request_help",
    methods=["GET", "POST"]
)
def request_help():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        user_id = session["user_id"]

        request_type = request.form.get(
            "request_type",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        if not request_type or not description:

            flash(
                "Please provide the required information.",
                "error"
            )

            return redirect(
                url_for("request_help")
            )

        connection = db

        if connection is None:

            flash(
                "Database connection failed.",
                "error"
            )

            return redirect(
                url_for("request_help")
            )

        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO help_requests
                (
                    user_id,
                    request_type,
                    description,
                    location,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    request_type,
                    description,
                    location,
                    "Pending"
                )
            )

            connection.commit()


            notify_cursor = connection.cursor()

            try:

                notify_cursor.execute("""
                    INSERT INTO cb_notifications
                    (
                        user_id,
                        title,
                        message
                    )
                    VALUES (%s, %s, %s)
                """, (
                    user_id,
                    "Help request submitted",
                    "Your help request has been submitted and is awaiting review."
                ))

                connection.commit()

            finally:

                notify_cursor.close()


            flash(
                "Your help request has been submitted.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        except Error as e:

            connection.rollback()

            print(
                "Help request error:",
                e
            )

            flash(
                "Unable to submit help request.",
                "error"
            )

            return redirect(
                url_for("request_help")
            )

        finally:

            cursor.close()


    return render_template(
        "request_help.html"
    )


@app.route("/volunteer", methods=["GET", "POST"])
def volunteer():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = db
    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("dashboard"))

    cursor = connection.cursor(dictionary=True)

    try:
        # ---------------------------------------------------------
        # SAVE / UPDATE VOLUNTEER INFORMATION
        # ---------------------------------------------------------
        if request.method == "POST":
            availability = request.form.get("availability", "").strip()
            skills = request.form.get("skills", "").strip()

            allowed_availability = {
                "Available",
                "Not Available",
                "Busy"
            }

            if availability not in allowed_availability:
                flash("Please select a valid availability status.", "error")
                return redirect(url_for("volunteer"))

            # Check whether this user is already registered as a volunteer
            cursor.execute("""
                SELECT id
                FROM volunteers
                WHERE user_id = %s
                LIMIT 1
            """, (user_id,))

            existing_volunteer = cursor.fetchone()

            if existing_volunteer:
                cursor.execute("""
                    UPDATE volunteers
                    SET availability = %s,
                        skills = %s
                    WHERE user_id = %s
                """, (
                    availability,
                    skills if skills else None,
                    user_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO volunteers
                        (user_id, availability, skills)
                    VALUES
                        (%s, %s, %s)
                """, (
                    user_id,
                    availability,
                    skills if skills else None
                ))

            connection.commit()

            flash("Your volunteer profile has been updated successfully.", "success")
            return redirect(url_for("volunteer"))

        # ---------------------------------------------------------
        # REAL LOGGED-IN USER
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.phone,
                u.email_verified,
                u.created_at,
                up.profile_image,
                up.location
            FROM users u
            LEFT JOIN user_profiles up
                ON up.user_id = u.id
            WHERE u.id = %s
            LIMIT 1
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            flash("User account could not be found.", "error")
            return redirect(url_for("logout"))

        # ---------------------------------------------------------
        # REAL VOLUNTEER INFORMATION
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                id,
                user_id,
                availability,
                skills,
                created_at
            FROM volunteers
            WHERE user_id = %s
            LIMIT 1
        """, (user_id,))

        volunteer_data = cursor.fetchone()

        if volunteer_data:
            volunteer_status = volunteer_data.get("availability") or "Not Registered"
            volunteer_skills = volunteer_data.get("skills") or ""
            volunteer_joined = volunteer_data.get("created_at")
            volunteer_registered = True
        else:
            volunteer_status = "Not Registered"
            volunteer_skills = ""
            volunteer_joined = None
            volunteer_registered = False
            
        # ---------------------------------------------------------
        # REGISTERED VOLUNTEER DIRECTORY
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                u.id AS user_id,
                u.name,
                u.email,
                u.phone,
                up.location,
                up.profile_image,
                v.availability,
                v.skills,
                v.created_at
            FROM volunteers v
            INNER JOIN users u
                ON u.id = v.user_id
            LEFT JOIN user_profiles up
                ON up.user_id = u.id
            ORDER BY
                CASE
                    WHEN v.availability = 'Available' THEN 1
                    WHEN v.availability = 'Busy' THEN 2
                    WHEN v.availability = 'Not Available' THEN 3
                    ELSE 4
                END,
                v.created_at DESC
        """)

        registered_volunteers = cursor.fetchall() or []


        
        # ---------------------------------------------------------
        # REAL NON-MONEY HELP REQUESTS
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                hr.id,
                hr.user_id,
                hr.request_type,
                hr.description,
                hr.location,
                hr.status,
                hr.created_at,

                u.name AS requester_name,
                u.phone AS requester_phone,
                u.email AS requester_email,

                up.location AS requester_profile_location

            FROM help_requests hr

            INNER JOIN users u
                ON hr.user_id = u.id

            LEFT JOIN user_profiles up
                ON up.user_id = hr.user_id

            WHERE LOWER(
                COALESCE(hr.status, '')
            ) IN ('pending', 'available')

            AND LOWER(
                COALESCE(hr.request_type, '')
            ) <> 'money'

            AND hr.user_id <> %s

            ORDER BY hr.created_at DESC, hr.id DESC
        """, (user_id,))

        help_requests = cursor.fetchall() or []


        # ---------------------------------------------------------
        # REAL COUNTS
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM help_requests
            WHERE status IN ('Pending', 'Available')
            AND user_id != %s
        """, (user_id,))

        result = cursor.fetchone()
        active_requests = result["total"] if result else 0

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM volunteers
        """)

        result = cursor.fetchone()
        total_volunteers = result["total"] if result else 0

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM help_requests
            WHERE user_id = %s
        """, (user_id,))

        result = cursor.fetchone()
        my_requests = result["total"] if result else 0

        # ---------------------------------------------------------
        # REAL COMPLETED REQUEST COUNT CONNECTED TO THIS USER
        # ---------------------------------------------------------
        # Your current volunteers table does not contain completed
        # activity information, so we do NOT invent a number here.
        completed_support = 0
        
        # ====================================================
        # FOOD DELIVERY OFFERS AND ASSIGNMENTS
        # ====================================================

        # Read the current user's actual database role.
        cursor.execute("""
            SELECT role
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        role_record = cursor.fetchone() or {}

        is_founder = (
            str(role_record.get("role") or "").strip().lower()
            == "founder"
        )

        # Show the founder their deliveries and volunteers
        # only the offers assigned to their own account.
        cursor.execute("""
            SELECT
                fd.id AS delivery_id,
                fd.request_id,
                fd.volunteer_user_id,
                fd.founder_user_id,
                fd.recipient_name,
                fd.recipient_phone,
                fd.recipient_address,
                fd.delivery_message,
                fd.status AS delivery_status,
                fd.created_at AS delivery_created_at,
                fd.assigned_at,
                fd.started_at,
                fd.delivered_at,

                requester.name AS requester_name,
                requester.email AS requester_email,

                volunteer_user.name AS volunteer_name,
                volunteer_user.email AS volunteer_email,
                volunteer_user.phone AS volunteer_phone,

                hr.request_type,
                hr.description AS food_description,
                hr.location AS request_location

            FROM food_deliveries fd

            INNER JOIN help_requests hr
                ON hr.id = fd.request_id

            INNER JOIN users requester
                ON requester.id = hr.user_id

            INNER JOIN users volunteer_user
                ON volunteer_user.id = fd.volunteer_user_id

            WHERE fd.volunteer_user_id = %s
               OR fd.founder_user_id = %s

            ORDER BY fd.created_at DESC, fd.id DESC
        """, (user_id, user_id))

        food_deliveries = cursor.fetchall() or []
                # ====================================================
        # FOOD REQUESTS FOR FOUNDER DELIVERY FORM
        # ====================================================
        cursor.execute("""
            SELECT
                hr.id,
                hr.request_type,
                hr.description,
                hr.location,
                hr.status,
                u.name AS requester_name
            FROM help_requests hr
            INNER JOIN users u ON u.id = hr.user_id
            WHERE LOWER(COALESCE(hr.status, '')) IN ('pending', 'available')
              AND (
                  LOWER(COALESCE(hr.request_type, '')) LIKE '%food%'
                  OR LOWER(COALESCE(hr.description, '')) LIKE '%food%'
              )
            ORDER BY hr.created_at DESC, hr.id DESC
        """)

        food_help_requests = cursor.fetchall() or []


        # ---------------------------------------------------------
        # SEND REAL DATA TO volunteer.html
        # ---------------------------------------------------------
        return render_template(
            "volunteer.html",

            user=user,

            user_name=user.get("name") or "User",
            user_email=user.get("email") or "",
            user_phone=user.get("phone") or "",
            user_location=user.get("location") or "",
            user_verified=bool(user.get("email_verified")),
            avatar_url=user.get("profile_image") or "",

            volunteer_data=volunteer_data,
            volunteer_registered=volunteer_registered,
            volunteer_status=volunteer_status,
            volunteer_skills=volunteer_skills,
            
            volunteer_joined=volunteer_joined,

            # Registered volunteer directory
            registered_volunteers=registered_volunteers,

            help_requests=help_requests,
            food_help_requests=food_help_requests,


            active_requests=active_requests,
            total_volunteers=total_volunteers,
            my_requests=my_requests,
            completed_support=completed_support,
             food_deliveries=food_deliveries,
            is_founder=is_founder
        )

    except Error as e:
        connection.rollback()
        print("Volunteer page database error:", e)
        flash("Unable to load the volunteer page.", "error")
        return redirect(url_for("dashboard"))

    except Exception as e:
        connection.rollback()
        print("Volunteer page unexpected error:", e)
        flash("Something went wrong while loading the volunteer page.", "error")
        return redirect(url_for("dashboard"))

    finally:
        cursor.close()

# ============================================================
# ACCEPT HELP REQUEST
# ============================================================

@app.route(
    "/accept_request/<int:id>",
    methods=["POST", "GET"]
)
def accept_request(id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = db

    if connection is None:

        flash(
            "Database connection failed.",
            "error"
        )

        return redirect(
            url_for("volunteer_dashboard")
        )

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            UPDATE help_requests
            SET status = 'Accepted'
            WHERE id = %s
            AND status = 'Pending'
            """,
            (id,)
        )

        connection.commit()


        if cursor.rowcount > 0:

            cursor.execute(
                """
                SELECT user_id
                FROM help_requests
                WHERE id = %s
                """,
                (id,)
            )

            request_owner = cursor.fetchone()

            if request_owner:

                cursor.execute("""
                    INSERT INTO cb_notifications
                    (
                        user_id,
                        title,
                        message
                    )
                    VALUES (%s, %s, %s)
                """, (
                    request_owner["user_id"],
                    "Help request updated",
                    "Your help request has been accepted for community support."
                ))

                connection.commit()


            flash(
                "Help request accepted successfully!",
                "success"
            )

        else:

            flash(
                "This request has already been accepted.",
                "error"
            )


        return redirect(
            url_for("volunteer_dashboard")
        )

    except Error as e:

        connection.rollback()

        print(
            "Accept request error:",
            e
        )

        flash(
            "Unable to accept request.",
            "error"
        )

        return redirect(
            url_for("volunteer_dashboard")
        )

    finally:

        cursor.close()
        
# ============================================================
# VOLUNTEER EXPRESSES INTEREST IN A HELP REQUEST
# Does not automatically accept or change the help request
# ============================================================

@app.route(
    "/volunteer/interest/<int:request_id>",
    methods=["POST"]
)
def submit_volunteer_interest(request_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("volunteer"))

    cursor = connection.cursor(dictionary=True)

    try:
        volunteer_id = session["user_id"]

        # Find the selected help request.
        cursor.execute("""
            SELECT id, user_id, request_type, location, status
            FROM help_requests
            WHERE id = %s
        """, (request_id,))

        help_request = cursor.fetchone()

        if not help_request:
            flash("Help request not found.", "error")
            return redirect(url_for("volunteer"))
        if help_request["status"] != "Pending":
            flash("This help request is no longer pending.", "error")
            return redirect(url_for("volunteer"))

        if help_request["user_id"] == volunteer_id:
            flash("You cannot volunteer for your own request.", "error")
            return redirect(url_for("volunteer"))

        # Find the volunteer's details.
        cursor.execute("""
            SELECT name, email
            FROM users
            WHERE id = %s
        """, (volunteer_id,))

        volunteer = cursor.fetchone()

        if not volunteer:
            flash("Volunteer account not found.", "error")
            return redirect(url_for("volunteer"))

        # Find the Founder dynamically.
        cursor.execute("""
            SELECT id, name, email
            FROM users
            WHERE LOWER(role) = 'founder'
            LIMIT 1
        """)

        founder = cursor.fetchone()

        if not founder:
            flash("Founder account was not found.", "error")
            return redirect(url_for("volunteer"))

        # Avoid duplicate interest records.
        cursor.execute("""
            SELECT id
            FROM cb_volunteer_interests
            WHERE request_id = %s AND volunteer_id = %s
        """, (request_id, volunteer_id))

        existing_interest = cursor.fetchone()

        if existing_interest:
            flash(
                "You have already expressed interest in this request.",
                "info"
            )
            return redirect(url_for("volunteer"))

        # Save the volunteer's interest.
        cursor.execute("""
            INSERT INTO cb_volunteer_interests
                (request_id, volunteer_id, status)
            VALUES (%s, %s, 'Pending')
        """, (request_id, volunteer_id))

        # Notify the Founder in CharityBridge.
        cursor.execute("""
            INSERT INTO cb_notifications (user_id, title, message)
            VALUES (%s, %s, %s)
        """, (
            founder["id"],
            "New volunteer interest",
            (
                f"{volunteer['name']} wants to help with "
                f"{help_request['request_type']} "
                f"(Request ID: {request_id}). "
                "Please review the request and provide instructions."
            )
        ))

        connection.commit()

        # Send a separate email; the login OTP function is untouched.
        if founder.get("email"):
            email_sent = send_volunteer_workflow_email(
                founder["email"],
                "CharityBridge - New Volunteer Interest",
                (
                    f"Hello {founder['name']},\n\n"
                    f"{volunteer['name']} has expressed interest in "
                    f"helping with: {help_request['request_type']}.\n"
                    f"Request ID: {request_id}\n"
                    f"Location: {help_request.get('location') or 'Not provided'}\n\n"
                    "Please log in to CharityBridge to review the request "
                    "and provide instructions to the volunteer."
                )
            )

            if not email_sent:
                print("Founder notification email could not be sent.")

        flash(
            "Your interest has been sent to the Founder!",
            "success"
        )

    except Error as e:
        connection.rollback()
        print("Volunteer interest error:", e)
        flash("Unable to submit your interest. Please try again.", "error")

    except Exception as e:
        connection.rollback()
        print("Unexpected volunteer interest error:", e)
        flash("Something went wrong while submitting your interest.", "error")

    finally:
        cursor.close()

    return redirect(url_for("volunteer"))



# ============================================================
# DASHBOARD SUPPORT LINKS
# ============================================================

@app.route("/nearby-connect")
def nearby_connect():

    return redirect(
        url_for("community")
    )





@app.route("/payment/confirm", methods=["POST"])
def confirm_payment():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("login"))

    helper_id = int(session["user_id"])
    response_id = request.form.get("response_id", type=int)
    amount_text = (request.form.get("amount_paid") or "").strip()
    uploaded_file = request.files.get("receipt_file")

    if not response_id:
        flash("Invalid help response.", "error")
        return redirect(url_for("response_page"))

    # Validate the amount.
    try:
        amount_input = Decimal(amount_text)

        if not amount_input.is_finite() or amount_input <= 0:
            raise InvalidOperation

        amount_paise = int(
            (amount_input * 100).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )

        if amount_paise <= 0:
            raise InvalidOperation

        amount_paid = Decimal(amount_paise) / Decimal("100")

    except (InvalidOperation, ValueError, TypeError):
        flash("Enter a valid payment amount.", "error")
        return redirect(url_for("response_page"))

    # A receipt is required for every new payment report.
    if not uploaded_file or not uploaded_file.filename:
        flash("Please select your payment receipt.", "error")
        return redirect(url_for("response_page"))

    original_name = secure_filename(uploaded_file.filename)

    if not original_name or "." not in original_name:
        flash("Invalid receipt filename.", "error")
        return redirect(url_for("response_page"))

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_RECEIPT_EXTENSIONS:
        flash("Only JPG, JPEG, PNG and PDF receipts are allowed.", "error")
        return redirect(url_for("response_page"))

    # Check actual file content, not just its filename.
    content = uploaded_file.read()
    uploaded_file.seek(0)

    valid_signature = (
        (extension in {"jpg", "jpeg"} and content.startswith(b"\xff\xd8\xff"))
        or (
            extension == "png"
            and content.startswith(b"\x89PNG\r\n\x1a\n")
        )
        or (
            extension == "pdf"
            and content.startswith(b"%PDF-")
        )
    )

    if not content or len(content) > 8 * 1024 * 1024:
        flash("Receipt must be non-empty and no larger than 8 MB.", "error")
        return redirect(url_for("response_page"))

    if not valid_signature:
        flash("The selected file does not match its file type.", "error")
        return redirect(url_for("response_page"))

    conn = None
    cursor = None
    saved_path = None

    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # Confirm this response belongs to the logged-in helper.
        cursor.execute("""
            SELECT
                cr.id AS response_id,
                cr.request_id,
                cr.helper_id,
                hr.user_id AS requester_id,
                hr.request_type,
                u.name AS helper_name
            FROM cb_request_responses cr
            JOIN help_requests hr
                ON hr.id = cr.request_id
            LEFT JOIN users u
                ON u.id = cr.helper_id
            WHERE cr.id = %s
            FOR UPDATE
        """, (response_id,))

        offer = cursor.fetchone()

        if not offer or int(offer["helper_id"]) != helper_id:
            conn.rollback()
            flash("You cannot report payment for this offer.", "error")
            return redirect(url_for("response_page"))

        if str(offer["request_type"]).strip().lower() != "money":
            conn.rollback()
            flash("Payment reports are only for Money requests.", "error")
            return redirect(url_for("response_page"))

        requester_id = int(offer["requester_id"])

        if requester_id == helper_id:
            conn.rollback()
            flash("You cannot pay your own request.", "error")
            return redirect(url_for("response_page"))

        # Lock the request while calculating the remaining amount.
        cursor.execute("""
            SELECT id, amount
            FROM help_requests
            WHERE id = %s
            FOR UPDATE
        """, (offer["request_id"],))

        help_request = cursor.fetchone()

        if not help_request:
            conn.rollback()
            flash("Help request not found.", "error")
            return redirect(url_for("response_page"))

        requested_amount = Decimal(str(help_request["amount"] or 0))

        if not requested_amount.is_finite() or requested_amount <= 0:
            conn.rollback()
            flash("This request has an invalid requested amount.", "error")
            return redirect(url_for("response_page"))

        # Prevent duplicate payment reports from this helper.
        cursor.execute("""
            SELECT id
            FROM cb_payment_records
            WHERE request_id = %s
              AND helper_id = %s
            LIMIT 1
            FOR UPDATE
        """, (offer["request_id"], helper_id))

        if cursor.fetchone():
            conn.rollback()
            flash(
                "You have already submitted payment details for this "
                "request. Duplicate submissions are not allowed.",
                "error"
            )
            return redirect(url_for("response_page"))

        # Count previously reported and recipient-confirmed payments.
        cursor.execute("""
            SELECT COALESCE(SUM(amount_paise), 0) AS total_paise
            FROM cb_payment_records
            WHERE request_id = %s
              AND status IN (
                  'reported',
                  'requester_confirmed',
                  'verified'
              )
        """, (offer["request_id"],))

        totals = cursor.fetchone()
        previous_paise = int(totals["total_paise"] or 0)

        requested_paise = int(
            (requested_amount * 100).quantize(Decimal("1"))
        )

        remaining_paise = requested_paise - previous_paise

        if remaining_paise <= 0:
            conn.rollback()
            flash(
                "The full requested amount has already been reported.",
                "error"
            )
            return redirect(url_for("response_page"))

        if amount_paise > remaining_paise:
            remaining_amount = Decimal(remaining_paise) / Decimal("100")
            conn.rollback()
            flash(
                f"Only ₹{remaining_amount:.2f} remains for this request.",
                "error"
            )
            return redirect(url_for("response_page"))

        new_total_paise = previous_paise + amount_paise
        new_remaining_paise = requested_paise - new_total_paise

        # Save the payment report first, within this transaction.
        cursor.execute("""
            INSERT INTO cb_payment_records
                (request_id, helper_id, amount_paise, status)
            VALUES (%s, %s, %s, 'reported')
        """, (
            offer["request_id"],
            helper_id,
            amount_paise
        ))

        payment_id = cursor.lastrowid

        # Save the receipt file using a random server-generated filename.
        stored_name = f"{uuid.uuid4().hex}.{extension}"
        saved_path = os.path.join(PAYMENT_RECEIPT_FOLDER, stored_name)

        uploaded_file.save(saved_path)

        # Link the receipt to the exact payment record just created.
        cursor.execute("""
            INSERT INTO cb_payment_receipts
                (payment_id, receipt_filename, uploaded_by)
            VALUES (%s, %s, %s)
        """, (payment_id, stored_name, helper_id))

        helper_name = offer.get("helper_name") or "A CharityBridge user"
        reported_total = Decimal(new_total_paise) / Decimal("100")
        remaining_amount = Decimal(new_remaining_paise) / Decimal("100")

        if new_remaining_paise == 0:
            message = (
                f"Payment update for your Money request "
                f"#{offer['request_id']}: {helper_name} has reported "
                f"₹{reported_total:.2f} out of ₹{requested_amount:.2f}. "
                "A receipt has been uploaded. Please check your bank or "
                "UPI app before confirming receipt. This report and receipt "
                "are not independent bank verification."
            )
        else:
            message = (
                f"Partial payment update for your Money request "
                f"#{offer['request_id']}: {helper_name} reported "
                f"₹{amount_paid:.2f}. Total reported so far: "
                f"₹{reported_total:.2f} out of ₹{requested_amount:.2f}. "
                f"Remaining amount: ₹{remaining_amount:.2f}. "
                "A receipt has been uploaded. Please check your bank or "
                "UPI app before confirming receipt."
            )

        cursor.execute("""
            INSERT INTO cb_private_messages
                (sender_id, receiver_id, message, is_read, is_delivered)
            VALUES (%s, %s, %s, 0, 0)
        """, (helper_id, requester_id, message))

        # Commit the payment, receipt record, and notification together.
        conn.commit()

        if new_remaining_paise == 0:
            flash(
                "Payment details submitted — awaiting recipient confirmation. "
                "Your payment details are available in Payment History.",
                "success"
            )
        else:
            flash(
                f"Payment details submitted — awaiting recipient confirmation. "
                f"Your payment details are available in Payment History. "
                f"₹{remaining_amount:.2f} remains.",
                "success"
            )

        return redirect(url_for("response_page"))

    except Exception:
        if conn:
            conn.rollback()
        # Remove the file if its database transaction failed.
        if saved_path and os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                app.logger.exception(
                    "Could not remove receipt after failed payment report"
                )

        app.logger.exception("Payment report and receipt upload failed")
        flash(
            "Unable to save the payment report and receipt. Please try again.",
            "error"
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("response_page"))

# ============================================================
# CHARITYBRIDGE: UPLOAD PAYMENT RECEIPT
# ============================================================

@app.route("/payment/receipt/upload", methods=["POST"])
def upload_payment_receipt():
    if "user_id" not in session:
        flash("Please log in to upload a receipt.", "error")
        return redirect(url_for("login"))

    user_id = int(session["user_id"])
    payment_id = request.form.get("payment_id", type=int)
    uploaded_file = request.files.get("receipt_file")

    if not payment_id or not uploaded_file or not uploaded_file.filename:
        flash("Select a receipt and try again.", "error")
        return redirect(url_for("payment_history"))

    original_name = secure_filename(uploaded_file.filename)
    if not original_name or "." not in original_name:
        flash("Invalid receipt filename.", "error")
        return redirect(url_for("payment_history"))

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_RECEIPT_EXTENSIONS:
        flash("Only JPG, PNG and PDF receipts are allowed.", "error")
        return redirect(url_for("payment_history"))

    # Basic file-signature validation, not a guarantee of authenticity.
    content = uploaded_file.read()
    uploaded_file.seek(0)

    valid_signature = (
        (extension in {"jpg", "jpeg"} and content.startswith(b"\xff\xd8\xff"))
        or (extension == "png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
        or (extension == "pdf" and content.startswith(b"%PDF-"))
    )

    if not valid_signature:
        flash("The selected file does not match its file type.", "error")
        return redirect(url_for("payment_history"))

    if not content or len(content) > 8 * 1024 * 1024:
        flash("Receipt must be smaller than 8 MB.", "error")
        return redirect(url_for("payment_history"))

    conn = None
    cursor = None
    saved_path = None

    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.id,
                p.helper_id,
                p.status,
                hr.user_id AS requester_id
            FROM cb_payment_records p
            JOIN help_requests hr ON hr.id = p.request_id
            WHERE p.id = %s
            FOR UPDATE
        """, (payment_id,))

        payment = cursor.fetchone()

        if not payment or int(payment["helper_id"]) != user_id:
            conn.rollback()
            flash("You cannot upload a receipt for this payment.", "error")
            return redirect(url_for("payment_history"))

        if str(payment["status"]).lower() not in {
            "reported", "requester_confirmed", "verified"
        }:
            conn.rollback()
            flash("This payment is not ready for receipt upload.", "error")
            return redirect(url_for("payment_history"))

        cursor.execute("""
            SELECT id
            FROM cb_payment_receipts
            WHERE payment_id = %s
            FOR UPDATE
        """, (payment_id,))

        if cursor.fetchone():
            conn.rollback()
            flash(
                "A receipt is already attached to this payment. "
                "Please contact the recipient if it needs correction.",
                "error"
            )
            return redirect(url_for("payment_history"))

        stored_name = f"{uuid.uuid4().hex}.{extension}"
        saved_path = os.path.join(PAYMENT_RECEIPT_FOLDER, stored_name)
        uploaded_file.save(saved_path)

        cursor.execute("""
            INSERT INTO cb_payment_receipts
                (payment_id, receipt_filename, uploaded_by)
            VALUES (%s, %s, %s)
        """, (payment_id, stored_name, user_id))

        conn.commit()
        flash("Receipt uploaded. The recipient can now review it.", "success")

    except Exception:
        if conn:
            conn.rollback()

        if saved_path and os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                app.logger.exception("Could not remove failed receipt upload")

        app.logger.exception("Payment receipt upload failed")
        flash("Unable to upload the receipt. Please try again.", "error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("payment_history"))



# ============================================================
# CHARITYBRIDGE: VIEW RECEIPT WITH ACCESS CONTROL
# ============================================================

@app.route("/payment/receipt/<int:payment_id>")
def view_payment_receipt(payment_id):
    if "user_id" not in session:
        flash("Please log in to view this receipt.", "error")
        return redirect(url_for("login"))

    user_id = int(session["user_id"])
    conn = None
    cursor = None

    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                r.receipt_filename,
                p.helper_id,
                hr.user_id AS requester_id
            FROM cb_payment_receipts r
            JOIN cb_payment_records p
                ON p.id = r.payment_id
            JOIN help_requests hr
                ON hr.id = p.request_id
            WHERE r.payment_id = %s
            LIMIT 1
        """, (payment_id,))

        receipt = cursor.fetchone()

        if not receipt:
            abort(404, description="Receipt record not found.")

        if user_id not in (
            int(receipt["helper_id"]),
            int(receipt["requester_id"])
        ):
            abort(403)

        filename = os.path.basename(receipt["receipt_filename"])
        path = os.path.join(PAYMENT_RECEIPT_FOLDER, filename)

        if not os.path.isfile(path):
            app.logger.error("Receipt file missing: %s", path)
            abort(404, description="Receipt file not found on the server.")

        extension = filename.rsplit(".", 1)[-1].lower()
        mimetype = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "pdf": "application/pdf"
        }.get(extension, "application/octet-stream")

        return send_file(
            path,
            mimetype=mimetype,
            as_attachment=False,
            download_name=filename
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# CHARITYBRIDGE: RECIPIENT CONFIRMS OR REPORTS A PROBLEM
# ============================================================

@app.route("/payment/receipt/decision", methods=["POST"])
def decide_payment_receipt():
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("login"))

    requester_id = int(session["user_id"])
    payment_id = request.form.get("payment_id", type=int)
    decision = (request.form.get("decision") or "").strip().lower()
    note = (request.form.get("recipient_note") or "").strip()

    if decision not in {"confirmed", "problem_reported"}:
        flash("Invalid receipt decision.", "error")
        return redirect(url_for("payment_history"))

    if len(note) > 500:
        flash("The note must be 500 characters or fewer.", "error")
        return redirect(url_for("payment_history"))

    conn = None
    cursor = None

    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                r.id AS receipt_id,
                r.recipient_decision,
                p.id AS payment_id,
                p.status,
                hr.user_id AS requester_id
            FROM cb_payment_receipts r
            JOIN cb_payment_records p ON p.id = r.payment_id
            JOIN help_requests hr ON hr.id = p.request_id
            WHERE p.id = %s
            FOR UPDATE
        """, (payment_id,))

        receipt = cursor.fetchone()

        if not receipt or int(receipt["requester_id"]) != requester_id:
            conn.rollback()
            abort(403)

        if receipt["recipient_decision"] != "pending":
            conn.rollback()
            flash("A decision has already been recorded for this receipt.", "error")
            return redirect(url_for("payment_history"))

        if decision == "confirmed":
            # Confirmation records the recipient's statement; it is not
            # independent bank verification.
            cursor.execute("""
                UPDATE cb_payment_records
                SET status = 'requester_confirmed'
                WHERE id = %s AND status = 'reported'
            """, (payment_id,))

            if cursor.rowcount != 1:
                conn.rollback()
                flash(
                    "This payment cannot be confirmed in its current status.",
                    "error"
                )
                return redirect(url_for("payment_history"))

        cursor.execute("""
            UPDATE cb_payment_receipts
            SET recipient_decision = %s,
                recipient_decided_at = CURRENT_TIMESTAMP,
                recipient_note = %s
            WHERE id = %s AND recipient_decision = 'pending'
        """, (decision, note or None, receipt["receipt_id"]))

        if cursor.rowcount != 1:
            conn.rollback()
            flash("The receipt decision could not be saved.", "error")
            return redirect(url_for("payment_history"))

        conn.commit()

        if decision == "confirmed":
            flash(
                "Receipt confirmed. This records the recipient's "
                "confirmation; it is not independent bank verification.",
                "success"
            )
        else:
            flash(
                "Problem reported. The payment remains unverified "
                "until the issue is resolved.",
                "success"
            )

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("Receipt decision failed")
        flash("Unable to save your decision. Please try again.", "error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("payment_history"))


@app.route("/payment/confirm-received/<int:payment_id>", methods=["POST"])
def confirm_payment_received(payment_id):
    if "user_id" not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for("login"))

    requester_id = int(session["user_id"])
    conn = None
    cursor = None

    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                p.id,
                p.status,
                p.helper_id,
                p.request_id,
                p.amount_paise,
                hr.user_id AS requester_id,
                hr.amount AS requested_amount,
                u.name AS requester_name
            FROM cb_payment_records p
            JOIN help_requests hr
                ON hr.id = p.request_id
            LEFT JOIN users u
                ON u.id = hr.user_id
            WHERE p.id = %s
            FOR UPDATE
        """, (payment_id,))

        payment = cursor.fetchone()

        if not payment:
            conn.rollback()
            flash("Payment record not found.", "error")
            return redirect(url_for("payment_history"))

        if int(payment["requester_id"]) != requester_id:
            conn.rollback()
            flash(
                "Only the requester can confirm receipt of this payment.",
                "error"
            )
            return redirect(url_for("payment_history"))

        if payment["status"] != "reported":
            conn.rollback()
            flash(
                "Only reported payments can be confirmed here.",
                "error"
            )
            return redirect(url_for("payment_history"))

        cursor.execute("""
           UPDATE cb_payment_records
SET status = 'requester_confirmed',
    verified_at = CURRENT_TIMESTAMP
WHERE id = %s
  AND status = 'reported'
""", (payment_id,))

        if cursor.rowcount != 1:
            conn.rollback()
            flash("This payment has already been processed.", "error")
            return redirect(url_for("payment_history"))

        # Tell the helper that the requester confirmed receipt.
        requester_name = payment.get("requester_name") or "The requester"
        amount = Decimal(int(payment["amount_paise"])) / Decimal("100")

        message = (
            f"{requester_name} confirmed receiving ₹{amount:.2f} "
            f"for Money request #{payment['request_id']}. "
            "This confirmation was made by the requester and was not "
            "independently verified by the bank."
        )

        cursor.execute("""
            INSERT INTO cb_private_messages
                (sender_id, receiver_id, message, is_read, is_delivered)
            VALUES (%s, %s, %s, 0, 0)
        """, (
            requester_id,
            int(payment["helper_id"]),
            message
        ))

        conn.commit()

        flash(
            "Receipt confirmed by the requester. "
            "It is not independently bank-verified.",
            "success"
        )

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("Requester payment confirmation failed")
        flash("Unable to confirm receipt. Please try again.", "error")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("payment_history"))

# ============================================================
# CHAT PAGE
# REAL USERS + PRIVATE CHAT
# ============================================================

@app.route("/chat")
def chat():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Person selected from Community -> Message
    selected_user_id = request.args.get(
        "user_id",
        type=int
    )

    conn = None
    cursor = None

    try:

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # ========================================================
        # CURRENT LOGGED-IN USER
        # ========================================================

        cursor.execute(
            """
            SELECT
                u.id,
                u.name,
                u.email,
                u.phone,
                u.role,
                u.email_verified,
                u.created_at,

                up.location,
                up.profile_image,
                up.profession

            FROM users u

            LEFT JOIN user_profiles up
                ON u.id = up.user_id

            WHERE u.id = %s

            LIMIT 1
            """,
            (user_id,)
        )

        current_user = cursor.fetchone()

        if not current_user:

            session.clear()

            return redirect(
                url_for("login")
            )

        # ========================================================
        # ALL COMMUNITY USERS
        # ========================================================
        # IMPORTANT:
        # Users are loaded directly from the users table.
        # Logout does NOT remove them.
        # ========================================================

        cursor.execute(
            """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role,
                u.email_verified,
                u.created_at,

                up.location,
                up.profile_image,
                up.profession

            FROM users u

            LEFT JOIN user_profiles up
                ON u.id = up.user_id

            WHERE u.id != %s

            ORDER BY u.name ASC
            """,
            (user_id,)
        )

        community_users = cursor.fetchall()

        # ========================================================
        # SELECTED USER
        # ========================================================

        selected_user = None

        if selected_user_id:

            # ----------------------------------------------------
            # Prevent messaging yourself
            # ----------------------------------------------------

            if int(selected_user_id) == int(user_id):

                selected_user_id = None

            else:

                cursor.execute(
                    """
                    SELECT
                        u.id,
                        u.name,
                        u.email,
                        u.role,
                        u.email_verified,
                        u.created_at,

                        up.location,
                        up.profile_image,
                        up.profession

                    FROM users u

                    LEFT JOIN user_profiles up
                        ON u.id = up.user_id

                    WHERE u.id = %s

                    LIMIT 1
                    """,
                    (selected_user_id,)
                )

                selected_user = cursor.fetchone()

                # ------------------------------------------------
                # Selected user doesn't exist
                # ------------------------------------------------

                if not selected_user:

                    selected_user_id = None

        # ========================================================
        # PRIVATE MESSAGES
        # ========================================================
        # Only show the conversation between the logged-in user
        # and the selected user.
        # ========================================================

        messages = []

        if selected_user_id:

            cursor.execute(
                """
                SELECT
                    m.id,
                    m.sender_id,
                    m.receiver_id,
                    m.message,
                    m.is_read,
                    m.created_at,

                    sender.name AS sender_name,
                    receiver.name AS receiver_name

                FROM cb_private_messages m

                LEFT JOIN users sender
                    ON m.sender_id = sender.id

                LEFT JOIN users receiver
                    ON m.receiver_id = receiver.id

                WHERE
                    (
                        m.sender_id = %s
                        AND
                        m.receiver_id = %s
                    )

                    OR

                    (
                        m.sender_id = %s
                        AND
                        m.receiver_id = %s
                    )

                ORDER BY m.created_at ASC
                """,
                (
                    user_id,
                    selected_user_id,
                    selected_user_id,
                    user_id
                )
            )

            messages = cursor.fetchall()

       
        # ========================================================
        # MARK SELECTED USER'S MESSAGES AS DELIVERED AND READ
        # ========================================================

        if selected_user_id:
            cursor.execute(
                """
                UPDATE cb_private_messages
                SET is_delivered = 1,
                    is_read = 1
                WHERE receiver_id = %s
                  AND sender_id = %s
                  AND (
                      is_delivered = 0
                      OR is_read = 0
                  )
                """,
                (user_id, selected_user_id)
            )

            conn.commit()

            # Reload messages with the updated status
            cursor.execute(
                """
                SELECT
                    m.id,
                    m.sender_id,
                    m.receiver_id,
                    m.message,
                    m.is_read,
                    m.is_delivered,
                    m.created_at,
                    sender.name AS sender_name,
                    receiver.name AS receiver_name
                FROM cb_private_messages m
                LEFT JOIN users sender
                    ON m.sender_id = sender.id
                LEFT JOIN users receiver
                    ON m.receiver_id = receiver.id
                WHERE
                    (
                        m.sender_id = %s
                        AND m.receiver_id = %s
                    )
                    OR
                    (
                        m.sender_id = %s
                        AND m.receiver_id = %s
                    )
                ORDER BY m.created_at ASC
                """,
                (
                    user_id,
                    selected_user_id,
                    selected_user_id,
                    user_id
                )
            )

            messages = cursor.fetchall()

        # ========================================================
        # UNREAD MESSAGE COUNT
        # ========================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS unread_count

            FROM cb_private_messages

            WHERE receiver_id = %s
              AND is_read = 0
            """,
            (user_id,)
        )

        unread_result = cursor.fetchone()

        unread_messages = (
            int(unread_result["unread_count"])
            if unread_result
            else 0
        )

        # ========================================================
        # NOTIFICATIONS
        # ========================================================

        cursor.execute(
            """
            SELECT
                id,
                title,
                message,
                is_read,
                created_at

            FROM cb_notifications

            WHERE user_id = %s

            ORDER BY created_at DESC

            LIMIT 20
            """,
            (user_id,)
        )

        notifications = cursor.fetchall()

        # ========================================================
        # UNREAD NOTIFICATION COUNT
        # ========================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS unread_count

            FROM cb_notifications

            WHERE user_id = %s
              AND is_read = 0
            """,
            (user_id,)
        )

        notification_result = cursor.fetchone()

        unread_notifications = (
            int(notification_result["unread_count"])
            if notification_result
            else 0
        )

        # ========================================================
        # TOTAL COMMUNITY USERS
        # ========================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_users

            FROM users
            """
        )

        user_count_result = cursor.fetchone()

        total_users = (
            int(user_count_result["total_users"])
            if user_count_result
            else 0
        )

        # ========================================================
        # CHAT PAGE
        # ========================================================

        return render_template(
            "chat.html",

            current_user=current_user,

            community_users=community_users,

            messages=messages,

            notifications=notifications,

            unread_messages=unread_messages,

            unread_notifications=unread_notifications,

            total_users=total_users,

            selected_user_id=selected_user_id,

            selected_user=selected_user
        )

    # ============================================================
    # ERROR HANDLING
    # ============================================================

    except Exception as e:

        print(
            "CHAT PAGE ERROR:",
            e
        )

        return render_template(
            "chat.html",

            current_user={
                "id": user_id,

                "name": session.get(
                    "user_name",
                    "User"
                ),

                "email": session.get(
                    "user_email",
                    ""
                ),

                "role": session.get(
                    "role",
                    "user"
                ),

                "email_verified": 0,

                "profile_image": None,

                "location": None,

                "profession": None
            },

            community_users=[],

            messages=[],

            notifications=[],

            unread_messages=0,

            unread_notifications=0,

            total_users=0,

            selected_user_id=None,

            selected_user=None
        )

    # ============================================================
    # CLEANUP
    # ============================================================

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
           
# ============================================================
# SEND PRIVATE CHAT MESSAGE
# ============================================================

@app.route("/chat/send", methods=["POST"])
def send_chat_message():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = None
    cursor = None

    try:
        sender_id = int(session["user_id"])
        data = request.get_json(silent=True) or {}

        receiver_id = data.get("receiver_id")
        message = str(data.get("message", "")).strip()

        try:
            receiver_id = int(receiver_id)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Invalid receiver."
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "message": "Message cannot be empty."
            }), 400

        if len(message) > 5000:
            return jsonify({
                "success": False,
                "message": "Message is too long."
            }), 400

        if sender_id == receiver_id:
            return jsonify({
                "success": False,
                "message": "You cannot message yourself."
            }), 400

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name FROM users WHERE id = %s LIMIT 1",
            (receiver_id,)
        )
        receiver = cursor.fetchone()

        if not receiver:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        cursor.execute(
            """
            INSERT INTO cb_private_messages
                (sender_id, receiver_id, message, is_read, is_delivered)
            VALUES (%s, %s, %s, 0, 0)
            """,
            (sender_id, receiver_id, message)
        )

        message_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            """
            SELECT
                m.id,
                m.sender_id,
                m.receiver_id,
                m.message,
                m.is_read,
                m.is_delivered,
                m.created_at,
                sender.name AS sender_name,
                receiver.name AS receiver_name
            FROM cb_private_messages m
            LEFT JOIN users sender ON m.sender_id = sender.id
            LEFT JOIN users receiver ON m.receiver_id = receiver.id
            WHERE m.id = %s
            LIMIT 1
            """,
            (message_id,)
        )

        saved_message = cursor.fetchone()

        return jsonify({
            "success": True,
            "message": "Message saved successfully.",
            "data": saved_message
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("SEND CHAT MESSAGE ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to send message."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
            
# ============================================================
# SEND CHAT FILE OR VOICE MESSAGE
# ============================================================

@app.route("/chat/upload", methods=["POST"])
def upload_chat_message():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = None
    cursor = None
    saved_path = None

    try:
        sender_id = int(session["user_id"])

        receiver_id = request.form.get(
            "receiver_id", type=int
        )

        message_text = (
            request.form.get("message", "").strip()
        )

        uploaded_file = request.files.get("file")

        if not receiver_id or receiver_id == sender_id:
            return jsonify({
                "success": False,
                "message": "Invalid chat recipient."
            }), 400

        if not uploaded_file or not uploaded_file.filename:
            return jsonify({
                "success": False,
                "message": "Please select a file."
            }), 400

        original_name = uploaded_file.filename
        extension = os.path.splitext(original_name)[1].lower()

        allowed_extensions = {
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".mp4", ".webm", ".mov",
            ".mp3", ".wav", ".ogg", ".m4a", ".aac",
            ".pdf", ".txt", ".doc", ".docx",
            ".xls", ".xlsx", ".ppt", ".pptx",
            ".zip"
        }

        if extension not in allowed_extensions:
            return jsonify({
                "success": False,
                "message": "This file type is not supported."
            }), 400

        # Limit uploads to 20 MB.
        if uploaded_file.content_length and uploaded_file.content_length > 20 * 1024 * 1024:
            return jsonify({
                "success": False,
                "message": "File must be 20 MB or smaller."
            }), 413

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE id = %s LIMIT 1",
            (receiver_id,)
        )

        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        upload_folder = os.path.join(
            app.root_path, "static", "uploads", "chat"
        )
        os.makedirs(upload_folder, exist_ok=True)

        unique_name = secrets.token_hex(16) + extension
        saved_path = os.path.join(upload_folder, unique_name)

        uploaded_file.save(saved_path)

        relative_path = "uploads/chat/" + unique_name

        if extension in {".mp3", ".wav", ".ogg", ".m4a", ".aac"}:
            media_type = "audio"
        elif extension in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            media_type = "image"
        elif extension in {".mp4", ".webm", ".mov"}:
            media_type = "video"
        else:
            media_type = "file"

        cursor.execute(
            """
            INSERT INTO cb_private_messages
                (sender_id, receiver_id, message,
                 is_read, is_delivered, media_path, media_type)
            VALUES (%s, %s, %s, 0, 0, %s, %s)
            """,
            (
                sender_id,
                receiver_id,
                message_text or original_name,
                relative_path,
                media_type
            )
        )

        message_id = cursor.lastrowid
        conn.commit()

        cursor.execute(
            """
            SELECT id, sender_id, receiver_id, message,
                   is_read, is_delivered, created_at,
                   media_path, media_type
            FROM cb_private_messages
            WHERE id = %s
            """,
            (message_id,)
        )

        saved_message = cursor.fetchone()

        if saved_message and saved_message.get("created_at"):
            saved_message["created_at"] = (
                saved_message["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            )

        return jsonify({
            "success": True,
            "message": "File sent successfully.",
            "data": saved_message
        })

    except Exception as e:
        if conn:
            conn.rollback()

        # Remove an uploaded file if saving the database record failed.
        if saved_path and os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                pass

        print("CHAT UPLOAD ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to upload the file."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            

@app.route("/chat/delete/<int:message_id>", methods=["POST"])
def delete_chat_message(message_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = None
    cursor = None

    try:
        current_user_id = int(session["user_id"])
        data = request.get_json(silent=True) or {}
        delete_for = data.get("delete_for", "me")

        if delete_for not in ("me", "everyone"):
            return jsonify({
                "success": False,
                "message": "Invalid delete option."
            }), 400

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, sender_id, receiver_id
            FROM cb_private_messages
            WHERE id = %s
            LIMIT 1
            """,
            (message_id,)
        )
        message = cursor.fetchone()

        if not message:
            return jsonify({
                "success": False,
                "message": "Message not found."
            }), 404

        if current_user_id not in (
            int(message["sender_id"]),
            int(message["receiver_id"])
        ):
            return jsonify({
                "success": False,
                "message": "You cannot delete this message."
            }), 403

        if delete_for == "everyone":
            if current_user_id != int(message["sender_id"]):
                return jsonify({
                    "success": False,
                    "message": "Only the sender can delete for everyone."
                }), 403

            cursor.execute(
                """
                UPDATE cb_private_messages
                SET message = 'This message was deleted.',
                    media_path = NULL,
                    media_type = NULL
                WHERE id = %s
                """,
                (message_id,)
            )

            result_message = "Message deleted for everyone."

        else:
            cursor.execute(
                """
                INSERT IGNORE INTO cb_private_message_deletions
                    (message_id, user_id)
                VALUES (%s, %s)
                """,
                (message_id, current_user_id)
            )

            result_message = "Message deleted for you."

        conn.commit()

        return jsonify({
            "success": True,
            "message": result_message
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("DELETE CHAT MESSAGE ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to delete message."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

            
# ============================================================
# REFRESH PRIVATE CHAT MESSAGE STATUSES
# ============================================================

@app.route("/chat/status", methods=["GET"])
def chat_message_status():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    conn = None
    cursor = None

    try:
        current_user_id = int(session["user_id"])
        other_user_id = request.args.get("user_id", type=int)

        if not other_user_id or other_user_id == current_user_id:
            return jsonify({
                "success": False,
                "message": "Invalid chat user."
            }), 400

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        # When the recipient opens this chat, mark incoming
        # messages as delivered and read.
        cursor.execute(
            """
            UPDATE cb_private_messages
            SET is_delivered = 1,
                is_read = 1
            WHERE sender_id = %s
              AND receiver_id = %s
              AND (is_delivered = 0 OR is_read = 0)
            """,
            (other_user_id, current_user_id)
        )

        conn.commit()

        # Return statuses for messages sent by the current user.
        cursor.execute(
            """
            SELECT id, is_delivered, is_read
            FROM cb_private_messages
            WHERE sender_id = %s
              AND receiver_id = %s
            ORDER BY id ASC
            """,
            (current_user_id, other_user_id)
        )

        statuses = cursor.fetchall()

        return jsonify({
            "success": True,
            "statuses": statuses
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("CHAT STATUS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to refresh message status."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ============================================================
# NEARBY NOTIFICATION
# ============================================================

@app.route("/nearby-notification")
def nearby_notification():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = db

    if connection is None:

        return redirect(
            url_for("dashboard")
        )

    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE cb_notifications
            SET is_read = 1
            WHERE user_id = %s
            AND is_read = 0
        """, (
            session["user_id"],
        ))

        connection.commit()

    except Error as e:

        connection.rollback()

        print(
            "Notification error:",
            e
        )

    finally:

        cursor.close()


    return redirect(
        url_for("dashboard") + "#notifications"
    )


# ============================================================
# MARK NOTIFICATION
# ============================================================

@app.route(
    "/mark-notification/<int:notification_id>",
    methods=["POST", "GET"]
)
def mark_notification(notification_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    connection = db

    if connection is None:

        return redirect(
            url_for("dashboard")
        )

    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE cb_notifications
            SET is_read = 1
            WHERE id = %s
            AND user_id = %s
        """, (
            notification_id,
            session["user_id"]
        ))

        connection.commit()

    except Error as e:

        connection.rollback()

        print(
            "Mark notification error:",
            e
        )

    finally:

        cursor.close()


    return redirect(
        url_for("dashboard") + "#notifications"
    )


# ============================================================
# IMPACT
# ============================================================

@app.route("/impact")
def impact():

    return redirect(
        url_for("community")
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested CharityBridge page does not exist.</p>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 - Server Error</h1>
    <p>Something went wrong on the CharityBridge server.</p>
    """, 500

@app.route("/api/charity-ai", methods=["POST"])
def charity_ai():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    try:
        data = request.get_json(silent=True) or {}
        user_message = str(data.get("message", "")).strip()

        if not user_message:
            return jsonify({
                "success": False,
                "message": "Please enter a question."
            }), 400

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return jsonify({
                "success": False,
                "message": "AI service is not configured yet."
            }), 500

        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model="gpt-5-mini",
            instructions="""
You are CharityBridge AI, the official helpful assistant
inside the CharityBridge charity platform.

Your job is to answer questions clearly and safely about:

- CharityBridge
- donating money or items
- food donations
- clothes donations
- furniture donations
- blood donation information
- requesting help
- volunteering
- community connections
- messaging
- profiles
- how the CharityBridge platform works

Be friendly, concise, practical and easy to understand.

Do not claim that you personally completed a donation,
created a request, contacted a person, or performed an
action unless the application actually confirms that action.

If the user asks about something unrelated to CharityBridge,
you may answer briefly when useful, but guide the conversation
back toward charity and community assistance.

Never invent CharityBridge database information.
""",
            input=user_message
        )

        answer = response.output_text.strip()

        return jsonify({
            "success": True,
            "answer": answer
        })

    except Exception as e:
        print("CHARITY AI ERROR:", e)

        return jsonify({
            "success": False,
            "message": "CharityBridge AI is temporarily unavailable."
        }), 500
    
@app.route("/payment/test/<int:request_id>", methods=["POST"])
def test_payment(request_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    if not PAYMENT_TEST_MODE:
        return jsonify({
            "success": False,
            "message": "Test payments are disabled."
        }), 403

    connection = None
    cursor = None

    try:
        from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

        helper_id = int(session["user_id"])
        data = request.get_json(silent=True) or request.form
        raw_amount = data.get("amount", "")

        try:
            payment_amount = Decimal(str(raw_amount))

            if not payment_amount.is_finite() or payment_amount <= 0:
                raise InvalidOperation

            amount_paise = int(
                (payment_amount * 100).quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP
                )
            )

        except (InvalidOperation, ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Enter a valid payment amount."
            }), 400

        if amount_paise <= 0:
            return jsonify({
                "success": False,
                "message": "Payment amount must be at least ₹0.01."
            }), 400

        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, user_id, request_type, amount
            FROM help_requests
            WHERE id = %s
            LIMIT 1
        """, (request_id,))

        help_request = cursor.fetchone()

        if not help_request:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Help request not found."
            }), 404

        if str(help_request["request_type"]).strip().lower() != "money":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Only Money requests support payment testing."
            }), 400

        if int(help_request["user_id"]) == helper_id:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "You cannot pay your own request."
            }), 400

        total_paise = int(
            (Decimal(str(help_request["amount"])) * 100).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP
            )
        )

        cursor.execute("""
            SELECT COALESCE(SUM(amount_paise), 0) AS paid_paise
            FROM cb_payment_records
            WHERE request_id = %s
              AND status = 'simulated'
        """, (request_id,))

        result = cursor.fetchone()
        paid_paise = int(result["paid_paise"] or 0)
        remaining_paise = max(0, total_paise - paid_paise)

        if remaining_paise == 0:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "The requested amount is already covered in test records."
            }), 400

        if amount_paise > remaining_paise:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": (
                    f"Only ₹{remaining_paise / 100:.2f} "
                    "remains in this test request."
                )
            }), 400

        cursor.execute("""
            INSERT INTO cb_payment_records
                (request_id, helper_id, amount_paise, status)
            VALUES (%s, %s, %s, 'simulated')
        """, (request_id, helper_id, amount_paise))

        new_paid_paise = paid_paise + amount_paise
        new_remaining_paise = max(0, total_paise - new_paid_paise)

        connection.commit()

        return jsonify({
            "success": True,
            "test_only": True,
            "message": "Test payment recorded. No real money was transferred.",
            "request_id": request_id,
            "simulated_payment_rupees": f"{amount_paise / 100:.2f}",
            "total_paid_in_test_records": f"{new_paid_paise / 100:.2f}",
            "remaining_in_test_records": f"{new_remaining_paise / 100:.2f}",
            "request_fulfilled": False
        })

    except Exception:
        if connection:
            connection.rollback()

        app.logger.exception("Test payment failed")

        return jsonify({
            "success": False,
            "message": "Unable to record the test payment."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
            
# ============================================================
# CREATE RAZORPAY TEST PAYMENT ORDER
# ============================================================

@app.route("/payment/create-order/<int:request_id>", methods=["POST"])
def create_razorpay_order(request_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    if razorpay_client is None:
        return jsonify({
            "success": False,
            "message": "Razorpay test keys are not configured."
        }), 503

    conn = None
    cursor = None

    try:
        helper_id = int(session["user_id"])
        amount = Decimal(str(request.form.get("amount", "0")))

        if not amount.is_finite() or amount <= 0:
            return jsonify({
                "success": False,
                "message": "Enter a valid payment amount."
            }), 400

        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        amount_paise = int(amount * 100)

        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, user_id, request_type, amount
            FROM help_requests
            WHERE id = %s
            LIMIT 1
            FOR UPDATE
        """, (request_id,))

        help_request = cursor.fetchone()

        if not help_request:
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "Help request not found."
            }), 404

        if str(help_request.get("request_type") or "").lower() != "money":
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "Payments are only available for money requests."
            }), 400

        if int(help_request["user_id"]) == helper_id:
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "You cannot pay your own request."
            }), 400

        cursor.execute("""
            SELECT COALESCE(SUM(amount_paise), 0) AS paid_paise
            FROM cb_payment_records
            WHERE request_id = %s
              AND status = 'verified'
        """, (request_id,))

        paid_paise = int(cursor.fetchone()["paid_paise"] or 0)
        requested_paise = int(
            (Decimal(str(help_request["amount"])) * 100)
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        remaining_paise = requested_paise - paid_paise

        if remaining_paise <= 0:
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "This request is already fully paid."
            }), 400

        if amount_paise > remaining_paise:
            conn.rollback()
            return jsonify({
                "success": False,
                "message": f"Remaining amount is ₹{remaining_paise / 100:.2f}."
            }), 400

        order = razorpay_client.order.create(data={
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"cb-{request_id}-{secrets.token_hex(6)}",
            "notes": {
                "request_id": str(request_id),
                "helper_id": str(helper_id)
            }
        })

        cursor.execute("""
            INSERT INTO cb_payment_records
                (request_id, helper_id, gateway_order_id,
                 amount_paise, status)
            VALUES (%s, %s, %s, %s, 'created')
        """, (
            request_id,
            helper_id,
            order["id"],
            amount_paise
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "key_id": RAZORPAY_KEY_ID,
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "request_id": request_id
        })

    except Exception:
        if conn:
            conn.rollback()

        app.logger.exception("Razorpay order creation failed")

        return jsonify({
            "success": False,
            "message": "Unable to create the payment order."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# FOUNDER: SEND FOOD DELIVERY OFFER TO A VOLUNTEER
# ============================================================

@app.route("/founder/food-delivery/send", methods=["POST"])
def send_food_delivery_offer():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("volunteer"))

    cursor = connection.cursor(dictionary=True)

    try:
        founder_user_id = session["user_id"]

        # Verify the founder's role directly from the database.
        cursor.execute("""
            SELECT role
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (founder_user_id,))

        founder = cursor.fetchone()

        if not founder or str(
            founder.get("role") or ""
        ).strip().lower() != "founder":

            flash(
                "Only the founder can send delivery offers.",
                "error"
            )
            return redirect(url_for("volunteer"))

        # Read submitted delivery details.
        request_id = request.form.get("request_id", type=int)
        volunteer_user_id = request.form.get(
            "volunteer_user_id", type=int
        )

        recipient_name = request.form.get(
            "recipient_name", ""
        ).strip()

        recipient_phone = request.form.get(
            "recipient_phone", ""
        ).strip()

        recipient_address = request.form.get(
            "recipient_address", ""
        ).strip()

        delivery_message = request.form.get(
            "delivery_message", ""
        ).strip()

        if (
            not request_id
            or not volunteer_user_id
            or not recipient_name
            or not recipient_phone
            or not recipient_address
        ):
            flash(
                "Please provide the request, volunteer, "
                "recipient name, phone and delivery address.",
                "error"
            )
            return redirect(url_for("volunteer"))

        # Confirm that this is a food-related help request.
        cursor.execute("""
            SELECT id, user_id, request_type, description, status
            FROM help_requests
            WHERE id = %s
              AND (
                  LOWER(COALESCE(request_type, '')) LIKE '%food%'
                  OR LOWER(COALESCE(description, '')) LIKE '%food%'
              )
            LIMIT 1
        """, (request_id,))

        food_request = cursor.fetchone()

        if not food_request:
            flash(
                "The selected food request could not be found.",
                "error"
            )
            return redirect(url_for("volunteer"))

        if str(food_request.get("status") or "").lower() not in (
            "pending", "available"
        ):
            flash(
                "This request is not currently available.",
                "error"
            )
            return redirect(url_for("volunteer"))

        # Confirm that the selected volunteer is registered
        # and currently available.
        cursor.execute("""
            SELECT user_id, availability
            FROM volunteers
            WHERE user_id = %s
            LIMIT 1
        """, (volunteer_user_id,))

        volunteer_record = cursor.fetchone()

        if (
            not volunteer_record
            or volunteer_record.get("availability") != "Available"
        ):
            flash(
                "Please select a registered, available volunteer.",
                "error"
            )
            return redirect(url_for("volunteer"))

        # Prevent duplicate pending offers for the same
        # request and volunteer.
        cursor.execute("""
            SELECT id
            FROM food_deliveries
            WHERE request_id = %s
              AND volunteer_user_id = %s
              AND status IN (
                  'pending_confirmation',
                  'accepted',
                  'assigned',
                  'in_progress'
              )
            LIMIT 1
        """, (request_id, volunteer_user_id))

        if cursor.fetchone():
            flash(
                "An active delivery already exists for this "
                "request and volunteer.",
                "error"
            )
            return redirect(url_for("volunteer"))

        # Create the delivery offer.
        cursor.execute("""
            INSERT INTO food_deliveries (
                request_id,
                volunteer_user_id,
                founder_user_id,
                recipient_name,
                recipient_phone,
                recipient_address,
                delivery_message,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    'pending_confirmation')
        """, (
            request_id,
            volunteer_user_id,
            founder_user_id,
            recipient_name,
            recipient_phone,
            recipient_address,
            delivery_message or None
        ))

        connection.commit()

        flash(
            "Food delivery offer sent to the volunteer.",
            "success"
        )

    except Error as e:
        connection.rollback()
        print("Food delivery offer database error:", e)

        flash(
            "Unable to send the food delivery offer.",
            "error"
        )

    except Exception as e:
        connection.rollback()
        print("Food delivery offer error:", e)

        flash(
            "Something went wrong while sending the offer.",
            "error"
        )

    finally:
        cursor.close()

    return redirect(url_for("volunteer"))

# ============================================================
# VOLUNTEER: ACCEPT OR DECLINE A FOOD DELIVERY OFFER
# ============================================================

@app.route(
    "/volunteer/food-delivery/<int:delivery_id>/respond",
    methods=["POST"]
)
def respond_to_food_delivery(delivery_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("volunteer"))

    cursor = connection.cursor(dictionary=True)

    try:
        volunteer_user_id = session["user_id"]

        # Verify the volunteer's response belongs to their account.
        cursor.execute("""
            SELECT id, status
            FROM food_deliveries
            WHERE id = %s
              AND volunteer_user_id = %s
            LIMIT 1
        """, (delivery_id, volunteer_user_id))

        delivery = cursor.fetchone()

        if not delivery:
            flash(
                "Delivery offer not found for your account.",
                "error"
            )
            return redirect(url_for("volunteer"))

        if delivery["status"] != "pending_confirmation":
            flash(
                "You can respond only to a pending delivery offer.",
                "error"
            )
            return redirect(url_for("volunteer"))

        response = request.form.get("response", "").strip().lower()

        if response not in ("accepted", "declined"):
            flash("Please choose Accept or Decline.", "error")
            return redirect(url_for("volunteer"))

        # Update only this volunteer's pending offer.
        cursor.execute("""
            UPDATE food_deliveries
            SET status = %s,
                volunteer_response_at = CURRENT_TIMESTAMP
            WHERE id = %s
              AND volunteer_user_id = %s
              AND status = 'pending_confirmation'
        """, (
            response,
            delivery_id,
            volunteer_user_id
        ))

        if cursor.rowcount != 1:
            connection.rollback()
            flash(
                "The offer has already been updated. Please refresh.",
                "error"
            )
            return redirect(url_for("volunteer"))

        # Notify the founder.
        cursor.execute("""
            INSERT INTO cb_notifications (
                user_id,
                title,
                message
            )
            SELECT founder_user_id,
                   'Food delivery response',
                   %s
            FROM food_deliveries
            WHERE id = %s
        """, (
            "The volunteer "
            + response
            + " the food delivery offer.",
            delivery_id
        ))

        connection.commit()

        if response == "accepted":
            flash(
                "You accepted the food delivery offer.",
                "success"
            )
        else:
            flash(
                "You declined the food delivery offer.",
                "success"
            )

    except Error as e:
        connection.rollback()
        print("Food delivery response database error:", e)
        flash("Unable to save your response.", "error")

    except Exception as e:
        connection.rollback()
        print("Food delivery response error:", e)
        flash("Something went wrong while responding.", "error")

    finally:
        cursor.close()

    return redirect(url_for("volunteer"))

# ============================================================
# FOUNDER: CONFIRM A FOOD DELIVERY ASSIGNMENT
# ============================================================

@app.route(
    "/founder/food-delivery/<int:delivery_id>/assign",
    methods=["POST"]
)
def assign_food_delivery(delivery_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("volunteer"))

    cursor = connection.cursor(dictionary=True)

    try:
        founder_user_id = session["user_id"]

        # Verify founder role from the database.
        cursor.execute("""
            SELECT role
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (founder_user_id,))

        founder = cursor.fetchone()

        if not founder or str(
            founder.get("role") or ""
        ).strip().lower() != "founder":
            flash("Only the founder can assign deliveries.", "error")
            return redirect(url_for("volunteer"))

        # Assign only an accepted offer created by this founder.
        cursor.execute("""
            UPDATE food_deliveries
            SET status = 'assigned',
                assigned_at = CURRENT_TIMESTAMP
            WHERE id = %s
              AND founder_user_id = %s
              AND status = 'accepted'
        """, (delivery_id, founder_user_id))

        if cursor.rowcount != 1:
            connection.rollback()
            flash(
                "Assignment failed. The offer may not be accepted "
                "or may not belong to your account.",
                "error"
            )
            return redirect(url_for("volunteer"))

        cursor.execute("""
            INSERT INTO cb_notifications (user_id, title, message)
            SELECT volunteer_user_id,
                   'Food delivery assigned',
                   'The founder confirmed your food delivery assignment.'
            FROM food_deliveries
            WHERE id = %s
        """, (delivery_id,))

        connection.commit()
        flash("Food delivery assigned successfully.", "success")

    except Error as e:
        connection.rollback()
        print("Delivery assignment database error:", e)
        flash("Unable to assign the delivery.", "error")

    except Exception as e:
        connection.rollback()
        print("Delivery assignment error:", e)
        flash("Something went wrong during assignment.", "error")

    finally:
        cursor.close()

    return redirect(url_for("volunteer"))


# ============================================================
# VOLUNTEER: UPDATE DELIVERY PROGRESS
# ============================================================

@app.route(
    "/volunteer/food-delivery/<int:delivery_id>/status",
    methods=["POST"]
)
def update_food_delivery_status(delivery_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = db

    if connection is None:
        flash("Database connection failed.", "error")
        return redirect(url_for("volunteer"))

    cursor = connection.cursor(dictionary=True)

    try:
        volunteer_user_id = session["user_id"]
        new_status = request.form.get("status", "").strip().lower()

        if new_status not in ("in_progress", "delivered"):
            flash("Invalid delivery status.", "error")
            return redirect(url_for("volunteer"))

        # Allow only the assigned volunteer to update progress.
        if new_status == "in_progress":
            cursor.execute("""
                UPDATE food_deliveries
                SET status = 'in_progress',
                    started_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND volunteer_user_id = %s
                  AND status = 'assigned'
            """, (delivery_id, volunteer_user_id))

        else:
            cursor.execute("""
                UPDATE food_deliveries
                SET status = 'delivered',
                    delivered_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND volunteer_user_id = %s
                  AND status = 'in_progress'
            """, (delivery_id, volunteer_user_id))

        if cursor.rowcount != 1:
            connection.rollback()
            flash(
                "Status update failed. Check that the delivery "
                "is assigned to you and is at the correct stage.",
                "error"
            )
            return redirect(url_for("volunteer"))

        # Notify the founder.
        cursor.execute("""
            INSERT INTO cb_notifications (user_id, title, message)
            SELECT founder_user_id,
                   'Food delivery status updated',
                   %s
            FROM food_deliveries
            WHERE id = %s
        """, (
            "Delivery status changed to " + new_status + ".",
            delivery_id
        ))

        connection.commit()
        flash("Delivery status updated successfully.", "success")

    except Error as e:
        connection.rollback()
        print("Delivery status database error:", e)
        flash("Unable to update delivery status.", "error")

    except Exception as e:
        connection.rollback()
        print("Delivery status error:", e)
        flash("Something went wrong while updating delivery status.", "error")

    finally:
        cursor.close()

    return redirect(url_for("volunteer"))
@app.route("/test-upload")
def test_upload():
    return "Flask is working!"

# ============================================================
# RUN FLASK
# ============================================================


if __name__ == "__main__":

    print()
    print("========================================")
    print("       CHARITYBRIDGE FLASK SERVER")
    print("========================================")
    print("Website: http://127.0.0.1:5000")
    print("Database:", MYSQL_DATABASE)
    print("========================================")
    print()

   
    
    # Open CharityBridge automatically in Google Chrome
    def open_chrome():
        import os
        import subprocess

        chrome_paths = [
            os.path.expandvars(
                r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
            ),
            os.path.expandvars(
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe"
            ),
        ]

        for chrome_path in chrome_paths:
            if os.path.isfile(chrome_path):
                subprocess.Popen([
                    chrome_path,
                    "http://127.0.0.1:5000/"
                ])
                return

        webbrowser.open("http://127.0.0.1:5000/")
        print("Chrome was not found in the usual installation folders.")

    threading.Timer(2, open_chrome).start()


    app.run(
    host="0.0.0.0",
    port=5000,
    debug=True,
    use_reloader=False
)