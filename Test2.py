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

def main():
    # Centered title
    st.markdown("<h1 style='text-align: center;'>Tool for ID Generation</h1>", unsafe_allow_html=True)

    # Replace text and set font size to small
    st.markdown("<p style='font-size: small;'>Please rename your column headers as per input file structure shown:</p>", unsafe_allow_html=True)

    # Data for the example table
    data = {
        'District': ['District A'],
        'Block': ['Block A'],
        'School_ID': [1001],
        'School': ['School A'],
        'Total_Students': [300]
    }
    # Create a DataFrame
    df = pd.DataFrame(data)

    # Convert DataFrame to HTML
    html_table = df.to_html(index=False, border=0, classes='custom-table')

    # Custom CSS to style the table
    css = """
    <style>
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        margin-top: 1px; /* Adjust spacing between text and table */
    }
    .custom-table th, .custom-table td {
        padding: 10px;
        text-align: left;
        border: 1px solid #ddd;
    }
    .custom-table th {
        background-color: #f4f4f4;
        text-align: center;
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
    </style>
    """

    # Display the text and table
    st.markdown(css, unsafe_allow_html=True)
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

    # Display the new blue text lines
    #st.markdown("<p style='color: blue;'>Please provide required values</p>", unsafe_allow_html=True)

    # Initialize session state for buttons
    if 'buttons_initialized' not in st.session_state:
        st.session_state['buttons_initialized'] = True
        st.session_state['download_data'] = None
        st.session_state['download_mapped'] = None
        st.session_state['download_teachers'] = None

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

        if run_default:
            # Default parameters
            partner_id = 1
            grade = st.number_input("Grade", min_value=1, value=1)
            buffer_percent = 0.0
            district_digits = 2
            block_digits = 2
            school_digits = 3
            student_digits = 3
            selected_param = 'A4'  # Default to A4

            st.write("Default parameters are set.")

        
    
        if customize_id:
    # Custom parameters
            st.markdown("<p style='color: blue;'>Please provide required values</p>", unsafe_allow_html=True)
            partner_id = st.number_input("Partner ID", min_value=0, value=1)
            grade = st.number_input("Grade", min_value=1, value=1)
            buffer_percent = st.number_input("Buffer (%)", min_value=0.0, max_value=100.0, value=30.0)
            st.markdown("<p style='color: blue;'>Please provide required digits</p>", unsafe_allow_html=True)
            district_digits = st.number_input("District ID Digits", min_value=1, value=2)
            block_digits = st.number_input("Block ID Digits", min_value=1, value=2)
            school_digits = st.number_input("School ID Digits", min_value=1, value=3)
            student_digits = st.number_input("Student ID Digits", min_value=1, value=4)

    # Display parameter descriptions directly in selectbox
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
            parameter_options = list(parameter_descriptions.values())
            selected_description = st.selectbox("", parameter_options)

    # Get the corresponding parameter key
            #selected_param = list(parameter_descriptions.keys())[parameter_options.index(selected_description)]
            #st.write(parameter_descriptions[selected_param])
            st.markdown("X"*LEN(partner_id))
            

    # Add notification messages
            st.warning("Avoid Digit Overload in Your Enrollments:")

        if run_default or customize_id:
            if st.button("Generate IDs"):
                data_expanded, data_mapped, teacher_codes = process_data(uploaded_file, partner_id, buffer_percent, grade, district_digits, block_digits, school_digits, student_digits, selected_param)

                # Save the data for download
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    data_expanded.to_excel(writer, sheet_name='Full Data', index=False)
                    data_mapped.to_excel(writer, sheet_name='Mapped Data', index=False)
                    teacher_codes.to_excel(writer, sheet_name='Teacher Codes', index=False)
                excel_data = excel_buffer.getvalue()

                b64 = base64.b64encode(excel_data).decode()
                st.session_state['download_data'] = f'<a href="data:application/octet-stream;base64,{b64}" download="generated_ids.xlsx" class="download-link"><img src="https://img.icons8.com/material-outlined/24/000000/download.png" class="download-icon"/>Click here to download Full Data File</a>'
                st.session_state['download_mapped'] = f'<a href="data:application/octet-stream;base64,{b64}" download="mapped_data.xlsx" class="download-link"><img src="https://img.icons8.com/material-outlined/24/000000/download.png" class="download-icon"/>Click here to Download Student IDs</a>'
                st.session_state['download_teachers'] = f'<a href="data:application/octet-stream;base64,{b64}" download="teacher_codes.xlsx" class="download-link"><img src="https://img.icons8.com/material-outlined/24/000000/download.png" class="download-icon"/>Click here to Download School Codes</a>'

            # Display the download links
            #if st.session_state['download_data']:
                #st.markdown(st.session_state['download_data'], unsafe_allow_html=True)
            if st.session_state['download_mapped']:
                st.markdown(st.session_state['download_mapped'], unsafe_allow_html=True)
            if st.session_state['download_teachers']:
                st.markdown(st.session_state['download_teachers'], unsafe_allow_html=True)

if __name__ == '__main__':
    main()
