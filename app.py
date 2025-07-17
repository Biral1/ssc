from flask import Flask, request, jsonify, render_template_string, make_response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Route 1: Home page with input form
@app.route("/", methods=["GET", "POST"])
def home():
    html_output = ""
    scraped_url = ""
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(url, headers=headers, timeout=10)
                res.raise_for_status()
                html_output = res.text[:5000]  # Limit output
                scraped_url = url
            except Exception as e:
                html_output = f"Error: {e}"
        else:
            html_output = "No URL provided."

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simple HTML Scraper</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
        <div class="container mx-auto px-4 py-8">
            <div class="max-w-4xl mx-auto">
                <div class="text-center mb-8">
                    <h1 class="text-4xl font-bold text-gray-800 mb-2">Simple HTML Scraper</h1>
                    <p class="text-gray-600">Enter a URL to scrape and view its HTML content</p>
                </div>
                <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                    <form method="POST" class="space-y-4">
                        <div>
                            <label for="url" class="block text-sm font-medium text-gray-700 mb-2">Website URL</label>
                            <div class="flex space-x-2">
                                <input 
                                    type="url" 
                                    name="url" 
                                    id="url"
                                    placeholder="https://example.com" 
                                    class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                                    required 
                                />
                                <button 
                                    type="submit" 
                                    class="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all"
                                >
                                    <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                                    </svg>
                                    Scrape
                                </button>
                            </div>
                        </div>
                    </form>
                </div>

                {% if html_output %}
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-xl font-semibold text-gray-800">Scraped Content</h3>
                        {% if scraped_url and not html_output.startswith('Error:') %}
                        <button 
                            onclick="downloadHTML()" 
                            class="px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-all"
                        >
                            <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            Download HTML
                        </button>
                        {% endif %}
                    </div>

                    {% if html_output.startswith('Error:') %}
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div class="flex">
                            <svg class="w-5 h-5 text-red-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                            </svg>
                            <p class="text-red-700">{{ html_output }}</p>
                        </div>
                    </div>
                    {% else %}
                    <div class="bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto">
                        <pre class="text-sm text-gray-800 whitespace-pre-wrap">{{ html_output }}</pre>
                    </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>

        <script>
            function downloadHTML() {
                const url = '{{ scraped_url }}';
                if (url) {
                    window.open('/download?url=' + encodeURIComponent(url), '_blank');
                }
            }
        </script>
    </body>
    </html>
    """, html_output=html_output, scraped_url=scraped_url)


# Route 2: API endpoint to get filtered HTML (body only, no scripts/images)
@app.route("/scrape")
def scrape():
    url = request.args.get("url")
    return_json = request.args.get("json", "false").lower() == "true"

    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        html = res.text
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if return_json:
        try:
            return jsonify(process_exam_data(html))
        except Exception as e:
            return jsonify({"error": f"Failed to process exam data: {str(e)}"}), 500
    else:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body")
        if not body:
            return jsonify({"error": "No body element found"}), 404

        for tag in body.find_all(["script", "img"]):
            tag.decompose()
        return str(body)


# Route 3: Download full HTML
@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        response = make_response(res.text)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = 'attachment; filename="scraped_content.html"'
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route 4: Ping route
@app.route("/ping")
def ping():
    return "pong", 200


# Exam Data Extraction Logic
def process_exam_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    main_info = soup.find("div", class_="main-info-pnl")
    if not main_info:
        raise ValueError("Main info panel not found")

    def get_text(label):
        cell = main_info.find("td", string=label)
        return cell.find_next_sibling("td").text.strip() if cell else "N/A"

    candidate_name = get_text("Candidate Name")
    roll_number = get_text("Roll Number")
    exam_date = get_text("Exam Date")
    exam_time = get_text("Exam Time")

    results = []
    sections = soup.find_all("div", class_="section-cntnr")
    for section in sections:
        label_elem = section.find("div", class_="section-lbl")
        section_lbl = label_elem.find_all("span")[-1].text.strip() if label_elem else "Unnamed Section"
        section_lbl = ''.join(filter(lambda x: not x.isdigit(), section_lbl)).strip()

        questions = section.find_all("div", class_="question-pnl")
        total_questions = len(questions)
        answered = right = wrong = 0

        for question in questions:
            menu_tbl = question.find("table", class_="menu-tbl")
            if not menu_tbl:
                continue
            status_cell = menu_tbl.find("td", string="Status :")
            if status_cell:
                status = status_cell.find_next_sibling("td").text.strip()
                if status == "Answered":
                    answered += 1
                    chosen_cell = menu_tbl.find("td", string="Chosen Option :")
                    chosen_option = chosen_cell.find_next_sibling("td").text.strip() if chosen_cell else ""
                    correct_cell = question.find("td", class_="rightAns")
                    if correct_cell:
                        correct_option = correct_cell.text.split(".")[0].strip()
                        if chosen_option == correct_option:
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
