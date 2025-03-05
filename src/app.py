from flask import Flask, render_template, request, jsonify
from trivia_bot import TriviaBot
from loguru import logger
import threading
import queue

app = Flask(__name__)
bot = TriviaBot()
question_queue = queue.Queue()
answer_queue = queue.Queue()
bot_thread = None
is_listening = False

def bot_worker():
    """Background worker to process questions and get answers."""
    global is_listening
    while True:
        try:
            question = question_queue.get(timeout=1)  # Wait for questions
            if question == "STOP":
                break
            
            logger.info(f"Processing question: {question}")
            answer = bot.get_answer(question)
            
            if answer:
                answer_queue.put({
                    "success": True,
                    "answer": answer,
                    "question": question
                })
            else:
                answer_queue.put({
                    "success": False,
                    "answer": "I couldn't find an answer to that question.",
                    "question": question
                })
                
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error in bot worker: {e}")
            answer_queue.put({
                "success": False,
                "answer": f"An error occurred: {str(e)}",
                "question": "Error"
            })

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question submissions."""
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({
            "success": False,
            "error": "Please provide a question"
        }), 400
    
    # Start bot thread if not running
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        bot_thread = threading.Thread(target=bot_worker, daemon=True)
        bot_thread.start()
    
    # Submit question
    question_queue.put(question)
    
    # Wait for answer (with timeout)
    try:
        result = answer_queue.get(timeout=30)
        return jsonify(result)
    except queue.Empty:
        return jsonify({
            "success": False,
            "error": "Request timed out"
        }), 408

@app.route('/status')
def get_status():
    """Get bot status."""
    return jsonify({
        "status": "running",
        "is_listening": is_listening
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) 