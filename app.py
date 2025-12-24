import os, io, json
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF

from utils import clean_text, extract_text_from_pdf
from ranking_model import get_semantic_score, analyze_skill_gap, get_semantic_score_simple
from role_data import JOB_ROLES
from company_data import COMPANY_VALUES

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def generate_detailed_pdf(candidate_name, role_matches, company_matches):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(0, 15, "Candidate Assessment Report", ln=True, align='C')
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 10, f"Candidate Name: {candidate_name}", ln=True, align='C')
    pdf.ln(5)

    # 1. Company Fit
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "Cultural Compatibility Match", ln=True)
    pdf.set_font("helvetica", '', 11)
    for comp in company_matches:
        pdf.cell(0, 8, f"- {comp['company']}: {comp['fit_score']}% Match", ln=True)
    pdf.ln(5)

    # 2. Technical Analysis
    for match in role_matches:
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, f" ROLE: {match['role']} ({match['score']}%)", 1, 1, 'L', True)
        
        # Decision Checklist
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(0, 7, " Screening Checklist:", ln=True)
        checks = [
            ("Technical Score >= 65%", match['score'] >= 65),
            ("Skill Alignment Found", match['score'] >= 45),
            ("MNC Baseline Met", match['score'] >= 35)
        ]
        for text, ok in checks:
            pdf.set_font("zapfdingbats", size=10)
            mark = "4" if ok else "6" # 4 is tick, 6 is cross
            pdf.cell(8, 7, mark, 0, 0)
            pdf.set_font("helvetica", size=10)
            pdf.cell(0, 7, text, 0, 1)

        # Status & Recommendations
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(0, 7, "Detailed Assessment:", ln=True)
        pdf.set_font("helvetica", '', 10)
        
        description = f"Status: {match['status']}. "
        if match['gaps']:
            description += f"Key Skill Gaps to address: {', '.join(match['gaps'])}."
        else:
            description += "All core competencies found."
        
        pdf.multi_cell(0, 6, description)
        pdf.ln(5)

    # Fix TypeError: Encode to latin-1 bytes
    return pdf.output(dest='S').encode('latin-1')

@app.route("/", methods=["GET", "POST"])
def index():
    final_reports = []
    if request.method == "POST":
        files = request.files.getlist("resumes")
        for file in files:
            if not file.filename: continue
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            cleaned = clean_text(extract_text_from_pdf(filepath))

            # Role Screening
            role_matches = []
            for role_name in JOB_ROLES.keys():
                score = get_semantic_score(role_name, cleaned)
                if score >= 0.35:
                    role_matches.append({
                        "role": role_name,
                        "score": round(float(score) * 100, 2),
                        "status": "Accepted" if score >= 0.65 else "Waitlist",
                        "gaps": analyze_skill_gap(role_name, cleaned)
                    })
            
            # Company Matching
            company_fits = []
            for company, info in COMPANY_VALUES.items():
                val_text = f"{info['description']} {' '.join(info['values'])}"
                fit_score = get_semantic_score_simple(val_text, cleaned)
                company_fits.append({"company": company, "fit_score": round(float(fit_score) * 100, 2)})

            role_matches.sort(key=lambda x: x["score"], reverse=True)
            company_fits.sort(key=lambda x: x["fit_score"], reverse=True)
            final_reports.append({"name": filename, "matches": role_matches, "company_matches": company_fits})

    return render_template("index.html", reports=final_reports)

@app.route("/download", methods=["POST"])
def download():
    # Safeguard against NoneType errors
    name = request.form.get("name", "Report")
    matches_raw = request.form.get("matches", "[]")
    companies_raw = request.form.get("companies", "[]")
    
    matches = json.loads(matches_raw)
    companies = json.loads(companies_raw)
    
    pdf_bytes = generate_detailed_pdf(name, matches, companies)
    buf = io.BytesIO(pdf_bytes)
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=f"{name}_Report.pdf")

if __name__ == "__main__":
    app.run(debug=True)