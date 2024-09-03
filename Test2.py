import streamlit as st
import pandas as pd
import numpy as np
import io
import base64

# Define the parameter descriptions
parameter_descriptions = {
    'A1': "School + Grade + Student",
    'A2': "Block + School + Grade + Student",
    'A3': "District + School + Grade + Student",
    'A4': "Partner + School + Grade + Student",
    'A5': "District + Block + School + Grade + Student",
    'A6': "Partner + Block + School + Grade + Student",
    'A7': "Partner + District + School + Grade + Student",
    'A8': "Partner + District + Block + School + Grade + Student"
}

# Define the new mapping for parameter sets
parameter_mapping = {
    'A1': "School_ID,Grade,student_no",
    'A2': "Block_ID,School_ID,Grade,student_no",
    'A3': "District_ID,School_ID,Grade,student_no",
    'A4': "Partner_ID,School_ID,Grade,student_no",
    'A5': "District_ID,Block_ID,School_ID,Grade,student_no",
    'A6': "Partner_ID,Block_ID,School_ID,Grade,student_no",
    'A7': "Partner_ID,District_ID,School_ID,Grade,student_no",
    'A8': "Partner_ID,District_ID,Block_ID,School_ID,Grade,student_no"
}

def generate_custom_id(row, params):
    params_split = params.split(',')
    custom_id = []
    for param in params_split:
        if param in row and pd.notna(row[param]):
            value = row[param]
            if isinstance(value, float) and value % 1 == 0:
                value = int(value)
            custom_id.append(str(value))
    return ''.join(custom_id)

def process_data(uploaded_file, partner_id, buffer_percent, grade, district_digits, block_digits, school_digits, student_digits, selected_param):
    data = pd.read_excel(uploaded_file)
    # Assign the Partner_ID directly
    data['Partner_ID'] = str(partner_id).zfill(len(str(partner_id)))  # Padding Partner_ID
    data['Grade'] = grade
    # Assign unique IDs for District, Block, and School, default to "00" for missing values
    data['District_ID'] = data['District'].apply(lambda x: str(data['District'].unique().tolist().index(x) + 1).zfill(district_digits) if x != "NA" else "0".zfill(district_digits))
    data['Block_ID'] = data['Block'].apply(lambda x: str(data['Block'].unique().tolist().index(x) + 1).zfill(block_digits) if x != "NA" else "0".zfill(block_digits))
    data['School_ID'] = data['School_ID'].apply(lambda x: str(data['School_ID'].unique().tolist().index(x) + 1).zfill(school_digits) if x != "NA" else "0".zfill(school_digits))
    # Calculate Total Students With Buffer based on the provided buffer percentage
    data['Total_Students_With_Buffer'] = np.floor(data['Total_Students'] * (1 + buffer_percent / 100))
    # Generate student IDs based on the calculated Total Students With Buffer
    def generate_student_ids(row):
        if pd.notna(row['Total_Students_With_Buffer']) and row['Total_Students_With_Buffer'] > 0:
            student_ids = [
                f"{row['School_ID']}{str(int(row['Grade'])).zfill(2)}{str(i).zfill(student_digits)}"
                for i in range(1, int(row['Total_Students_With_Buffer']) + 1)
            ]
            return student_ids
        return []
    data['Student_IDs'] = data.apply(generate_student_ids, axis=1)
    # Expand the data frame to have one row per student ID
    data_expanded = data.explode('Student_IDs')
    # Extract student number from the ID
    data_expanded['student_no'] = data_expanded['Student_IDs'].str[-student_digits:]
    # Use the selected parameter set for generating Custom_ID
    data_expanded['Custom_ID'] = data_expanded.apply(lambda row: generate_custom_id(row, parameter_mapping[selected_param]), axis=1)
    # Generate the additional Excel sheets with mapped columns (without the Gender column)
    data_mapped = data_expanded[['Custom_ID', 'Grade', 'School', 'School_ID', 'District', 'Block']].copy()
    data_mapped.columns = ['Roll_Number', 'Grade', 'School Name', 'School Code', 'District Name', 'Block Name']
    # Generate Teacher_Codes sheet
    teacher_codes = data[['School', 'School_ID']].copy()
    teacher_codes.columns = ['School Name', 'Teacher Code']
    return data_expanded, data_mapped, teacher_codes

def download_link(df, filename, link_text):
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-link"><img src="https://img.icons8.com/material-outlined/24/000000/download.png" class="download-icon"/> {link_text}</a>'

def main():
    # Centered title
    st.markdown("<h1 style='text-align: center;'>Tool for ID Generation</h1>", unsafe_allow_html=True)
    
    # Initialize session state
    if 'buttons_initialized' not in st.session_state:
        st.session_state['buttons_initialized'] = True
        st.session_state['generate_clicked'] = False
        st.session_state['download_data'] = None
        st.session_state['checkboxes_checked'] = False

    # Data for the example table
    data = {
        'District': ['District A'],
        'Block': ['Block A'],
        'School_ID': [1001],
        'School': ['School A'],
        'Total_Students': [300]
    }
    df = pd.DataFrame(data)
    
    # Convert DataFrame to HTML
    html_table = df.to_html(index=False, border=0, classes='custom-table')
    
    # Custom CSS to style the table and the warning box
    css = """
    <style>
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        margin-top: 10px;
    }
    .custom-table th, .custom-table td {
        padding: 10px;
        text-align: center;
        border: 1px solid #ddd;
    }
    .custom-table th {
        background-color: #F4F4F4;
    }
    .download-link {
        color: green;
        text-decoration: none;
        font-weight: bold;
    }
    .download-link:hover {
        text-decoration: underline;
    }
    .download-icon {
        margin-right: 8px;
    }
    .warning-box {
        background-color: #FFFFE0;
        border: 1px solid #FFD700;
        padding: 10px;
        margin-top: 10px;
        border-radius: 5px;
    }
    </style>
    """
    
    # Display the text and table
    st.markdown(css, unsafe_allow_html=True)
    st.markdown("<p style='font-size: small;'>Please rename your column headers as per input file structure shown:</p>", unsafe_allow_html=True)
    st.markdown(html_table, unsafe_allow_html=True)
    
    # Display a single note with two pointers, separated by line breaks for clarity
    st.markdown(
        """
        <span style='color:red; font-weight:bold;'>Note:</span><br>
        <span style='color:black;'>• School_ID column should be unique</span><br>
        <span style='color:black;'>• Please upload an XLSX file that is less than 200MB in size.</span>
        """,
        unsafe_allow_html=True
    )
    
    # File uploader section
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    if uploaded_file is not None:
        # Centered and colored message
        st.markdown("<p style='text-align: center; color: green;'>File uploaded successfully!</p>", unsafe_allow_html=True)
        
        # Checkboxes to select mode
        run_default = st.checkbox("IDs with Default Settings")
        customize_id = st.checkbox("IDs with Customized Settings")
        
        # Ensure only one checkbox is selected
        if run_default and customize_id:
            st.warning("Please select only one option.")
            return

        # Set checkboxes_checked to True if either checkbox is selected
        st.session_state['checkboxes_checked'] = run_default or customize_id
        
        if run_default:
            # Default parameters
            partner_id = 1
            grade = st.number_input("Grade", min_value=1, value=1)
            buffer_percent = 0.0
            district_digits = 2
            block_digits = 2
            school_digits = 4
            student_digits = 3
            selected_param = 'A4'  # Default parameter
        elif customize_id:
            # Custom parameters
            st.markdown("<p style='color: blue;'>Please provide required Values</p>", unsafe_allow_html=True)
            partner_id = st.number_input("Partner ID", min_value=1, value=1)
            buffer_percent = st.number_input("Buffer Percentage", min_value=0.0, value=0.0, format="%.2f")
            grade = st.number_input("Grade", min_value=1, value=1)
            
            # Message in blue color above District ID Digits
            st.markdown("<p style='color: blue;'>Please provide required Digits</p>", unsafe_allow_html=True)
            district_digits = st.number_input("District ID Digits", min_value=1, value=2)
            block_digits = st.number_input("Block ID Digits", min_value=1, value=2)
            school_digits = st.number_input("School ID Digits", min_value=1, value=3)
            student_digits = st.number_input("Student ID Digits", min_value=1, value=4)
            
            # Display parameter descriptions directly in selectbox
            parameter_options = list(parameter_descriptions.values())
            st.markdown(
                """
                <style>
                .custom-selectbox-label {
                    color: blue;
                    margin: 0;
                }
                </style>
                <p class='custom-selectbox-label'>Please Select Parameter Set for Desired Combination of Student IDs</p>
                """,
                unsafe_allow_html=True
            )
            selected_description = st.selectbox("", parameter_options)
            
            # Get the corresponding parameter key
            selected_param = list(parameter_descriptions.keys())[parameter_options.index(selected_description)]
            
            # Create the format string based on selected_param
            param_description = parameter_descriptions[selected_param]
            format_parts = param_description.split(' + ')
            format_string = ' '.join([f"{'X' * (school_digits if 'School' in part else 
            block_digits if 'Block' in part else 
            district_digits if 'District' in part else 
            len(str(grade)) if 'Grade' in part else 
            len(str(partner_id)) if 'Partner' in part else 
            student_digits)}" for part in format_parts])
            
            # Display the ID format with a smaller font size
            st.markdown(f"<p style='font-size: small;'>Your ID format would be: {format_string}</p>", unsafe_allow_html=True)
            
            # Warning box in yellow color
            st.markdown("<div class='warning-box'><p style='color: black;'>Note: Avoid Digit Overload in your Enrolments</p></div>", unsafe_allow_html=True)
        
        # Generate button action
        if st.session_state['checkboxes_checked']:
            if st.button("Generate IDs"):
                if uploaded_file is not None:
                    try:
                        # Process the uploaded file
                        expanded_data, mapped_data, teacher_codes = process_data(
                            uploaded_file,
                            partner_id,
                            buffer_percent,
                            grade,
                            district_digits,
                            block_digits,
                            school_digits,
                            student_digits,
                            selected_param
                        )
                        # Update session state with generated data
                        st.session_state['download_data'] = (expanded_data, mapped_data, teacher_codes)
                        st.session_state['generate_clicked'] = True
                    except Exception as e:
                        st.error(f"Error processing file: {e}")
    
    # Download buttons after IDs are generated
    if st.session_state['generate_clicked'] and st.session_state['download_data'] is not None:
        expanded_data, mapped_data, teacher_codes = st.session_state['download_data']
        
        # Download button for full data with Custom_IDs and Student_IDs
        #st.markdown(download_link(expanded_data, "full_data.xlsx", "Download Full Data (with Custom_IDs and Student_IDs)"), unsafe_allow_html=True)
        
        # Download button for mapped data
        st.markdown(download_link(mapped_data, "mapped_data.xlsx", "Download Student IDs"), unsafe_allow_html=True)
        
        # Download button for teacher codes
        st.markdown(download_link(teacher_codes, "teacher_codes.xlsx", "Download School Codes"), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
