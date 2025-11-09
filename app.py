

import sqlite3
import pandas as pd
import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load Gemini API Key
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=API_KEY)


# Extract SQL properly from Gemini response
def get_gemini_sql(question, prompt):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([prompt[0], question])
    text = response.text.strip()

    # Only pick first SELECT-based line
    lines = text.splitlines()
    sql_candidates = [l for l in lines if l.strip().lower().startswith("select")]

    if sql_candidates:
        return sql_candidates[0]
    else:
        return text


# Generate SQL explanation
def explain_sql_query(query):
    explain_prompt = f"Explain this SQL query step-by-step in simple terms:\n{query}"
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(explain_prompt)
    return response.text.strip()


# Execute SQL on SQLite
def read_sql_query(sql, db):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        col_name = [desc[0] for desc in cur.description]
        conn.close()
        return rows, col_name

    except sqlite3.Error as e:
        return [("SQL Error", str(e))], ["Error"]


# Professional Prompt
prompt = ["""
# 1. Context:
You are helping the user interact with a SQLite **employee database** using natural language.

# 2. Role:
You are an expert SQL assistant who converts English questions into SQLite queries.

# 3. Database Description:
Target database: employee_details.db

Available table:

1) employee_details
   - Contains employee details such as:
     employee_id, name, age, gender, role, department, salary, join_date,
     email, phone, city, state, performance_rating, experience_years,
     employment_type, work_mode

# 4. Instructions:
- Translate the user's question into a valid SQLite query.
- Use only SQLite syntax.
- Use correct table & column names.
- Do not use backticks (`) or semicolons.
- Keep SQL clean & correct.
- If the user mentions:
    → "employees", "employee", "staff", "workers", treat all as referring to the employee_details table.
- For filtering text, use LIKE for partial match.
- For counting/aggregation, use COUNT, AVG, SUM, MIN, MAX properly.

# 5. Examples:

Q: List all employees.
A: SELECT * FROM employee_details

Q: Show only Software Developers.
A: SELECT * FROM employee_details WHERE role = 'Software Developer'

Q: Who earns more than 60000?
A: SELECT * FROM employee_details WHERE salary > 60000

Q: Count of Data Analysts.
A: SELECT COUNT(*) FROM employee_details WHERE role = 'Data Analyst'

Q: Highest salary employee.
A: SELECT * FROM employee_details ORDER BY salary DESC LIMIT 1

Q: Show employees from Delhi.
A: SELECT * FROM employee_details WHERE city = 'Delhi'

Q: Show average salary by department.
A: SELECT department, AVG(salary) FROM employee_details GROUP BY department

Q: List employees joined after 2021.
A: SELECT * FROM employee_details WHERE join_date > '2021-01-01'

# 6. Chain of Thought:
Understand the question, map keywords to SQL, and return the final SQL query only.

Now generate the SQL query for this question:
"""]




#  we are setting the page congiguration

st.set_page_config(page_title="Gemini SQL Assistant", layout="wide")

st.title("Gemini SQL Assistant (Employee DB)")
st.write("Ask questions in English. Get SQL queries and results instantly!")


# Question Inout
question = st.text_input("Enter Your Question:")


# we assign some example 
with st.expander("Try These Examples"):
    st.markdown("""
    - List all employees.
    - Show only Software Developers.
    - Who earns more than 60,000?
    - Count of Data Analysts.
    - Highest salary employee.
    - Provide the average salary based on department.
    - Show employees from Mumbai.
    - List employees who joined after 2022.
    - Show employees with performance rating greater than 4.
    - Count employees having more than 5 years of experience.
    """)


# ✅ RUN BUTTON
if st.button("RUN"):

    if question.strip() == "":
        st.warning("Please enter a question")

    else:
        # Foe Generate SQL
        sql_query = get_gemini_sql(question, prompt)

        st.subheader("Generated SQL Query:")
        st.code(sql_query, language="sql")

        
        result, columns = read_sql_query(sql_query, "employee_details.db")

        # use for when sql error occure
        if result and "SQL Error" in result[0]:
            st.error(f"Error: {result[0][1]}")

        else:
            #  Display result + explanation side-by-side
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Query Result")
                df = pd.DataFrame(result, columns=columns)
                st.dataframe(df, use_container_width=True)

            with col2:
                st.subheader("SQL Explanation")
                explanation = explain_sql_query(sql_query)
                st.write(explanation)
