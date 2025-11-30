1. create & activate venv
python -m venv venv
venv\Scripts\activate   (Windows)  or  source venv/bin/activate

2. install
pip install -r requirements.txt

3. download nltk punkt
python -c "import nltk; nltk.download('punkt')"

4. create rubrics.csv
python convert_rubric.py

5. run app
python app.py

6. open http://127.0.0.1:5000 in browser
# Speech-Evaluator
