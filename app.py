import streamlit as st
import pandas as pd
import datetime
from utils import init_db,connect_db, render_navbar, get_daily_stock_data,group_and_aggregate_data
from utils import get_aggregated_data, create_company_table, add_company_to_db, create_order_table, get_company_details, add_order_to_db, get_pending_orders,create_invoice_table, get_company_address, add_invoice_to_db, get_stock_details
from utils import show_invoice_details, add_worker, get_worker_names, add_dailystock, insert_product_details, generate_invoice_pdf

from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.add_vertical_space import add_vertical_space






# Initialize the database
init_db()

# Render navigation bar
render_navbar()

# Render content based on the current page
page = st.session_state.get('page', 'home')

if page == 'home':
    st.title('Home Page')
    st.write('Welcome to the Textile Management System!')




elif page == 'add_production2':
     
    st.header('Add Production')

    sr_no = st.text_input('SR No. (Unique)')
    quality = st.selectbox('Quality', ['60 gm Plain', 'Chiffon'])
    today_date = datetime.date.today()

    # Machine number inputs side by side
    col1, col2 = st.columns(2)
    with col1:
        machine_no1 = st.selectbox('Machine',['','A','B','L','H','R','G','S','M','P'], key='machine_no1', placeholder='M', help='Enter first part of machine number')
    with col2:
        machine_no2 = st.number_input('Machine No',step=1, key='machine_no2', placeholder='01', help='Enter second part of machine number')

    # Combine machine number parts
    machine_no = f"{machine_no1}{machine_no2}"



    worker_names_list =  get_worker_names()
    print(type(worker_names_list))

    with st.container():
        st.subheader(f'SR No. {sr_no}')
        dates = [(today_date - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)]

        # Initialize lists to capture inputs
        date_inputs, worker1_metre, worker2_metre, worker3_metre = [], [], [], []

        col1, col2, col3, col4 = st.columns(4)

       

        with col1:
            st.write("")    
            st.markdown("<p style='font-size:32px; font-weight:bold;'>DATE</p>", unsafe_allow_html=True)

            for date in dates:
                date_input = st.text_input('', value=date, key=f'date_{date}')
                date_inputs.append(date_input)

        with col2:
            worker1_name = st.selectbox('Worker 1', options=worker_names_list, key='worker1_name')
            worker1_metre = [st.number_input('', min_value=0, step=1, key=f'metre01_{i}', label_visibility='hidden') for i in range(5)]

        with col3:
            worker2_name = st.selectbox('Worker 2', options=worker_names_list, key='worker2_name')
            worker2_metre = [st.number_input('', min_value=0, step=1, key=f'metre11_{i}', label_visibility='hidden') for i in range(5)]

        with col4:
            worker3_name = st.selectbox('Worker 3', options=worker_names_list, key='worker3_name')
            worker3_metre = [st.number_input('', min_value=0, step=1, key=f'metre21_{i}', label_visibility='hidden') for i in range(5)]

   # Calculate total metre
    total_metre = sum(worker1_metre) + sum(worker2_metre) + sum(worker3_metre)

    # Display total metre count
    st.write(f"**Total Metre:** {total_metre}")

    # Additional input fields for weight, category, and remarks
    weight = st.number_input("Weight", min_value=0.0, step=0.1, format="%.2f")
    category = st.selectbox("Category", ["Category 1", "Category 2", "Category 3"])
    remarks = st.text_area("Remarks", height=100)

    # Collect data for each worker and date combination if there is a valid metre value
    product_data = []
    for i in range(5):
        for worker_name, metres in [(worker1_name, worker1_metre), (worker2_name, worker2_metre), (worker3_name, worker3_metre)]:
            metre_value = metres[i]
            if worker_name and metre_value > 0:
                try:
                    metre_value_float = float(metre_value)
                    product_data.append((sr_no, date_inputs[i], worker_name, metre_value_float, machine_no))
                except ValueError:
                    st.error(f"Invalid metre value for {worker_name} on {date_inputs[i]}")

    # Submit button to save data
    if st.button('Submit'):
        if sr_no and quality and total_metre and weight:
            sr_no_added = add_dailystock(sr_no, quality, total_metre, weight, today_date, machine_no, category, remarks)

            if sr_no_added and product_data:
                insert_product_details(product_data)
                for key in st.session_state.keys():
                    del st.session_state[key]
            
            elif not sr_no_added:
                st.warning("SR No. already exists. Product details will not be added.")

        
        else :
            st.warning("data missing.")





        if sr_no and quality and total_metre and weight:
            # Display the data being added
            st.subheader("Data to be added:")
            st.write(f"**SR No:** {sr_no}")
            st.write(f"**Quality:** {quality}")
            st.write(f"**Total Metre:** {total_metre}")
            st.write(f"**Weight:** {weight}")
            st.write(f"**Machine No:** {machine_no}")
            st.write(f"**Category:** {category}")
            st.write(f"**Remarks:** {remarks}")
            
            # Prepare data for table format
            worker_data = {
                'Date': date_inputs,
                worker1_name: worker1_metre,
                worker2_name: worker2_metre,
                worker3_name: worker3_metre
            }
            df_worker_data = pd.DataFrame(worker_data)

            # Display the table
            st.write("**Product Details:**")
            st.table(df_worker_data)
       

   

elif page == 'product_data':

    st.title('Product Data')
    conn = connect_db()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM product_details')
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=['ID','SR. NO','Date','worker name','metre', 'machine_no'])
            st.dataframe(df)
        finally:
            cursor.close()
            conn.close()
    

elif page == 'daily_stock_data':
    st.title('Daily Stock Data')
    data = get_daily_stock_data()
    df = pd.DataFrame(data, columns=['SR No.', 'QUALITY','Metre', 'Weight', 'Machine No.','Category', 'Remarks','today_date'])
    st.dataframe(df)



elif page == 'daily_report':

    st.title('Aggregate Daily Stock Data')

    # Date input
    date = st.text_input('Date (YYYY-MM-DD)')

    # Quality dropdown
    quality = st.selectbox('Quality', ['60 gm Plain', 'Chiffon'])

    if st.button('Submit'):
        if date:
            group_and_aggregate_data(date, quality)
            st.success(f'Data aggregated and stored for {quality} on {date}.')
        else:
            st.error('Please enter a date.')


    st.header('Aggregated Daily Stock Data - 60 gm Plain')
    aggregated_data_60gm_plain = get_aggregated_data('aggregated_60gm_plain')
    df_60gm_plain = pd.DataFrame(aggregated_data_60gm_plain, columns=['Date', 'Quality', 'SR No. Count', 'Metre Sum', 'Total Stock', 'Sales'])
    st.dataframe(df_60gm_plain)
    
    st.header('Aggregated Daily Stock Data - Chiffon')
    aggregated_data_chiffon = get_aggregated_data('aggregated_chiffon')
    df_chiffon = pd.DataFrame(aggregated_data_chiffon, columns=['Date', 'Quality', 'SR No. Count', 'Metre Sum', 'Total Stock', 'Sales'])
    st.dataframe(df_chiffon)

elif page == 'add_client_details': 
    create_company_table()

    st.title('Add Company Details')

    with st.form(key='company_form'):
        name = st.text_input('Name')
        address = st.text_area('Address')
        contact_number = st.text_input('Contact Number')
        submit_button = st.form_submit_button(label='Submit')

    if submit_button:
        if name and address and contact_number:
            add_company_to_db(name, address, contact_number)
        else:
            st.error('Please fill in all fields.')



elif page == 'add_order':

    # Initialize the database and create the order_requests table
    create_order_table()

    # Create the Streamlit form for order requests
    st.title('Add Order Request')

    # Fetch company details for the dropdown list
    companies = get_company_details()
    company_dict = {name: code for code, name in companies}

    company_name = st.selectbox('Company Name', list(company_dict.keys()))
    company_code = company_dict[company_name]
    quantity = st.number_input('Quantity', min_value=1, step=1)
    quality = st.selectbox('Quality', ['60 gm Plain', 'Chiffon'])

    if st.button('Submit'):
        if company_name and quantity and quality:
            today_date = datetime.datetime.today().strftime('%Y-%m-%d')
            add_order_to_db(today_date, company_code, quantity, quality)
        else:
            st.error('Please fill in all fields.')


# Create a Streamlit page to display pending orders
elif page == 'pending_orders':
    st.title('Pending Orders')
    
    pending_orders = get_pending_orders()
    
    if pending_orders:
        order_data = []
        for order in pending_orders:
            order_id, company_name, quality, completed_quantity, quantity = order
            progress = f"{completed_quantity}/{quantity}"
            order_data.append([company_name, quality, progress])
        
        df = pd.DataFrame(order_data, columns=['Company Name', 'Quality', 'Quantity'])
        st.dataframe(df)
    else:
        st.write('No pending orders.')



elif page == 'make_invoice':
    
    create_invoice_table()
    # Initialize the form
    st.title('Create Challan')
    # create_invoice_table()

    # Auto-incremented challan number
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(challan_number) FROM invoice_details')
    result = cursor.fetchone()
    conn.close()
    challan_number = result[0] + 1 if result[0] else 1
    st.write(f'Challan Number: {challan_number}')

    # Date input
    date = datetime.datetime.today().strftime('%Y-%m-%d')
    st.write(f'Date: {date}')

    # Company details
    companies = get_company_details()
    company_dict = {name: code for code, name in companies}
    company_name = st.selectbox('Company Name', list(company_dict.keys()))
    company_code = company_dict[company_name]
    address = get_company_address(company_code)
    st.write(f'Address: {address}')

    # Broker and Quality
    broker = st.text_input('Broker')
    quality = st.selectbox('Quality', ['60 gm Plain', 'Chiffon'])

    # SR No. inputs
    sr_no_list = []
    metre_list = []
    weight_list = []
    total_metre = 0 
    for i in range(28):
        col1, col2, col3 = st.columns(3)
        with col1:
            sr_no = st.text_input(f'SR No. {i + 1}', key=f'sr_no_{i}')
            if sr_no:
                sr_no_list.append(sr_no)
                metre, weight, machine_no = get_stock_details(sr_no)
                metre_list.append(metre)
                weight_list.append(weight)
                # Handle None or invalid metre values
                if metre is not None and isinstance(metre, (int, float)):
                    total_metre += metre
                else:
                    metre_list[-1] = 'N/A'  # Replace invalid metre with 'N/A'


        with col2:
            st.write(f'Metre: {metre_list[-1]}' if sr_no else 'Metre: N/A')
            
        with col3:
            st.write(f'Weight: {weight_list[-1]}' if sr_no else 'Weight: N/A')
        
        # Display totals
    sr_no_count = 0
    sr_no_count =len(sr_no_list)
    st.write(f"Total SR No. Count: {len(sr_no_list)}")
    st.write(f"Total Metre: {total_metre}")

    # Form submission logic here
    if st.button('Submit'):
        if company_name and broker and quality and sr_no_list:
            valid = True  # Flag to track if all SR numbers are valid
            
            for sr_no in sr_no_list:
                metre, weight, machine_no = get_stock_details(sr_no)
                if metre == 'Product not found':
                    valid = False  # Mark as invalid if any SR number is not found
                    break  # Exit the loop immediately when an invalid SR number is found

            if valid:
            # Fetch the order details to check the remaining quantity
                conn = connect_db()
                cursor = conn.cursor(buffered=True)
                cursor.execute('''SELECT quantity, completed_quantity FROM order_requests WHERE company_code = %s AND quality = %s AND status = 'pending'ORDER BY order_id ASC LIMIT 1''', 
                           (company_code, quality))
                order = cursor.fetchone()
                conn.close()

                if order:
                    quantity, completed_quantity = order
                    remaining_quantity = quantity - completed_quantity
                    
                    if sr_no_count <= remaining_quantity:
                        # Proceed with adding the invoice and updating completed orders
                        add_invoice_to_db(challan_number, date, company_code, company_name, address, broker, quality, sr_no_list)
                        
                        
                        # Generate PDF after data is saved
                        pdf_filename = generate_invoice_pdf(challan_number, date, company_name, broker, quality, sr_no_list, total_metre)
        
                        st.success('Challan created successfully!')
                    else:
                        st.error('Challan creation failed: Insufficient remaining quantity to fulfill the order.')
                else:
                    st.error('No matching order found for the provided company and quality.')
            else:
                st.error('Challan creation failed due to an invalid SR number.')
        else:
            st.error('Please fill in all required fields.')



elif page == 'view_invoice':
    st.title("View Invoices")

        # Fetch latest 20 invoices
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT challan_number, date, company_name, quality, quantity FROM invoice_header ORDER BY date DESC LIMIT 20')
    invoices = cursor.fetchall()
    conn.close()

    st.subheader("Latest 20 Invoices")
    headers = ["Challan Nos", "Date", "Company", "Quality", "Quantity", "Actions"]
    st.write("      -     ".join(headers))

    for invoice in invoices:
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])
        col1.write(invoice[0])  # Challan Number
        col2.write(invoice[1])  # Date
        col3.write(invoice[2])  # Company Name
        col4.write(invoice[3])  # Quality
        col5.write(invoice[4])  # Quantity

        if col6.button(f"View Invoice ", key=invoice[0]):
            show_invoice_details(invoice[0])



elif page == "add_worker":

    st.title("Add Worker")
    with st.form("worker_form"):
        name = st.text_input("Worker Name")
        date_joined = st.date_input("Date Joined", value=datetime.date.today())  # Default to today's date
        position = st.selectbox("Position", ["Worker", "Manager", "Supervisor"], index=0)  # Default to "Worker"
                    
                # Submit button
        submitted = st.form_submit_button("Add Worker")
                    
        if submitted:
            add_worker(name, date_joined, position)
            st.success(f"Worker {name} added successfully!")

# Ensure the current page is set in session state
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'



