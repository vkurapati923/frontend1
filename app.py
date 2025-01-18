from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from pdf2image import convert_from_path
import tempfile
from transformers import T5Tokenizer, T5ForConditionalGeneration
import openai
import json
from sentence_transformers import SentenceTransformer, util
import torch
from datetime import datetime

# Path to Poppler binaries
poppler_path = r"C:\poppler-24.08.0\Library\bin"
import pytesseract

# Specify the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Set OpenAI API key
openai.api_key = "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"

# Replace with your Hugging Face token if required
HF_AUTH_TOKEN = "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"

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3001"}})

# Global variables for models
tokenizer, t5_model, similarity_model = None, None, None

# Utility function to log messages with timestamps
def log(message):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

# Function to load models
def load_models():
    global tokenizer, t5_model, similarity_model
    try:
        # Load T5 model and tokenizer
        print("Loading T5 model...")
        tokenizer = T5Tokenizer.from_pretrained("doc2query/msmarco-t5-base-v1", use_auth_token=HF_AUTH_TOKEN)
        t5_model = T5ForConditionalGeneration.from_pretrained("doc2query/msmarco-t5-base-v1", use_auth_token=HF_AUTH_TOKEN)
        t5_model.to("cuda" if torch.cuda.is_available() else "cpu")  # Use GPU if available

        # Load SentenceTransformer
        print("Loading SentenceTransformer model...")
        similarity_model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda" if torch.cuda.is_available() else "cpu")
        print("Models loaded successfully!")
    except Exception as e:
        log(f"Error loading models: {e}")
        raise RuntimeError("Failed to load models. Ensure the model names are correct and dependencies are installed.")

# Function to generate a schema for a question
def build_question_schema(question, context):
    prompt = (
        f"Context: {context}\n"
        f"Question: {question}\n"
        "Generate the following JSON format:\n"
        "{\n"
        "  \"correct_answer\": \"[Correct Answer]\",\n"
        "  \"wrong_answers\": [\"Wrong Option 1\", \"Wrong Option 2\", \"Wrong Option 3\"],\n"
        "  \"hints\": [\"Hint 1\", \"Hint 2\"],\n"
        "  \"explanation\": \"[Provide a clear and concise explanation of the answer.]\"\n"
        "}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an educational assistant that provides JSON-formatted answers."},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(response["choices"][0]["message"]["content"])
    except Exception as e:
        log(f"Error generating schema: {e}")
        return {"error": str(e)}

# Function to generate questions from context
def generate_questions(context, num_questions=5, similarity_threshold=0.8):
    input_text = f"Generate questions for the following context: {context}"
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(t5_model.device)

    outputs = t5_model.generate(
        **inputs,
        max_length=50,
        num_return_sequences=num_questions * 2,
        num_beams=num_questions * 2,
        early_stopping=True
    )

    questions = [tokenizer.decode(o, skip_special_tokens=True) for o in outputs]
    embeddings = similarity_model.encode(questions, convert_to_tensor=True)

    # Deduplicate questions using semantic similarity
    final_questions = []
    for i, question in enumerate(questions):
        if not any(util.cos_sim(embeddings[i], embeddings[j]).item() >= similarity_threshold for j in range(len(final_questions))):
            final_questions.append(question)
            if len(final_questions) == num_questions:
                break

    return final_questions

# Flask route to confirm the app is running
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Trivia Generator Backend is Running!"}), 200

# Flask route to process a PDF and extract text
@app.route("/process-pdf", methods=["POST"])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    try:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name  # Get the path to the temporary file
            
        # Convert the temporary file using pdf2image
        images = convert_from_path(tmp_file_path, dpi=100, poppler_path=poppler_path)
        context = " ".join(pytesseract.image_to_string(img) for img in images).strip()

        # Check if any text was extracted
        if not context:
            return jsonify({"error": "No text extracted from the PDF."}), 400

        return jsonify({"status": "success", "context": context}), 200
    except Exception as e:
        log(f"Error processing PDF: {e}")
        return jsonify({"error": str(e)}), 500

# Flask route to generate questions
@app.route("/generate-questions", methods=["POST"])
def generate_questions_endpoint():
    data = request.json
    context = data.get("context", "").strip()

    if not context:
        return jsonify({"error": "Context is required to generate questions."}), 400

    try:
        questions = generate_questions(context, num_questions=5)
        schemas = [build_question_schema(question, context) for question in questions]

        return jsonify({"status": "success", "questions": schemas}), 200
    except Exception as e:
        log(f"Error generating questions: {e}")
        return jsonify({"error": str(e)}), 500

# Main block to load models and run the app
if __name__ == "__main__":
    load_models()  # Load models before starting the server
    app.run(debug=True)
