import os
import requests
from flask import Flask, request, render_template
import easyocr
import cv2
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

reader = easyocr.Reader(['en'])
API_KEY = "AIzaSyA2xHPbot0o6tVuueVpE6yOAlvBZNAyth8"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            image = cv2.imread(filepath)
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # edges = cv2.Canny(gray_image, 100, 200)
            result = reader.readtext(gray_image)
            
            extracted_text = []
            for (bbox, text, confidence) in result:
                # ...existing code...
                if confidence > 0.6:
                    text = text.replace(" ", "")
                    text = text.replace("1", "i")
                    extracted_text.append(re.sub("[^a-zA-Z0-9\s]","", text))

            query = "+".join(extracted_text).lower()

            # Debug prints
            print(f"Query: {query}")
            print(f"API Key: {API_KEY}")

            books_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}"
            print(books_api_url)
            response = requests.get(books_api_url)
            print(response.status_code)
            if response.status_code == 200:
                books_data = response.json()
                books_info = []
                for item in books_data["items"]:
                    book_title = item.get("volumeInfo", {}).get("title", "Unknown Title")
                    book_authors = item.get("volumeInfo", {}).get("authors", ["Unknown Author"])
                    book_thumbnail = item.get("volumeInfo", {}).get("imageLinks", ["Image not found"]).get("smallThumbnail", "")
                    print(book_thumbnail)
                    books_info.append({"title": book_title, "authors": ", ".join(book_authors), "thumbnail": book_thumbnail})
            else:
                books_info = [{"title": "Error fetching data", "authors": ""}]
            
            return render_template("index.html", extracted_text=query, uploaded_image=filepath, books_info=books_info)

    return render_template("index.html", extracted_text=None)

@app.route("/books", methods=["GET"])
def a():
    title = request.args.get('title')
    title = title.replace(" ", "+").lower()
    title = re.sub("[^a-zA-Z0-9\s]","", title)
    print(title)
    books_api_url = f"https://www.googleapis.com/books/v1/volumes?q={title}&key={API_KEY}"
    print(books_api_url)
    response = requests.get(books_api_url)
    print(response)
    book_details = response.json()
    print(book_details)
    main_book = book_details["items"][0]
    return render_template("book.html", book_details=main_book, books=book_details["items"])

if __name__ == "__main__":
    app.run(debug=True)
