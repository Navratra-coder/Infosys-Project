from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
    send_file,
    flash,
)
import os
import time
import traceback
import zipfile
import tempfile
import pandas as pd
from ultralytics import YOLO
import cv2
from easyocr import Reader
import io
from PIL import Image
from fuzzywuzzy import fuzz
import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, DateTime
from flask_mail import Mail, Message
from Helpers import apology, login_required, debug
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from dotenv import load_dotenv

load_dotenv(dotenv_path="../project.env")

folderpath = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
app.config["ALLOWED_EXTENSIONS"] = {"zip", "xlsx"}
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{folderpath}/data/users.db"
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = os.getenv("my_email")  # My email
app.config["MAIL_PASSWORD"] = os.getenv("my_email_app_password")  # App password
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("my_email")
app.config["SECRET_KEY"] = os.getenv("secret_key")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQLAlchemy(app)
mail = Mail(app)

# Load models (Initialize only once)
classifier = YOLO(
    "../Classification_Model/code_files/Classification/runs/classify/train/weights/best.pt"
)
detector = YOLO(
    "../Classification_Model/code_files/Detection/runs/detect/train7/weights/best.pt"
)
reader = Reader(["en"])


# Database models
class User(db.Model):
    __tablename__ = "User"
    user_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    extracted_data = db.relationship("ExtractedData", backref="User", lazy=True)

    @debug
    def send_login_email(self):
        msg = Message("Login to Aadhaar Detection System", recipients=[self.email])
        msg.body = "Welcome! You have logged in to the Aadhaar detection system."
        mail.send(msg)


class ExtractedData(db.Model):
    __tablename__ = "ExtractedData"
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey("User.email"), nullable=False)
    name = db.Column(db.String(100))
    uid = db.Column(db.String(20))
    address = db.Column(db.Text)


class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255))
    name_score = db.Column(db.Integer)
    uid_score = db.Column(db.Integer)
    address_score = db.Column(db.Integer)
    score = db.Column(db.Integer)
    remarks = db.Column(db.Text)
    upload_date = db.Column(
        DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
    )
    session_id = db.Column(db.String(36))


@debug
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


@debug
def process_image(image_data, reader=reader):
    try:
        image = Image.open(io.BytesIO(image_data))
        image.save("temp_image.jpg")
        img_cv2 = cv2.imread("temp_image.jpg")
        extracted_data = {}
        prediction = classifier.predict("temp_image.jpg")
        if prediction[0].names[prediction[0].probs.top1] == "aadhar":
            remarks = "Aadhaar Image"
            results = detector("temp_image.jpg")
            for result in results[0].boxes.data.tolist():
                x1, y1, x2, y2, confidence, class_id = map(int, result[:6])
                field_class = detector.names[class_id]
                cropped_roi = img_cv2[int(y1) : int(y2), int(x1) : int(x2)]
                gray_roi = cv2.cvtColor(cropped_roi, cv2.COLOR_BGR2GRAY)
                text = reader.readtext(gray_roi, detail=0)
                extracted_data[field_class] = " ".join(text)
        else:
            remarks = "Non-Aadhaar Image"
        return extracted_data, remarks
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, "Image Processing Error"


@debug
def name_match(input_name, extracted_name):
    """
    Evaluates whether the input name matches the extracted name,
    based on the specified rules, and outputs a score accordingly
    """

    def clean_name(text):
        return "".join(e for e in str(text) if e.isalpha()).lower()

    name_score = fuzz.ratio(clean_name(extracted_name), clean_name(input_name))

    if name_score < 100:
        extracted_parts = extracted_name.split()
        excel_parts = input_name.split()
        if len(extracted_parts) > 1 and len(excel_parts) > 1:
            # Allow abbreviation of first name
            if fuzz.ratio(extracted_parts[0][0], excel_parts[0][0]) > 90:
                name_score = 90

    if name_score < 100:
        extracted_parts = extracted_name.split()
        excel_parts = input_name.split()
        if len(extracted_parts) == 2 and len(excel_parts) > 2:
            if (
                extracted_parts[0] == excel_parts[0]
                and extracted_parts[1] == excel_parts[2]
            ):
                name_score = 90

    if name_score < 100:
        if any(part in extracted_name for part in input_name.split()):
            name_score = 90

    if name_score < 100:
        if sorted(extracted_name.split()) == sorted(input_name.split()):
            name_score = 90

    if name_score < 100:
        for part in input_name.split():
            if len(part) == 1 and part.lower() == extracted_name[0].lower():
                name_score = 90
                break

    return name_score


@debug
def uid_match(input_uid, extracted_uid):
    """
    Outputs the score of how much input UIDs match
    """

    def clean_uid(uid):
        return "".join(filter(str.isdigit, str(uid)))

    return fuzz.ratio(clean_uid(extracted_uid), clean_uid(input_uid))


@debug
def address_match(extracted_address, row):
    """
    Compares extracted address with given components
    returns score and full address created from given components
    """

    @debug
    def normalize_address(address):
        address = address.lower()
        address = re.sub(r"\s+", " ", address)  # Remove extra spaces
        address = re.sub(
            r"(marg|lane|township|block|street)", "", address
        )  # Remove common terms
        return address

    address_score = 0
    address_components = [
        "House Flat Number",
        "Floor Number",
        "Premise Building Name",
        "Street Road Name",
        "Landmark",
        "Town",
        "City",
        "State",
    ]
    full_address = " ".join((str(row.get(col, "")) for col in address_components))

    cleaned_extracted_address = normalize_address(extracted_address)
    cleaned_full_address = normalize_address(full_address)

    address_score = fuzz.partial_ratio(cleaned_extracted_address, cleaned_full_address)

    extracted_pincode = (
        digits[-1] if (digits := re.findall(r"\d+", extracted_address)) else ""
    )
    if extracted_pincode == row["PINCODE"]:
        address_score = 100

    return address_score, full_address


@debug
def overall_match(name_score, uid_score, address_score):
    """
    Evaluates the overall match based on name, UID, and address matches.
    """
    return sum((name_score, uid_score, address_score)) / 3


@debug
def compare_and_score(
    extracted_name,
    extracted_uid,
    extracted_address,
    original_df,
    filename,
    image_remarks,
    overall_threshold,
) -> dict[str]:
    try:
        match_found = False

        for index, row in original_df.iterrows():
            if row["SrNo"] != filename.split(".")[0]:
                continue
            match_found = True
            input_name = row["Name"]
            input_uid = str(row["UID"])

            name_score = name_match(input_name, extracted_name) if extracted_name else 0
            uid_score = uid_match(input_uid, extracted_uid) if extracted_uid else 0
            address_score, full_address = (
                address_match(extracted_address, row)
                if extracted_address
                else (0, None)
            )

            overall_score = overall_match(name_score, uid_score, address_score)
            if overall_score >= overall_threshold:
                verification_remarks = "Data Verified"
            else:
                verification_remarks = "Data Mismatch"

            remarks = f"{image_remarks}, {verification_remarks}"
            matching_serial_number = row["SrNo"]
            break

        if not match_found:
            full_address = "N/A"
            name_score = address_score = uid_score = overall_score = "N/A"
            matching_serial_number = "N/A"
            remarks = "No data found in file"

        # Store results in the database using SQLAlchemy
        result = Result(
            filename=filename,
            name_score=name_score,
            uid_score=uid_score,
            address_score=address_score,
            score=overall_score,
            remarks=remarks,
            session_id=session["session_id"],
        )
        db.session.add(result)
        db.session.commit()

        return {
            "SrNo": matching_serial_number,  # merge key
            "Extracted Name": extracted_name,
            "Extracted UID": extracted_uid,
            "Full Address": full_address,
            "Extracted Address": extracted_address,
            "Name Match Score": name_score,
            "UID Match Score": uid_score,
            "Address Match Score": address_score,
            "Overall Score": overall_score,
            "Remarks": remarks,
        }

    except Exception as e:
        print(f"Error comparing and scoring: {e}")
        print(*traceback.format_exception(e))


@app.route("/login", methods=["GET", "POST"])
@debug
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Ensure username was submitted
        if not email:
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        user = User.query.filter_by(email=email).first()
        if user is not None and check_password_hash(user.password, password):
            user.send_login_email()
            session["user_id"] = user.user_id
            return jsonify({"message": "Login successful!"})
        return jsonify({"message": "Invalid credentials"}), 401

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@debug
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
@debug
def register():
    """Register user"""
    if request.method == "POST":
        # Get submission
        username = request.form.get("username")
        if not username:
            return apology("MISSING USERNAME")
        email = request.form.get("email")
        if not email:
            return apology("MISSING EMAIL ID")
        password = request.form.get("password")
        if not password:
            return apology("MISSING PASSWORD")
        password2 = request.form.get("confirmation")

        if password != password2:
            return apology("PASSWORDS DO'NT MATCH")

        # Store it into db
        try:
            db.session.execute(
                text(
                    "INSERT INTO User (username, email, password) VALUES (:username, :email, :password)"
                ),
                {
                    "username": username,
                    "email": email,
                    "password": generate_password_hash(password),
                },
            )
            db.session.commit()  # Commit the transaction
        except IntegrityError:
            db.session.rollback()  # Rollback on error
            return apology("EMAIL ALREADY TAKEN")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/", methods=["GET", "POST"])
@debug
# @login_required
def index():
    overall_threshold = 80  # Default threshold
    if request.method == "POST":
        if "zipfile" not in request.files or "excelfile" not in request.files:
            return jsonify({"error": "Both files are required."}), 400
        zip_file = request.files["zipfile"]
        excel_file = request.files["excelfile"]
        overall_threshold = int(
            request.form.get("threshold", 80)
        )  # Get the threshold from the form
        if zip_file.filename == "" or excel_file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        if (
            zip_file
            and allowed_file(zip_file.filename)
            and excel_file
            and allowed_file(excel_file.filename)
        ):
            zip_filename = os.path.join(app.config["UPLOAD_FOLDER"], zip_file.filename)
            excel_filename = os.path.join(
                app.config["UPLOAD_FOLDER"], excel_file.filename
            )
            zip_file.save(zip_filename)
            excel_file.save(excel_filename)
            try:
                session_id = str(uuid.uuid4())  # Generate a unique session ID
                session["session_id"] = session_id  # Store session ID in session
                with zipfile.ZipFile(zip_filename, "r") as zip_ref:
                    original_df = pd.read_excel(excel_filename)
                    results_list = []

                    for file_info in zip_ref.infolist():
                        if file_info.filename.lower().endswith(
                            (".png", ".jpg", ".jpeg")
                        ):
                            with zip_ref.open(file_info) as file:
                                image_data = file.read()
                                extracted_data, remarks = process_image(image_data)
                                extracted_name = extracted_data.get("name", "")
                                extracted_uid = extracted_data.get("uid", "")
                                extracted_address = extracted_data.get("address", "")
                                result_dict = compare_and_score(
                                    extracted_name,
                                    extracted_uid,
                                    extracted_address,
                                    original_df,
                                    file_info.filename,
                                    remarks,
                                    overall_threshold, 
                                )
                            results_list.append(result_dict)
                    session["results_list"]=results_list
                    results_df = pd.DataFrame(results_list)
                    common_fields = {*original_df.columns} & {*results_df.columns}
                    updated_df = pd.merge(
                        original_df.drop(
                            columns=[
                                field for field in common_fields if field != "SrNo"
                            ]
                        ),
                        results_df,
                        on="SrNo",
                        how="left",
                    )

                    temp_excel_filename = os.path.join(
                        tempfile.gettempdir(), f"updated_{uuid.uuid4()}.xlsx"
                    )
                    updated_df.to_excel(temp_excel_filename, index=False)

                    session["download_file"] = temp_excel_filename
                return redirect(
                    url_for("show_results")
                )  # Redirect to the results page after processing
            except Exception as e:
                return jsonify({"error": f"Error processing files: {e}"}), 500
        else:
            return jsonify({"error": "Invalid file type."}), 400
    return render_template("index.html", overall_threshold=overall_threshold)


@app.route("/results", methods=["GET", "POST"])
@debug
def show_results():
    session_id = session.get("session_id")  # Retrieve session ID
    results_list = session.get("results_list")
    results = Result.query.filter(
        Result.session_id == session_id  # Filter by session ID
    ).all()
    return render_template("results.html", results=results, results_list=results_list)


# Route for downloading the Excel file
@app.route("/download_excel")
@login_required
def download_excel():
    temp_excel_filename = session.get("download_file")
    if temp_excel_filename and os.path.exists(temp_excel_filename):
        return send_file(
            temp_excel_filename,
            as_attachment=True,
            download_name="updated_results.xlsx",  # The name of the downloaded file.
        )
    else:
        flash("Excel file not found.", "error")
        return redirect(url_for("results"))  # or your result page.