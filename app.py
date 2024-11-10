from flask import (
    Flask, 
    jsonify, 
    request, 
    render_template, 
    send_file, 
    abort, 
    send_from_directory, 
    current_app,
    g
)

from prompt_templates import (
    SYSTEM_INSTRUCTION,
    prompt_template_four, 
    prompt_template_one, 
    prompt_template_three, 
    prompt_template_two, 
    email_draft_prompt, 
    email_modification_prompt, 
    bluesheet_finalization_prompt, 
    follow_up_prompt, 
    response_handling_prompt
)

from typing import Iterable
import io
import time
import pandas as pd
import json
import os  # Handle file paths and directory operations
from os import path  # Check if files or directories exist, get file paths
import re  # Use regular expressions for text processing
from texts import SHAPE, SOUTH_WEST, MISCO
from queue import Queue
import threading
import requests
import vertexai

from openpyxl import Workbook
from openpyxl.styles import Font
from docx import Document as Docxdocument
from docx.shared import Pt
from spire.doc import *
from spire.doc.common import *

from vertexai.preview.generative_models import (
    GenerationResponse,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part, 
    ChatSession
)
from dotenv import load_dotenv


load_dotenv()
# Access the variables
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
MODEL_NAME = os.getenv("MODEL_NAME")
BASE_URL = os.getenv("CLOUD_RUN_SERVICE_URL", "http://127.0.0.1:5000")
BLOCK_LEVEL = HarmBlockThreshold.BLOCK_ONLY_HIGH



app = Flask(__name__)

vertexai.init(project=PROJECT_ID, location=LOCATION)


# Configuration settings 
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

TEMP_DOWNLOADS_FOLDER = 'downloads'
os.makedirs(TEMP_DOWNLOADS_FOLDER, exist_ok=True)
app.config['TEMP_DOWNLOADS_FOLDER'] = TEMP_DOWNLOADS_FOLDER

SYSTEM_DOCS = "app_documents"
os.makedirs(SYSTEM_DOCS, exist_ok=True)
app.config["SYSTEM_DOCS"] = SYSTEM_DOCS

# Global variables
print_queue = Queue()
input_request_queue = Queue()
input_response_queue = Queue()
chat_thread = None

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/chat', methods=['GET'])
def chat():
    # Initialize chat when this route is accessed
    initialize_chat()
    return render_template('chat.html')

def initialize_chat():
    """Initialize chat components and start background processes"""
    global chat_thread
    if not hasattr(g, 'chat_initialized'):
        if chat_thread is None:
            chat_thread = threading.Thread(target=start_chat_session)
            chat_thread.start()
        g.chat_initialized = True

def start_chat_session():
    """Main chat session logic"""
    
    time.sleep(1)  # Allow time for server start
    
    
    model = GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION
    )

    session = model.start_chat()
    handle_step_one(session)
    handle_step_two(session)
    handle_step_three(session)
    handle_step_four(session)
    handle_step_five(session)
    handle_step_six(session)
    the_doc = os.listdir(app.config['UPLOAD_FOLDER'])[0]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], the_doc)
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error removing file: {e}")
        
        


@app.route('/upload', methods=['POST'])
def upload_file():
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400
    
    # Save the file to the server
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    
    file.save(file_path)    
    
    print(file_path)
    # For example, return a part of the document as JSON
    response_data = {
        "filename": file.filename,
        "content_preview": "Success"  
    }
    
    return jsonify(response_data), 200
    
# Endpoint to list new files in the downloads folder
@app.route('/check-new-files', methods=['GET'])
def check_new_files():
    try:
        files = os.listdir(app.config['TEMP_DOWNLOADS_FOLDER'])
        return jsonify(files=files), 200
    except Exception as e:
        print(f"Error checking new files: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    try:
        downloads = os.path.join(current_app.root_path, app.config['TEMP_DOWNLOADS_FOLDER'])
        
        # Log the full path for debugging
        file_path = os.path.join(downloads, filename)
        print(f"Attempting to download: {file_path}")

        # Check if the file exists
        if os.path.isfile(file_path):
            return send_from_directory(downloads, filename, as_attachment=True)
        else:
            # If the file does not exist, return a 404 error
            abort(404, description="File not found")
    except Exception as e:
        print(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/remove/<filename>', methods=['DELETE'])
def remove_file(filename):
    try:
        file_path = os.path.join(app.config['TEMP_DOWNLOADS_FOLDER'], filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            return jsonify({"message": "File deleted successfully"}), 200
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/message', methods=['POST'])
def message_handler():
    action = request.json.get('action')

    if action == "print":
        # Queue a message for the client
        message = request.json.get('message')
        print_queue.put(message)
        return jsonify({"status": "Message queued for client"}), 200

    elif action == "input_request":
        # Queue an input request
        input_request_queue.put("Input requested")
        return jsonify({"status": "Input request sent to client"}), 200

    elif action == "input_response":
        # Store client input in response queue
        response = request.json.get('response')
        if response is not None:
            input_response_queue.put(response)
            return jsonify({"status": "Input received from client"}), 200
        return jsonify({"error": "No response provided"}), 400

    elif action == "fetch":
        # Send queued messages and input requests to client
        messages = []
        while not print_queue.empty():
            messages.append(print_queue.get())

        input_prompt = None
        if not input_request_queue.empty():
            input_prompt = input_request_queue.get()

        return jsonify({"messages": messages, "input_prompt": input_prompt}), 200

    return jsonify({"error": "Invalid action"}), 400

# Function to send a message to the client

def custom_print(message):
    requests.post(f"{BASE_URL}/message", json={"action": "print", "message": message})

# Function to request client input, waits for a response
def custom_input():
    requests.post(f"{BASE_URL}/message", json={"action": "input_request"})

    # Wait for the client to respond
    while True:
        if not input_response_queue.empty():
            return input_response_queue.get()
        time.sleep(1)  # Poll every second

def generate(
    prompt: list,
    max_output_tokens: int = 2048,
    temperature: int = 2,
    top_p: float = 0.4,
    stream: bool = False,
    session = None,
) -> GenerationResponse | Iterable[GenerationResponse]:
    """
    Function to generate response using Gemini 1.5 Pro

    Args:
        prompt:
            List of prompt parts
        max_output_tokens:
            Max Output tokens
        temperature:
            Temperature for the model
        top_p
            Top-p for the model
        stream:
            Stream results?

    Returns:
        Model response """
    while True:
        try:
            responses = session.send_message(
                prompt,
                generation_config={
                    "max_output_tokens": max_output_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: BLOCK_LEVEL,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: BLOCK_LEVEL,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: BLOCK_LEVEL,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: BLOCK_LEVEL,
                },
                stream=stream,
            )
            break
        except Exception as e:
            print(f"An error occurred retrying in 2 seconds: {e}")
            time.sleep(2)

    return responses


def is_valid_json(response_text):
    """
    Check if response_text is valid JSON.
    
    Strips any JSON code block delimiters (e.g., ```json) and 
    then attempts to parse it to confirm validity.
    """
    # Remove JSON code block delimiters if they exist
    json_text = re.sub(r'```json|```', '', response_text).strip()

    try:
        # Try loading the text as JSON
        json.loads(json_text)
        return True
    except ValueError:
        # If parsing fails, it's not valid JSON
        return False
def clean_html(response_text):
    html = re.sub(r'```html|```', '', response_text).strip()
    return html

def save_to_excel(json_data, folder=None):
    """Save JSON data to Excel with bold headers using openpyxl."""
    # Clean up JSON data if it contains markdown formatting
    json_text = re.sub(r'```json|```', '', json_data).strip()
    json_data = json.loads(json_text)

    # Create a new workbook and get the document name
    wb = Workbook()
    document_name = json_data.get("document_name", "Bluesheet Draft.xlsx")
    
    # Remove the default sheet created by openpyxl
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    # Process each worksheet in the JSON data
    for sheet_name, rows in json_data.items():
        if sheet_name == "document_name":
            continue  # Skip the document name key
        
        ws = wb.create_sheet(title=sheet_name)

        # Check if rows contain data
        if rows:
            # Use the first row's keys as headers
            headers = rows[0].keys()
            ws.append(list(headers))
            
            # Apply bold font to headers
            for cell in ws[1]:  # First row (headers)
                cell.font = Font(bold=True)
            
            # Append each row's values to the worksheet
            for row_data in rows:
                ws.append(list(row_data.values()))
        else:
            print(f"Warning: No data found for sheet '{sheet_name}'.")

    # Ensure the TEMP_DOWNLOADS_FOLDER is set in the config
    folder = app.config.get('TEMP_DOWNLOADS_FOLDER')
    if not folder:
        raise ValueError("TEMP_DOWNLOADS_FOLDER is not configured in app.config.")
    
    # Ensure the folder exists
    os.makedirs(folder, exist_ok=True)
    save_path = os.path.join(folder, document_name)
    
    # Save the workbook
    wb.save(save_path)
    print(f"Document saved as {save_path}")
    

    

def json_to_docx(json_string, folder):
    # Parse JSON string into a Python dictionary
    json_text = re.sub(r'```json|```', '', json_string).strip()
    data = json.loads(json_text)
    
    # Retrieve filename from the first dictionary
    file_name = data[0].get("fileName", "output.docx")
    
    # Initialize a Word document
    document = Docxdocument()
    
    # Iterate through JSON data (skip the first dictionary as it only contains the filename)
    for item in data[1:]:
        content_type = item.get("type")
        text = item.get("text", "")
        font_size = item.get("fontSize", 12)
        level = item.get("level", 1)  # For headings, this defines heading level

        if content_type == "heading":
            # Add a heading with the specified level
            heading = document.add_heading(text, level=level)
            # Adjust font size of heading if specified
            for run in heading.runs:
                run.font.size = Pt(font_size)
        
        elif content_type == "paragraph":
            # Add a paragraph with the specified font size
            paragraph = document.add_paragraph(text)
            # Set the font size for each run in the paragraph
            for run in paragraph.runs:
                run.font.size = Pt(font_size)
                
    # Build the full path for saving the file
    save_path = os.path.join(app.config['TEMP_DOWNLOADS_FOLDER'], file_name)
    
    # Save the document with the specified filename in the uploads folder
    document.save(save_path)
    print(f"Document saved as {save_path}")
    


def word_to_pdf(file_path, folder):
    # Create a Document object
    document = Document()
    # Load a Word DOCX file
    document.LoadFromFile(file_path)

    # Create a ToPdfParameterList object
    parameters = ToPdfParameterList()

    # Embed all used fonts in Word into PDF
    parameters.IsEmbeddedAllFonts = True

    #Save the file to a PDF file
    if file_path.endswith('.docx'):
        document.SaveToFile(f"{folder}/{file_path.replace('.docx', '.pdf')}", parameters)
    elif file_path.endswith('.doc'):
        document.SaveToFile(f"{folder}/{file_path.replace('.doc', '.pdf')}", parameters)
    document.Close()

        
def csv_to_txt(csv_file_path, folder):
    # Derive TXT file path based on CSV file path
    txt_file_path = f"{folder}/{os.path.splitext(csv_file_path)[0]}.txt"
    
    with open(csv_file_path, 'r') as csv_file:
        lines = csv_file.readlines()
        
        # Write to the TXT file
        with open(txt_file_path, 'w') as txt_file:
            for line in lines:
                # # Strip trailing commas, replace with a single space if the line is otherwise empty
                # stripped_line = line.rstrip(',\n')
                
                # # Only write non-empty lines
                # if stripped_line:
                #     # Replace remaining commas with tabs to format as columns
                txt_file.write(
                    line
                )
    return txt_file_path


# Document loading function
# Load the document (Word, PDF, or Excel)
def load_document(file_path, folder=None):
    file_extension = file_path.split('.')[-1].lower()
    mime_type = None
    if file_extension == "pdf":
        mime_type = "application/pdf"
    elif file_extension == "csv":
        file_path = csv_to_txt(file_path, folder)
        mime_type = "text/plain"
    elif file_extension == "txt":
        mime_type = "text/plain"
    elif file_extension in ["doc", "docx"]:
        word_to_pdf(file_path, folder)
        file_path = f"{folder}/{file_path.replace('.docx', '.pdf')}"
        mime_type = "application/pdf"
    else:
        print("Unsupported file type. Please provide a PDF, or TXT document.") 
    # Load the file
    with open(file_path, "rb") as fp:
        document = Part.from_data(data=fp.read(), mime_type=mime_type)
    return document

def handle_step_one(session):
    stage = 0
    
    while True:
        first_message = custom_input()
        rfp_doc = os.listdir(app.config['UPLOAD_FOLDER'])[0]
        rfp_doc = os.path.join(UPLOAD_FOLDER, rfp_doc)
        if stage == 0: 
            custom_print("Hello! I'm here to help build your bluesheet. What is the name of this project?")
            project_name = custom_input()
            custom_print("Please upload the rfp document before proceeding")
            stage +=1
        if rfp_doc == None:
            # custom_print("Please upload the rfp document...")
            time.sleep(2)
            print("Waiting for RFP document upload...")
            app.logger.info("Waiting for RFP document upload...")
            raise Exception("RFP document not uploaded")
            continue
        
        rfp_document = load_document(rfp_doc)
        
        template_file_path = os.path.join(SYSTEM_DOCS, "Blue_Sheet_Bid_Document_Template.pdf")
        
        bluesheet_bid_doc_template = load_document(template_file_path)
        
        custom_print("Processing the RFP document...")
        prompt_template_one.format(project_name=project_name)
        # Request JSON content for the document
        response_text = generate(prompt=[rfp_document, bluesheet_bid_doc_template, prompt_template_one], session=session).text
        
        custom_print("Generating Bluesheet Basic RFP Bid Analysis Document...")
     
        if is_valid_json(response_text):
            try:
                # Save or pass the JSON data to the json_to_docx function
                print(response_text)
                json_to_docx(response_text, TEMP_DOWNLOADS_FOLDER)
                custom_print("Document successfuly analyzed")
                break
            except Exception as e: 
                print(f"An error occurred: {e}")
        
        print("Error occurred while generating the JSON structure. Trying again...")
        custom_print("An error occurred")
        custom_print("Regenerating Bluesheet Basic RFP Bid Analysis Document...")
        responses = generate(prompt=[
            """
            The document generation failed. Please try again, ensuring no errors in JSON structure.
            """
        ], session=session)
        response_text = responses.text
        if is_valid_json(response_text):
            try:
                
                json_to_docx(response_text, TEMP_DOWNLOADS_FOLDER)
                custom_print("Document successfuly analyzed")
                break
                
            except Exception as e: 
                print(f"An error occurred: {e}")
                custom_print("An error ocurred. Try again later")
                return False
    # Handle user feedback and modifications
    while True:
        custom_print("Would you like to make any modifications or corrections to the document? If yes, please specify the modifications.")
        user_response = custom_input().strip()
        # Request JSON content for the document
        response_text = generate(prompt=[
            f"""
            <NOTE> This stage is iterative depending on the user's feedback. </NOTE>
            <INSTRUCTIONS>
            Apply user feedback to the previously sent JSON document and send new document with changes. That is if user requests modifications.
            <ACTION>
            If the user requests modifications:
                * apply the user feedback to the JSON document and return the JSON that'll be formatted into a DOCX document.
            If the user does not request modifications:
                * Reply with a message indicating that no modifications were requested and proceeding to the next step. (Not in JSON format)
                * Do not mention anything about JSON in your response.
            <USER_RESPONSE>{user_response}</USER_RESPONSE>
            """
        ],  session=session).text
        if is_valid_json(response_text):
            try:
                json_to_docx(response_text, TEMP_DOWNLOADS_FOLDER)
                custom_print("Document updated successfully.")
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                continue
        else: 
            custom_print("No modifications were requested. Proceeding to the next step.")
            break


def handle_step_two(session):
    custom_print("Would you like me to proceed with equipment identification for MISCO analysis?")
    response = custom_input()
    misco_document = MISCO
    prompt_template_two.format(response=response)

    prompt = [misco_document, prompt_template_two]
    try:
        responses = generate(prompt=prompt, session=session)
    except Exception as e:
        raise Exception(f"Error generating MISCO document: {e}")
    response_text = responses.text
    custom_print(clean_html(response_text))

    # Ask for anything else
    while True:
        custom_print("Anything else you'd like me to do? or shall we proceed to the next step?")
        user_response = custom_input().strip().lower()
        response_text = generate(prompt=[
            f"""
            <NOTE> This stage is iterative depending on the user's feedback. </NOTE>
            <INSTRUCTIONS>
            Perform the next action based on the user's response. 
            If user wants to proceed to the next step, reply with a message (in plain text and not with html format) indicating that you will proceed to next step. Start with: "END STAGE..." 
            <ACTION>
            Respond to the user's feedback and proceed to the next step if the user does not request any further actions or questions.
            If user asks to generate a document, reply with: "Can't generate that document now."
            <USER_RESPONSE>{user_response}</USER_RESPONSE>
            """
        ], session=session).text
        if response_text.startswith("END"):
            custom_print("Proceeding to the next step.")
            break
        else:
            custom_print(clean_html(response_text))
            continue





def handle_step_three(session):
    custom_print("""
Would you like to identify synergy opportunities in this RFP for UFT’s platform companies,
Shape (representing related companies in Northern California),
and Southwest Valve? I will review the RFP based on their products and categories.
""")
    response = custom_input()
    shape_document = SHAPE
    southwest_valve_document = SOUTH_WEST

    prompt_template_three.format(response=response)
    prompt = [shape_document, southwest_valve_document, prompt_template_three]
    responses = generate(prompt=prompt, session=session)
    response_text = responses.text
    custom_print(clean_html(response_text))
        # Ask for anything else
    while True:
        custom_print("Anything else you'd like me to do? or shall we proceed to the next step?")
        user_response = custom_input().strip().lower()
        response_text = generate(prompt=[
            f"""
            <NOTE> This stage is iterative depending on the user's feedback. </NOTE>
            <INSTRUCTIONS>
            Perform the next action based on the user's response. 
            If user wants to proceed to the next step, reply with a message (in plain text and not with html format) indicating that you will proceed to next step. Start with: "END STAGE..." 
            <ACTION>
            Respond to the user's feedback and proceed to the next step if the user does not request any further actions or questions.
            If user asks to generate a document, reply with: "Can't generate that document now."
            <USER_RESPONSE>{user_response}</USER_RESPONSE>
            """
        ], session=session).text
        if response_text.startswith("END"):
            custom_print("Proceeding to the next step.")
            break
        else:
            custom_print(clean_html(response_text))
            continue



def handle_step_four(session):
    template_file_path = os.path.join(SYSTEM_DOCS, "Blue Sheet Template 2024.txt")
    bluesheet_template = load_document(template_file_path)
    
    custom_print("I will go ahead to generate a draft of the bluesheet in Excel format.")
   
    prompt1 = [bluesheet_template, prompt_template_four]
    responses = generate(prompt=prompt1, session=session)
    response_text = responses.text

    # Check if response is JSON and attempt to save it
    status = False
    if is_valid_json(response_text):
        
        try:
            custom_print("Generating draft...")
            save_to_excel(response_text, TEMP_DOWNLOADS_FOLDER)
            custom_print("Generated excel draft!")
            status = True
        except Exception as e:
            print(f"Error saving bluesheet: {e}")

    # Loop for handling user feedback and modifications
    while True:
        if status:
            # Success case - ask for user review
            responses = generate(prompt=[
                """
                <STATUS>"Success"</STATUS>
                <ACTION>Ask user to review draft to see if there are modifications
                <MESSAGE FOR USER> "I have generateted bluesheet Excel with detailed product specifications, criteria, and requirements for each category, as well as the contact information for MISCO, Shape, and Southwest Valves opportunities. Please review this draft and let me know if there are any changes or additions."
                """
            ], session=session)
        else:
            # Failure case - regenerate JSON without errors
            responses = generate(prompt=[
                """
                <STATUS>"Fail"</STATUS>
                <ACTION>Regenerate JSON output, following the correct schema for the Excel document generation.
                """
            ], session=session)

        response_text = responses.text
        if is_valid_json(response_text):
            
            try:
                save_to_excel(response_text, TEMP_DOWNLOADS_FOLDER)
                custom_print("Generated excel draft.")
                status = True
                continue
            except Exception as e:
                print(f"Error saving bluesheet: {e}")
                continue
        else:
            custom_print(clean_html(response_text))
            custom_print("Please provide your modifications: ")
            response = custom_input()
            responses = generate(prompt=[
                f"""
                <INSTRUCTIONS>
                Apply user feedback to the JSON draft, updating or adding rows to the specified worksheet (MISCO, Shape, or Southwest Valve) in the schema.
                <USER_RESPONSE>{response}</USER_RESPONSE>
                """
            ], session=session)
            response_text = responses.text
            status = False
            if is_valid_json(response_text):
                
                try:
                    save_to_excel(response_text, TEMP_DOWNLOADS_FOLDER)
                    custom_print("Generated excel draft.")
                    status = True
                except Exception as e:
                    print(f"Error saving bluesheet: {e}")
                continue
            else:
                custom_print(clean_html(response_text))
                break

def handle_step_five(session):
    # Ask the user if they want to draft an email
    custom_print("Would you like to draft an email to UFT portfolio company leads? (yes/no): ")
    user_response = custom_input().strip().lower()

    if user_response == "yes":
        # Generate initial email draft
        email_draft = generate(prompt=[email_draft_prompt], session=session)
        custom_print(clean_html(email_draft.text))  # Display the initial draft

        # Iteratively ask for modifications until the user is satisfied
        while True:
            custom_print("Would you like any modifications to the email draft? (yes/no): ")
            user_response = custom_input().strip().lower()
            if user_response == "no":
                break  # Exit loop if no modifications needed

            # Gather modification details and generate revised draft
            custom_print("Please specify the modifications you'd like to make: ")
            modification_details = custom_input()
            modified_email_draft = generate(prompt=[email_modification_prompt.format(modification_details=modification_details)], session=session)
            custom_print(clean_html(modified_email_draft.text))  # Display the revised draft

        # Finalized draft message
        custom_print("The email draft is finalized and ready for sending.")
        
    elif user_response == "no":
        # If no email draft needed, generate the final bluesheet JSON and save as Excel
        bluesheet_json_response = generate(prompt=[bluesheet_finalization_prompt], session=session).text
        try:
            save_to_excel(bluesheet_json_response, TEMP_DOWNLOADS_FOLDER)
            custom_print("The final bluesheet Excel file has been successfully generated.")
        except Exception as e:
            print(f"Error generating the final bluesheet: {e}")
    
    else:
        # Handle invalid input
        custom_print("Invalid response. Please respond with 'yes' to draft an email or 'no' to proceed with bluesheet download.")




def handle_step_six(session):
    while True:
        # Initial prompt to ask if the user would like to do anything else
        # Send the prompt to the model to capture the user's intent (yes/no response)
        follow_up_response = generate(prompt=[follow_up_prompt], session=session)
        response_text = follow_up_response.text
        if not is_valid_json(response_text):
            custom_print(clean_html(response_text))  # Display model's follow-up prompt to user
            user_response = custom_input().strip().lower()
            response_handling_prompt.format(user_response=user_response)

            final_follow_up = generate(prompt=[response_handling_prompt], session=session)
            custom_print(clean_html(final_follow_up.text))  # Display model's final follow-up or conclusion message
            if final_follow_up.text.startswith("END"):
                return 
        else:
            custom_print("Can't generate that document now")
            continue


        
        

def run_server():
    """Server initialization function"""
    if BASE_URL == "http://127.0.0.1:5000":
        app.run(debug=True, use_reloader=False)
    else:
        port = 8080
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start only the Flask server initially
    
    run_server()
