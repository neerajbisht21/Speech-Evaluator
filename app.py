from flask import Flask, request, jsonify, render_template

from scoring import score_transcript

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/score", methods=["POST"])
def score():
    data = request.get_json()
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "No text provided"}), 400
    try:
        result = score_transcript(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
