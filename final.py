from typing import Iterable
import io
import time

import json

import os 
from os import path  
import re  
from texts import SHAPE, SOUTH_WEST, MISCO, SYSTEM_INSTRUCTION
from prompt_templates import (
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

import vertexai
from vertexai.preview.generative_models import (
    GenerationResponse,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part, 
    ChatSession
)


# Configuration
PROJECT_ID = "my-bluesheet-project-440016"  # Replace with your project ID
LOCATION = "us-central1"  # Replace with your location
MODEL_NAME = "gemini-1.5-pro-002"  # Replace with model name
BLOCK_LEVEL = HarmBlockThreshold.BLOCK_ONLY_HIGH
vertexai.init(project=PROJECT_ID, location=LOCATION)


def csv_to_txt(csv_file_path):
    # Derive TXT file path based on CSV file path
    txt_file_path = os.path.splitext(csv_file_path)[0] + '.txt'
    
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


# Load the document (Word, PDF, or Excel)
def load_document(file_path):
    
    file_extension = file_path.split('.')[-1].lower()
    
    mime_type = None
    if file_extension == "pdf":
        mime_type = "application/pdf"
    elif file_extension in ["csv", "txt"]:
        file_path = csv_to_txt(file_path)
        mime_type = "text/plain"
        
    else:
        print("Unsupported file type. Please provide a PDF, or TXT document.")
    
    # Load the file
    with open(file_path, "rb") as fp:
        document = Part.from_data(data=fp.read(), mime_type=mime_type)
    
    return document

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


def save_to_excel(json_data):
    """Save JSON data to Excel using openpyxl."""


    # Create a new workbook
    wb = Workbook()
    document_name = json_data.get("document_name", "Bluesheet Draft.xlsx")
    
    # Process each worksheet in the JSON data
    for sheet_name, rows in json_data.items():
        if sheet_name == "document_name":
            continue  # Skip the document name key
        ws = wb.create_sheet(title=sheet_name)
        
        # Assume first row in the first list entry has the headers
        headers = rows[0].keys()
        ws.append(list(headers))
        
        # Add each row from the JSON data
        for row_data in rows:
            ws.append(list(row_data.values()))
    
    # Save the workbook with the specified document name
    wb.save(f'{document_name}')



def json_to_docx(json_string: str):
    # Parse JSON string into a Python dictionary
    json_text = re.sub(r'```json|```', '', json_string).strip()
    data = json.loads(json_text)
    
    # Retrieve filename from the first dictionary
    file_name = data[0].get("fileName", "output.docx")
    
    # Initialize a Word document
    document = Document()
    
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
                
    # Save the document with the specified filename
    document.save(file_name)
    print(f"Document saved as {file_name}")



def generate(
    prompt: list,
    max_output_tokens: int = 2048,
    temperature: int = 2,
    top_p: float = 0.4,
    stream: bool = False,
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

def handle_step_one():
    print("Hello! I'm here to help build your bluesheet. What is the name of this project? Please upload the RFP document: ")
    project_name = input()
    rfp_document_path = input("What is the rfp document path: ")
    rfp_document = load_document(rfp_document_path)
    blue_sheet_template_path = input("What is the blue sheet template path: ")
    bluesheet_bid_doc_template = load_document(blue_sheet_template_path)
    
    prompt_template_one.format(project_name=project_name)
    # Request JSON content for the document
    responses1 = generate(prompt=[rfp_document, bluesheet_bid_doc_template, "Here is the rfp_document and bluesheet_bid_doc_template"])
    prompt = [prompt_template_one]
    print("Generating document structure in JSON format...")
    
    # Generate JSON response from prompt
    responses = generate(prompt=prompt)
    response_text = responses.text
    
    if is_valid_json(response_text):
        try:
            # Save or pass the JSON data to the json_to_docx function
            print(response_text)
            json_to_docx(response_text)
            
            
        except Exception as e: 
            print(f"An error occurred: {e}")
            raise
    else:
        print("Error occurred while generating the JSON structure. Trying again...")
        print(response_text)
        responses = generate(prompt=[
            """
            The document generation failed. Please try again, ensuring no errors in JSON structure.
            """
        ])
        response_text = responses.text
        if is_valid_json(response_text):
            try:
                
                json_to_docx(response_text)
                
            except Exception as e: 
                print(f"An error occurred: {e}")

    

def handle_step_two():
    print("Would you like me to proceed with equipment identification for MISCO analysis?")
    response = input()
    misco_document = MISCO
    prompt_template_two.format(response=response)

    prompt = [misco_document, prompt_template_two]
    responses = generate(prompt=prompt)
    response_text = responses.text
    print(response_text)



def handle_step_three():
    print("""
Would you like to identify synergy opportunities in this RFP for UFT’s platform companies,
Shape (representing related companies in Northern California),
and Southwest Valve? I will review the RFP based on their products and categories.
""")
    response = input()
    shape_document = SHAPE
    southwest_valve_document = SOUTH_WEST

    prompt_template_three.format(response=response)
    prompt = [shape_document, southwest_valve_document, prompt_template_three]
    responses = generate(prompt=prompt)
    response_text = responses.text
    print(response_text)


def handle_step_four():
    bluesheet_template = load_document("chat-agent\Blue Sheet Template 2024.csv")
    print("I will go ahead to generate a draft of the bluesheet in Excel format.")
   
    # Initial prompt for generating JSON for the bluesheet draft
    # Request initial JSON for generating the bluesheet draft
    prompt1 = [bluesheet_template, prompt_template_four]
    responses = generate(prompt=prompt1)
    response_text = responses.text

    # Check if response is JSON and attempt to save it
    status = False
    if is_valid_json(response_text):
        bluesheet_data = json.loads(re.sub(r'```json|```', '', response_text).strip())
        try:
            save_to_excel(bluesheet_data)
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
                <MESSAGE FOR USER> "I have generated a JSON draft for the bluesheet, ready to be converted to Excel format with detailed product specifications, criteria, and requirements for each category, as well as the contact information for MISCO, Shape, and Southwest Valves opportunities. Please review this draft and let me know if there are any changes or additions."
                """
            ])
        else:
            # Failure case - regenerate JSON without errors
            responses = generate(prompt=[
                """
                <STATUS>"Fail"</STATUS>
                <ACTION>Regenerate JSON output, following the correct schema for the Excel document generation.
                """
            ])

        response_text = responses.text
        if is_valid_json(response_text):
            bluesheet_data = json.loads(re.sub(r'```json|```', '', response_text).strip())
            try:
                save_to_excel(bluesheet_data)
                status = True
                continue
            except Exception as e:
                print(f"Error saving bluesheet: {e}")
                continue
        else:
            print(response_text)
            response = input("Please provide your modifications: ")
            responses = generate(prompt=[
                f"""
                <INSTRUCTIONS>
                Apply user feedback to the JSON draft, updating or adding rows to the specified worksheet (MISCO, Shape, or Southwest Valve) in the schema.
                <USER_RESPONSE>{response}</USER_RESPONSE>
                """
            ])
            response_text = responses.text
            status = False
            if is_valid_json(response_text):
                bluesheet_data = json.loads(re.sub(r'```json|```', '', response_text).strip())
                try:
                    save_to_excel(bluesheet_data)
                    status = True
                except Exception as e:
                    print(f"Error saving bluesheet: {e}")
                continue
            else:
                print(response_text)
                break

def handle_step_five():
    # Initial prompt to ask the user if they would like an email draft
    user_response = input("Would you like to draft an email to UFT portfolio company leads? (yes/no): ").strip().lower()

    # Prepare the appropriate prompt based on the user's response
    if user_response == "yes":
        # Prompt template for drafting the initial email
        email_draft_prompt.format(user_response=user_response)

        # Generate the email draft based on the user input
        email_draft = generate(prompt=[email_draft_prompt])
        email_text = email_draft.text
        print("Draft email generated:")
        print(email_text)  # Display email draft to user

        # Ask the user if they would like any modifications to the draft
        user_response = input("Would you like any modifications to the email draft? (yes/no): ").strip().lower()

        while user_response == "yes":
            # Get specific modifications from the user
            modification_details = input("Please specify the modifications you'd like to make: ")

            # Prompt template for modifications to the email draft
            email_modification_prompt.format(modification_details=modification_details)

            # Generate the modified email draft
            modified_email_draft = generate(prompt=[email_modification_prompt])
            modified_email_text = modified_email_draft.text
            print("Modified draft email:")
            print(modified_email_text)  # Display modified email draft to user

            # Ask if further modifications are needed
            user_response = input("Would you like any further modifications to the email draft? (yes/no): ").strip().lower()

        # Finalize the email draft if no more modifications are needed
        print("The email draft is finalized and ready for sending.")
        return modified_email_text if user_response == "yes" else email_text  # Return the finalized email draft for sending or saving

    elif user_response == "no":
        # If the user does not want an email draft, prepare the final bluesheet in JSON format
        bluesheet_finalization_prompt.format(user_response=user_response)

        # Generate the final bluesheet JSON
        bluesheet_json_response = generate(prompt=[bluesheet_finalization_prompt])
        bluesheet_json_text = re.sub(r'```json|```', '', bluesheet_json_response.text).strip()

        # Save the JSON output as an Excel file
        try:
            bluesheet_data = json.loads(bluesheet_json_text)
            # Save Excel file using openpyxl based on the JSON schema
            book_name = bluesheet_data["excel_document_name"]
            workbook = openpyxl.Workbook()
            for company in ["MISCO", "Shape", "Southwest Valve"]:
                if company in bluesheet_data:
                    worksheet = workbook.create_sheet(company)
                    # Write data to worksheet
                    for row_data in bluesheet_data[company]:
                        worksheet.append([row_data[col] for col in row_data])
            workbook.save(f"{book_name}.xlsx")
            print("The final bluesheet Excel file has been successfully generated and saved.")
        except Exception as e:
            print(f"Error generating the final bluesheet: {e}")
    else:
        # Handle unexpected responses
        print("Invalid response. Please respond with 'yes' to draft an email or 'no' to proceed with bluesheet download.")


def handle_step_six():
    while True:
        # Initial prompt to ask if the user would like to do anything else
        

        # Send the prompt to the model to capture the user's intent (yes/no response)
        follow_up_response = generate(prompt=[follow_up_prompt])
        response_text = follow_up_response.text
        print(response_text)  # Display model's follow-up prompt to user

        # Capture the user's actual response to the follow-up prompt
        user_response = input().strip().lower()

        # Pass the user's response back to the model for interpretation
        response_handling_prompt.format(user_response=user_response)

        # Generate the model's handling of the user's response
        final_follow_up = generate(prompt=[response_handling_prompt])
        print(final_follow_up.text)  # Display model's final follow-up or conclusion message

        if final_follow_up.text.startswith("END"):
            break




while True:
    print("Welcome to the Bluesheet Generator! Let's get started.(yes/no)")
    if input().strip().lower() == "no":
        print("Thank you for using the Bluesheet Generator. Goodbye!")
        break
    model = GenerativeModel(
    MODEL_NAME,
    system_instruction=SYSTEM_INSTRUCTION
    )

    session = model.start_chat()
    handle_step_one()
    handle_step_two()
    handle_step_three()
    handle_step_four()
    handle_step_five()
    handle_step_six()
