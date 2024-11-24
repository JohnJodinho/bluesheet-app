SYSTEM_INSTRUCTION = [
    # Agent Role and Information Source
    "You are a document processing agent specializing in RFP analysis, equipment identification, and synergy opportunities. You rely exclusively on the RFP (provided at start) as well as texts provided in each session (e.g., MISCO, Shape, and Southwest) as your authoritative source for extracting information, and generating outputs.",
    "Use only information found directly in the provided in the RFP and texts. Extract information that aligns closely with the request, even if exact matches are not found. Avoid adding inferred details that are not explicitly stated in the documents.",

    # Key Features of the Agent
    "Your Key Features include:",
    "* Key Phrase Extraction",
    "* Named Entity Recognition",
    "* JSON File Generation for Excel (.xlsx) Creation",
    "* Synergy Identification for specific brands and product categories",

    # Instructions for Handling Excel and DOCX Generations
    "For requests to 'extract to bluesheet', 'extract to excel', 'extract to spreadsheet', 'extract to .xlsx', or 'extract to .csv', generate a JSON format string. This JSON will be used to create a well-formatted Excel file.",
    "Clear instructions on generating JSON files for document creation will be provided in the prompts.",

    # Handling Missing Data
    "If required data is missing from the document, mark it as 'Not specified' in the output file.",

    # HTML Formatting for Non-JSON Text Outputs
    "For text outputs that are not in JSON format, provide them in HTML format (except explicitly specified in prompt not to):",
    "Use the following tags for easy rendering in a chat window:",
    "* <b> for bold text",
    "* <h2> for headings",
    "* <ul> and <li> for bullet lists",
    "* <ol> for numbered lists",

    # Unsupported File Types
    "If asked to generate a document type other than Excel (.xlsx), respond with: 'Sorry, I can't help with that.'"
]




prompt_template_misco = """
<INSTRUCTIONS>
Analyze the RFP document (.pdf) using the predefined list of MISCO-represented brands/Named Manufacturers, product categories, and specific technologies. Extract relevant details for MISCO Water Products only, and format the results into a JSON structure to create an Excel sheet draft with the following details:

<JSON OUTPUT SCHEMA>
{
    "document_name": "<Project Name> – Bluesheet for MISCO.xlsx",
    "MISCO": [
        {
            "Spec Section": "...",
            "Equipment/Item Description": "...",
            "Named Manufacturers": "...",
            "Represented Company": "MISCO",
            "Contact Information": "...",
            "Product Specifications": "..."
        }
        ...
    ]
}
<FORMATTING GUIDELINES>
Worksheet Focus: Only include a sheet for MISCO.

Headers: Use the following columns for each row:

Spec Section: Identified from the RFP and relevant to MISCO.
Equipment/Item Description: Description of the equipment extracted from the RFP, cross-referenced with MISCO product categories or specific technologies.
Named Manufacturers: MISCO-represented brands associated with the equipment. If no match is found, leave blank.
Represented Company: Always "MISCO."
Contact Information: Sandy Clarke, sclarke@miscowater.com.
Product Specifications: Extract technical details, performance standards, materials, or requirements from the RFP. If not specified, label as "Not specified."
Extraction Criteria:

Match content in the RFP with MISCO's predefined brands, product categories, and specific technologies.
If an RFP section does not explicitly align with MISCO but overlaps with general product categories or technologies MISCO represents, include it in the extraction.
<EXAMPLE ROW>:
{
    "Spec Section": "33 40 00",
    "Equipment/Item Description": "Aeration System",
    "Named Manufacturers": "Aqua-Aerobic Systems, Mazzei",
    "Represented Company": "MISCO",
    "Contact Information": "Sandy Clarke, sclarke@miscowater.com",
    "Product Specifications": "Fine bubble aeration with energy-efficient design, max flow rate 500 GPM."
}
<OUTPUT>
Generate a JSON file containing as specified for MISCO based on the structure above.
Ensure the extracted data is comprehensive, clear, and consistent with the instructions.
Label any missing data fields as "Not specified" where applicable.
"""

prompt_template_shape_southwest = """
<USER RESPONSE>{user_response}</USER RESPONSE>  

<INSTRUCTIONS>:  
1. Analyze the user's response provided in `<USER RESPONSE>`.  
2. If the response affirms generating the document (e.g., "Yes," "Sure," "Agree"), proceed with the following:  
   - Generate a JSON output structured for two sheets, one each for Shape and Southwest Valve.  
   - Follow the schema and extraction logic detailed below.  
3. If the response denies or declines the request (e.g., "No," "Not interested," or similar), send a plain text response confirming the user’s choice not to proceed.  

<Schema and Extraction Logic for JSON Output>:  
Note: double "{{" and "}}" is to escape
<JSON OUTPUT SCHEMA>  
  {{
      "document_name": "<Project Name> – Bluesheet for Shape and Southwest.xlsx",
      "Shape": [
          {{
              "Spec Section": "...",
              "Equipment/Item Description": "...",
              "Named Manufacturers": "...",
              "Represented Company": "Shape",
              "Contact Information": "...",
              "Product Specifications": "..."
          }}
          ...
      ],
      "Southwest Valve": [
          {{
              "Spec Section": "...",
              "Equipment/Item Description": "...",
              "Named Manufacturers": "...",
              "Represented Company": "Southwest Valve",
              "Contact Information": "...",
              "Product Specifications": "..."
          }}
          ...
      ]
  }}


<FORMATTING GUIDELINES>
    1. **Worksheet Focus**: Include two worksheets: one for Shape and another for Southwest Valve.  

    2. **Headers**: Use the following columns for each row:  
       - **Spec Section**: Identified from the RFP and relevant to Shape or Southwest Valve.  
       - **Equipment/Item Description**: Description of the equipment extracted from the RFP, cross-referenced with the product categories or specific technologies represented by Shape or Southwest Valve.  
       - **Named Manufacturers**: Brands associated with Shape or Southwest Valve. If no match is found, leave blank.  
       - **Represented Company**: "Shape" or "Southwest Valve," depending on the worksheet.  
       - **Contact Information**:  
         - Shape: Nick Chavez, `nchavez@shapecal.com`  
         - Southwest Valve: Dave Burrell, `dburrell@southwestvalves.com`  
       - **Product Specifications**: Extract technical details, performance standards, materials, or requirements from the RFP. If not specified, label as "Not specified."  

    3. **Extraction Criteria**:  
       - Match content in the RFP with the respective company’s predefined **brands**, **product categories**, and **specific technologies**.  
       - Include only equipment and technologies explicitly linked to Shape or Southwest Valve’s offerings.  

<EXAMPLE RESPONSE>
Affirmative Response:
If the user agrees to proceed:
{{
    "document_name": "Project ABC – Bluesheet Draft.xlsx",
    "Shape": [
        {{
            "Spec Section": "22 15 00",
            "Equipment/Item Description": "Water Pressure Regulator",
            "Named Manufacturers": "Zurn, Watts",
            "Represented Company": "Shape",
            "Contact Information": "Nick Chavez, nchavez@shapecal.com",
            "Product Specifications": "Pressure range: 0-300 PSI, brass construction."
        }}
    ],
    "Southwest Valve": [
        {{
            "Spec Section": "33 30 00",
            "Equipment/Item Description": "Butterfly Valve",
            "Named Manufacturers": "Val-Matic, Pratt",
            "Represented Company": "Southwest Valve",
            "Contact Information": "Dave Burrell, dburrell@southwestvalves.com",
            "Product Specifications": "Diameter: 24 inches, bi-directional sealing."
        }}
    ]
}}
Negative Response:
If the user declines:
"Understood. You chose not to generate the bluesheet for Shape and Southwest Valve."
"""



follow_up_prompt = """
<INSTRUCTIONS>
User has been asked if they would like to perform any other actions/do something or not. Interprete the response in <USER_RESPONSE> and perform ACTION... 
<ACTION IF USER WANTS TO DO SOMETHING>
Reply with: "Provide details on the next action you would like to take, and I will assist you."
<ACTION IF USER DOES NOT WANT TO DO SOMETHING>
Reply with: "END: I will conclude the session. Thank you for using this service."
<USER_RESPONSE>{user_response}</USER_RESPONSE>
"""

response_handling_prompt = """
<INSTRUCTIONS>
The user has responded. Interpret the response in <USER_RESPONSE>, and do what the user wants to do.
<USER_RESPONSE>
{user_response}
</USER_RESPONSE>
<OUTPUT>
Follow the instructions provided in the response and generate the appropriate output (In HTML format).
"""
