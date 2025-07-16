from flask import Flask, jsonify, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form['url']
        return extract(url)
    
    # HTML form for user input
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>URL Input</title>
        </head>
        <body>
            <h1>Enter URL to Extract Exam Data</h1>
            <form action="/" method="post">
                <label for="url">URL:</label>
                <input type="text" id="url" name="url" required>
                <button type="submit">Submit</button>
            </form>
        </body>
        </html>
    ''')

@app.route('/<path:url>', methods=['GET'])
def extract(url):
    # Prepend "http://" if the URL does not start with "http://" or "https://"
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    html_content = download_html(url)
    if html_content is None:
        return jsonify({"error": "Failed to retrieve the page"}), 500
    
    results = process_exam_data(html_content)
    return jsonify(results)

def download_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return None

def process_exam_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Main info panel
    main_info = soup.find("div", class_="main-info-pnl")
    candidate_name = main_info.find("td", string="Candidate Name").find_next_sibling("td").text.strip() if main_info else "unknown_candidate"
    
    # Extract additional information
    roll_number = main_info.find("td", string="Roll Number").find_next_sibling("td").text.strip() if main_info else "unknown_roll_number"
    exam_date = main_info.find("td", string="Exam Date").find_next_sibling("td").text.strip() if main_info else "unknown_exam_date"
    exam_time = main_info.find("td", string="Exam Time").find_next_sibling("td").text.strip() if main_info else "unknown_exam_time"
    
    # List of results
    results = []
    
    # All sections
    sections = soup.find_all("div", class_="section-cntnr")
    for section in sections:
        section_lbl = section.find("div", class_="section-lbl").find_all("span")[-1].text.strip()
        section_lbl = ''.join(filter(lambda x: not x.isdigit(), section_lbl)).strip()
        
        questions = section.find_all("div", class_="question-pnl")
        total_questions = len(questions)
        
        answered = 0
        right = 0
        wrong = 0
        
        for question in questions:
            menu_tbl = question.find("table", class_="menu-tbl")
            status_row = menu_tbl.find("td", string="Status :")
            if status_row:
                status = status_row.find_next_sibling("td").text.strip()
                if status == "Answered":
                    answered += 1
                    
                    chosen_row = menu_tbl.find("td", string="Chosen Option :")
                    chosen_option = chosen_row.find_next_sibling("td").text.strip()
                    
                    right_ans = question.find("td", class_="rightAns")
                    if right_ans:
                        right_option = right_ans.text.split(".")[0].strip()
                        if chosen_option == right_option:
                            right += 1
                        else:
                            wrong += 1
        
                unattempted = total_questions - answered
        
        total_marks = right * 3 - wrong
        
        results.append({
            "Section Label": section_lbl,
            "Total Questions": total_questions,
            "Answered": answered,
            "Unattempted": unattempted,
            "Right": right,
            "Wrong": wrong,
            "Total Marks": total_marks
        })
    
    return {
        "Candidate Name": candidate_name,
        "Roll Number": roll_number,
        "Exam Date": exam_date,
        "Exam Time": exam_time,
        "Results": results
    }

if __name__ == '__main__':
    app.run(debug=True)
