import streamlit as st
import pandas as pd
import numpy as np
import io

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

    # Generate the additional Excel sheets with mapped columns
    data_mapped = data_expanded[['Custom_ID', 'Grade', 'School', 'School_ID', 'District', 'Block']].copy()
    data_mapped.columns = ['Roll_Number', 'Grade', 'School Name', 'School Code', 'District Name', 'Block Name']
    data_mapped['Gender'] = np.random.choice(['Male', 'Female'], size=len(data_mapped), replace=True)
    
    # Generate Teacher_Codes sheet
    teacher_codes = data[['School', 'School_ID']].copy()
    teacher_codes.columns = ['School Name', 'Teacher Code']

    return data_expanded, data_mapped, teacher_codes

def main():
    st.title("Tool for ID generation")
    
    # Initialize session state for buttons
    if 'buttons_initialized' not in st.session_state:
        st.session_state['buttons_initialized'] = True
        st.session_state['download_data'] = None
        st.session_state['download_mapped'] = None
        st.session_state['download_teachers'] = None
        st.title("Input File Structure")
        
        # Data for the example table
        data = {
            'District': ['District A', 'District B', 'District C'],
            'Block': ['Block A', 'Block B', 'Block C'],
            'School_ID': [1001, 1002, 1003],
            'School': ['School A', 'School B', 'School C'],
            'Total_Students': [300, 450, 200]
        }
        # Create a DataFrame
        df = pd.DataFrame(data)
        # Display the table
        st.table(df)
        # Display a note emphasizing that School_ID should be unique
        st.markdown(" Note:School_ID column should be unique")

    # File uploader section
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

    if uploaded_file is not None:
        st.write("File uploaded successfully!")
        
        # Checkboxes to select mode
        run_default = st.checkbox("Rock the Default Settings")
        customize_id = st.checkbox("Play by Your Rules")

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
            partner_id = st.number_input("Partner ID", min_value=0, value=1)
            grade = st.number_input("Grade", min_value=1, value=1)
            buffer_percent = st.number_input("Buffer (%)", min_value=0.0, max_value=100.0, value=30.0)
            district_digits = st.number_input("District ID Digits", min_value=1, value=2)
            block_digits = st.number_input("Block ID Digits", min_value=1, value=2)
            school_digits = st.number_input("School ID Digits", min_value=1, value=3)
            student_digits = st.number_input("Student ID Digits", min_value=1, value=4)
            
            # Display parameter descriptions directly in selectbox
            parameter_options = list(parameter_descriptions.values())
            selected_description = st.selectbox("Select Parameter Set", parameter_options)
            
            # Get the corresponding parameter key
            selected_param = list(parameter_descriptions.keys())[parameter_options.index(selected_description)]
            st.write(parameter_descriptions[selected_param])

            # Add notification messages
            st.warning("Avoid Digit Overload in Your Enrollments:")

        if run_default or customize_id:
            if st.button("Generate IDs"):
                data_expanded, data_mapped, teacher_codes = process_data(uploaded_file, partner_id, buffer_percent, grade, district_digits, block_digits, school_digits, student_digits, selected_param)

                # Save the data for download
                towrite1 = io.BytesIO()
                towrite2 = io.BytesIO()
                towrite3 = io.BytesIO()
                with pd.ExcelWriter(towrite1, engine='xlsxwriter') as writer:
                    data_expanded.to_excel(writer, index=False)
                with pd.ExcelWriter(towrite2, engine='xlsxwriter') as writer:
                    data_mapped.to_excel(writer, index=False)
                with pd.ExcelWriter(towrite3, engine='xlsxwriter') as writer:
                    teacher_codes.to_excel(writer, index=False)
                
                towrite1.seek(0)
                towrite2.seek(0)
                towrite3.seek(0)
                
                # Update session state for download links
                st.session_state['download_data'] = towrite1
                st.session_state['download_mapped'] = towrite2
                st.session_state['download_teachers'] = towrite3

    # Always show download buttons
    if st.session_state['download_mapped'] is not None:
        st.download_button(label="Download Student IDs", data=st.session_state['download_mapped'], file_name="Student_Ids_Mapped.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    if st.session_state['download_teachers'] is not None:
        st.download_button(label="Download School Codes", data=st.session_state['download_teachers'], file_name="Teacher_Codes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    main()
