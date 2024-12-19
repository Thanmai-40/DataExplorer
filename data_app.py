import streamlit as st
import os
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_string_dtype, is_datetime64_any_dtype

uploaded_file =  st.file_uploader("Choose a file to upload")

def read_excel_file(uploaded_file):
    excel_file = pd.ExcelFile(uploaded_file)

    if len(excel_file.sheet_names) > 1:
        sheet_name = st.selectbox("Select the sheet to load", excel_file.sheet_names)
    else:
        sheet_name = excel_file.sheet_names[0]

    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    return df

def data_info(df):
    info_dict = {
        "Column": df.columns,
        "Non-Null Count": [df[col].notnull().sum() for col in df.columns],
        "Dtype": [df[col].dtype for col in df.columns]
    }
    info_df = pd.DataFrame(info_dict)
    return info_df

def indentify_file_type(uploaded_file):
    file_name = uploaded_file.name
    file_extension = os.path.splitext(file_name)[1].lower()
    return file_extension

def classify_data(df):
    numeric = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical = df.select_dtypes(include=["object", "category"]).columns.tolist()
    datetime = df.select_dtypes(include=["datetime64[ns]"]).columns.tolist()
    for col in df.select_dtypes(include=['object']):
        temp_col = pd.to_datetime(df[col], format = "%Y-%m-%d", errors="coerce")

        if temp_col.notna().all():
            datetime.append(col)

    return [numeric, categorical, datetime]

def display_missing_values(df):
    missing_values = df.isnull().sum()   
    missing_columns = missing_values[missing_values > 0] 
    missing_columns_df = missing_columns.reset_index() 
    missing_columns_df.columns = ['Column', 'Missing Values'] 
    return missing_columns_df 

def drop_null_values(df):
    df.dropna(inplace=True)
    st.write("Dropped Null Values")
    return df

def fill_missing_values(df):
    options = ['0', 'Mean', 'Median', 'Custom Value']

    if 'current_column_index' not in st.session_state:
        st.session_state.current_column_index = 0
        st.session_state.fill_values = {}

    def confirm_values(value):
        st.session_state.fill_values[current_column] = value
        st.session_state.current_column_index += 1

    missing_columns = [col for col in df.columns if df[col].isnull().any()]

    if st.session_state.current_column_index < len(missing_columns):
        current_column = missing_columns[st.session_state.current_column_index]

        st.write(f"Processing column: **'{current_column}'**")
    
        if is_numeric_dtype(df[current_column]):
            select_value = st.selectbox(f"Choose which value to fill nulls in column '{current_column}'", options=options, index=None)
            if select_value == 'Custom Value':
                value = st.number_input(f"Enter custom value for numeric column '{current_column}'")
                st.button("Confirm Value", on_click=confirm_values, args=(value,))
            if select_value =='Mean':
                value = df[current_column].mean()
                st.button("Confirm Mean", on_click=confirm_values, args=(value,))
            if select_value == 'Median':
                value = df[current_column].median()
                st.button("Confirm Median", on_click=confirm_values, args=(value,))
            if select_value == '0':
                value = 0
                st.button("Confirm Zero", on_click=confirm_values, args=(value,))
        
        if is_string_dtype(df[current_column]) or df[current_column].dtype == 'object':
            select_string_value = st.selectbox(f"Choose which value to fill nulls in column '{current_column}'", options=["No Value", "Not Available", "Custom Value"], index=None)
            if select_string_value == 'Custom Value':  
                value = st.text_input(f"Enter custom value for string column '{current_column}'")
                st.button("Confirm Value", on_click=confirm_values, args=(value,))

            if select_string_value in ['No Value', 'Not Available']:
                value = select_string_value
                st.button("Confirm Value", on_click=confirm_values, args=(value,))
        
        if is_datetime64_any_dtype(df[current_column]):
            min_value = min(df[current_column].dropna())
            max_value = max(df[current_column].dropna())
            value = st.date_input(f"Enter custom date to fill the date column '{current_column}'", min_value=min_value, max_value=max_value)
            st.button("Confirm Mean", on_click=confirm_values, args=(value,))
    
    else:
        for column in missing_columns:
            if column not in st.session_state.fill_values:
                st.session_state.fill_values[column] = 0

        for column, value in st.session_state.fill_values.items():
            df[column] = df[column].fillna(value=value)

        st.write("The values have been filled!")
        st.subheader("Dataset After Data Cleaning")
        st.write(df)
        return df

    return df

def visualize_data(df, chart_type, numeric_columns, categorical_columns, datetime_columns):
    if chart_type == 'Line Chart':
        numeric_and_categorical = numeric_columns + categorical_columns
        x_column = st.selectbox("Select x-axis column", options=numeric_and_categorical)
        y_column = st.selectbox("Select y-axis column", options=numeric_columns)

        if st.button("Generate Plot"):
            return st.line_chart(df.set_index(x_column)[y_column])

    if chart_type == 'Bar Chart':
        categorical_and_datetime = categorical_columns + datetime_columns
        x_column = st.selectbox("Select x-axis column", options=categorical_and_datetime)
        y_column = st.selectbox("Select y-axis column", options=numeric_columns)

        if st.button("Generate Plot"):
            return st.bar_chart(df.set_index(x_column)[y_column])

    if chart_type == 'Area Chart':
        categorical_and_datetime = categorical_columns + datetime_columns
        x_column = st.selectbox("Select x-axis column", options=categorical_and_datetime)
        y_column = st.selectbox("Select y-axis column", options=numeric_columns)

        if st.button("Generate Plot"):
            return st.area_chart(df.set_index(x_column)[y_column])

    if chart_type == 'Scatter Plot':
        x_column = st.selectbox("Select x-axis column", options=numeric_columns)
        y_column = st.selectbox("Select y-axis column", options=numeric_columns)

        if st.button("Generate Plot"):
            return st.scatter_chart(df.set_index(x_column)[y_column])

if uploaded_file is not None:
    
    file_type = indentify_file_type(uploaded_file)

    if file_type == ".csv":
        df = pd.read_csv(uploaded_file)
    elif file_type == ".xlsx":
        df = read_excel_file(uploaded_file)
    else:
        st.error("Unsupported File Format!")
        st.stop()

    # Total Records
    st.subheader("Total Records")
    st.metric("",value=len(df), label_visibility="collapsed")
    
    # Data Summary
    st.subheader("Data Summary")
    st.write(df.describe())
    
    # Data Information
    st.subheader("Data Information")
    info_df = data_info(df)
    st.dataframe(info_df, hide_index=True)

    # Categorize the Data
    numeric_columns, categorical_columns, datetime_columns = classify_data(df)

    st.subheader("Data Preview")
    st.write(df)

    # Checking for Missing Values
    st.subheader("Data Cleaning")
    missing_values = display_missing_values(df)

    if missing_values.empty:
        st.write("There are No Null Values")

    elif not missing_values.empty:

        st.write("Missing Values per Column")
        st.dataframe(missing_values, hide_index=True)

        # Data Cleaning
        st.write("Select an Cleaning Method")
        choice = st.radio("Select an cleaning method", ['Drop Null Values', 'Fill Missing Values'], index=None, label_visibility="collapsed")
        if choice == 'Drop Null Values':
            drop_null_values(df)

        elif choice == 'Fill Missing Values':
            st.subheader("Fill Null Values in Each Column")
            df = fill_missing_values(df)

    #Check for missing values after data cleaning 
    #missing_values = display_missing_values(df)
    #st.dataframe(missing_values, hide_index=True)

    # Checking for Duplicates
    st.subheader("Duplicates")
    if df.duplicated().any():
        duplicate = st.checkbox("Remove Duplicates")
        if duplicate:
            df.drop_duplicates(keep='last', inplace=True)
            st.write("Dropped Duplicate Values")
            st.write("")
            st.write(f"Now the total No.of Records are {len(df)}")

    elif not df.duplicated().any():
        st.write("There are no duplicates")

    # Filtering Data
    st.subheader("Filter Data")
    columns = df.columns.tolist()
    selected_column = st.selectbox("Select Column to filter by", columns)
    unique_values = df[selected_column].unique()
    selected_value = st.selectbox("Select Value", unique_values, index=None)

    filtered_df = df[df[selected_column] == selected_value]
    st.write(filtered_df)

    # Visualize Data
    st.subheader("Visualizing the Data")
    chart_options = ['Line Chart', 'Bar Chart', 'Area Chart', 'Scatter Plot']
    chart_type = st.selectbox("Select the Chart Type",options=chart_options, index=None)
    visualization = visualize_data(df, chart_type, numeric_columns, categorical_columns, datetime_columns)

else:
    st.write("Waiting for file upload...")
