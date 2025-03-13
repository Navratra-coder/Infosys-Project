# 🛡️ Aadhaar Fraud Detection System: Prevent fraud and ensure authenticity with our advanced Aadhaar verification system.

👋 Welcome to the Aadhaar Fraud Detection System, a project designed to prevent fraud and ensure authenticity through our advanced Aadhaar verification system. This repository details the integration of machine learning models, OCR, and a Flask backend to create a comprehensive fraud detection pipeline.

## 🚀 The Mission: Prevent fraud and ensure authenticity.

🎯 Our goal is to provide a reliable system that safeguards digital identity by combining cutting-edge technologies to detect and prevent Aadhaar fraud.

## ✨ What Makes Our Aadhaar Verification System Shine?

* 🔍 **Intelligent Detection:** Leveraging YOLOv11 for classification and detection, ensuring accuracy in identifying Aadhaar documents and extracting relevant data.
* 👁️ **OCR Precision:** Utilizing EasyOCR for accurate text extraction from cropped document sections.
* 🌐 **Seamless Integration:** Building a Flask-powered backend to create a smooth, efficient, and scalable API.
* 🔒 **User Security:** Implementing robust user authentication with advanced password hashing algorithms to protect user credentials.
* 📧 **Email Verification:** Utilizing Flask-Mail to generate and send login emails, enhancing security and user experience.
* 🎨 **User-Centric Vision:** Designing an intuitive UI for user authentication, easy file uploads, dynamic threshold adjustment, result visualization, and report downloads.
* 📊 **Database & Scoring Logic:** Implementing robust scoring logic and database integration with SQLAlchemy for efficient data management.

## 🛠️ Tech Stack: Our Arsenal

* 🐍 **Python:** Core programming language.
* 🔥 **Flask:** Backend framework.
* 🧠 **YOLOv11:** Classification and detection models.
* 📜 **EasyOCR:** Optical Character Recognition.
* 📊 **SQLAlchemy:** Database management.
* ✨ **HTML/CSS/JavaScript:** Frontend development.

## 🗺️ Project Workflow

1.  **Input Data:**
    * 📥 Users upload a ZIP folder containing document images.
    * 📄 An Excel file with existing user records (name, UID, address).
      
2.  **Classification Model (YOLOv11):**
    * 🖼️ Each image is processed to determine if it's an Aadhaar card.
      
3.  **Detection Model (YOLOv11):**
    * ✂️ Relevant sections (name, UID, address) are identified and cropped.
    
4.  **OCR Model (EasyOCR):**
    * 📝 Text is extracted from cropped sections.
      
5.  **Comparison and Scoring:**
    * ⚖️ Extracted data is compared with Excel records.
    * 💯 Match percentages are generated based on business rules.
      
6.  **Output:**
    * 📊 A report with match scores for each user is generated in the form of updated excel file and analytics. 

## 📂 **Project Structure**

- aadhaar-fraud-detection/
    - data/
        - users.db
    - instance/
    - static/
    - templates/
        - apology.html
        - index.html
        - login.html
        - register.html
        - results.html
    - uploads/
    - app.py
    - Helpers.py
    - requirements.txt


## ⚙️ Backend Architecture with Flask

###   1. Set Up Flask

```bash
pip install flask
```

###  2. API Endpoints
* 🔑 /login: Handles user login.
* 🚪 /logout: Handles user logout.
* ✍️ /register: Handles user registration.
* 🏠 /: Serves the index page and handles file uploads.
* 📈 /results: Displays the results table and analytical graphs.
* ⬇️ /download_excel: Allows users to download the Excel file after results are updated.
* 🎨 Designing the User Interface

##  UI Features

### Authentication:
* 🔑 Login and registration functionalities.
* 🔒 Secure Password Handling: User passwords are encrypted using advanced hashing algorithm for enhanced security.
* 📧 Email Verification: Login emails are generated and sent to the user using Flask-Mail.

### Upload Section:
📁 ZIP and Excel file upload fields.

### Matching threshold adjustment slider:
🎚️ Allows users to set the threshold for matching scores.

### Process Button:
▶️ Triggers the backend pipeline.

### Results Display:

* 📊 Tabular display of match scores.
* 📈 Analytical graphs.
* ✔️❌ **Dynamic Remarks:** "Data verified" / "Data mismatch" remarks displayed based on the adjusted threshold.

### Download:
💾 Option to download the updated Excel file.

## Frontend Tools
* ✨ HTML, CSS, JavaScript.
* 🔗 Flask's render_template() for HTML integration.

## 🧠 Integrating Models
```Python

from ultralytics import YOLOv11
from easyocr import Reader

classifier = YOLO("classification_model.pt")
detector = YOLO("detection_model.pt")
reader = Reader(['en'])
```

## 🔗 Connecting Backend and Frontend
* 💬 Used HTML forms for communication.
* 🔑 Implemented user authentication and session management.
* 🔄 Dynamically fetched the results and updated the UI.
* 📥 Handled file downloads.
* 🎚️ Implemented the matching threshold slider functionality, updating results and remarks dynamically.
* 🔒 Implemented secure password handling using advanced hashing algorithms.
* 📧 Integrateed Flask-Mail to generate and send login emails.

## 🚀 Project Deployment
☁️ Deploying by setting up a server, installing dependencies, configuring the database, and running our application.

## 🤝 Contribute
🙌 Contributions are welcome!

## 📜 License
MIT license

## 📧 Connect
https://github.com/Navratra-coder
