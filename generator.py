import subprocess
from sys import argv, stderr, stdout, exit
import re
import os
from os.path import exists, basename, join
from os import makedirs
from itertools import combinations_with_replacement as cmb

# Configuration constants
LOGGER_PREFIX = "GENERATOR"
USE_EXTENDED_MODE = True
INDENT = "    "


class Logger:
    @staticmethod
    def output(prefix, content, is_error=False):
        """Output messages to appropriate stream with formatting"""
        target = stderr if is_error else stdout
        if is_error:
            target.write(f"[{prefix}] {content}\n")
        else:
            target.write(f"{prefix}: {content}\n")
        target.flush()


class InputParser:
    @staticmethod
    def extract_parameters(filepath):
        """Extract PHI parameters from input file"""
        try:
            with open(filepath, 'r') as file:
                content = file.readlines()
        except Exception as error:
            Logger.output(LOGGER_PREFIX, f"Error while reading given input file: {error}", True)
            exit(1)  

        # Check if this is an SQL file
        if filepath.endswith('.sql'):
            # Return SQL query content
            return {"sql_query": ''.join(content)}

        # Create a mapping
        keyword_map = {
            "s:": "s", "n:": "n", "v:": "v", 
            "f:": "f", "p:": "p", "g:": "g",
            "(S)": "s", "(n)": "n", "(V)": "v", 
            "([F])": "f", "([C])": "p", "(G)": "g"
        }
        
        result = {"s": [], "n": [], "v": [], "f": [], "p": [], "g": ""}
        active_section = None

        # Check if file is in EMF format (with parentheses)
        is_emf_format = any("(" in line for line in content)
        
        if is_emf_format:
            # Process EMF format 
            key_place = {}
            keyword = ["(S)", "(n)", "(V)", "([F])", "([C])", "(G)"]
            
            for i in range(len(keyword)):
                for j in range(len(content)):
                    if keyword[i] in content[j]:
                        key_place[keyword[i]] = j
            
            # Make sure all required sections are found
            if not all(key in key_place for key in keyword):
                # Not all sections found, might be an SQL file or other format
                if any(line.strip().upper().startswith("SELECT") for line in content):
                    return {"sql_query": ''.join(content)}
                Logger.output(LOGGER_PREFIX, "Invalid EMF format: not all required sections found", True)
                exit(1)
                
            # Extract sections based on positions
            for i in range(len(keyword) - 1):
                begin = key_place[keyword[i]] + 1
                end = key_place[keyword[i+1]]
                section_content = content[begin:end]
                
                # Map to our internal format
                section_key = keyword_map[keyword[i]]
                
                if section_key == "s":
                    result[section_key] = [item.strip() for item in section_content[0].split(',')]
                elif section_key == "n":
                    result[section_key] = [item.strip() for item in section_content[0].split(',')]
                elif section_key == "v":
                    result[section_key] = [item.strip() for item in section_content[0].split(',')]
                elif section_key == "f":
                    result[section_key] = [item.strip() for item in section_content[0].split(',')]
                elif section_key == "p":
                    result[section_key] = section_content
                elif section_key == "g":
                    result[section_key] = section_content[0] if section_content else ""
            
            # Handle the last section
            last_key = keyword_map[keyword[-1]]
            last_content = content[key_place[keyword[-1]]+1:]
            if last_content:
                if last_key == "g":
                    result[last_key] = last_content[0] if last_content else ""
                else:
                    result[last_key] = last_content
        else:
            # Check if this might be an SQL file
            if any(line.strip().upper().startswith("SELECT") for line in content):
                return {"sql_query": ''.join(content)}
                
            # Process original format
            for line in content:
                clean_line = line.strip()
                
                # Skip empty lines
                if not clean_line:
                    continue
                
                # Check if line defines a section
                if clean_line.lower() in keyword_map:
                    active_section = keyword_map[clean_line.lower()]
                    continue
                
                # Check if line has format like "s:"
                for key in keyword_map:
                    if clean_line.startswith(key):
                        active_section = keyword_map[key]
                        clean_line = clean_line[len(key):].strip()
                        break
                
                if not active_section:
                    continue
                
                # Process content based on active section
                if active_section == "s":
                    result[active_section] = [item.strip() for item in clean_line.split(",")]
                elif active_section == "n":
                    # Handle grouping variable numbers
                    if isinstance(clean_line, str) and "," in clean_line:
                        result[active_section] = [item.strip() for item in clean_line.split(",")]
                    else:
                        try:
                            result[active_section] = int(clean_line)
                        except ValueError:
                            result[active_section] = clean_line
                elif active_section == "v":
                    result[active_section] = [item.strip() for item in clean_line.split(",")]
                elif active_section == "f":
                    result[active_section] = [item.strip() for item in clean_line.split(",")]
                elif active_section == "p":
                    result[active_section].append(clean_line)
                elif active_section == "g":
                    result[active_section] = clean_line
        
        # Handle n as if it's a list of strings
        if isinstance(result["n"], list):
            if all(isinstance(x, str) for x in result["n"]):
                result["n"] = len(result["n"])
        
        return result
    
    @staticmethod
    def get_parameters_from_user():
        """Interactively collect query parameters from user input"""
        result = {"s": [], "n": 0, "v": [], "f": [], "p": [], "g": ""}
        
        # Get select attributes (s)
        s_input = input("Enter select attributes (comma-separated): ")
        result["s"] = [item.strip() for item in s_input.split(",")]
        
        # Get number of grouping variables (n)
        n_input = input("Enter number of grouping variables: ")
        try:
            result["n"] = int(n_input)
        except ValueError:
            print("Invalid number, defaulting to 1")
            result["n"] = 1
        
        # Get grouping attributes (v)
        v_input = input("Enter grouping attributes (comma-separated): ")
        result["v"] = [item.strip() for item in v_input.split(",")]
        
        # Get aggregate functions (f)
        f_input = input("Enter aggregate functions (comma-separated): ")
        result["f"] = [item.strip() for item in f_input.split(",")]
        
        # Get predicates (p)
        print(f"Enter {result['n']} predicates (one per line, press Enter after each):")
        for i in range(result["n"]):
            p_input = input(f"Predicate for grouping variable {i}: ")
            result["p"].append(p_input)
        
        # Get having clause (g)
        g_input = input("Enter having clause (optional, press Enter to skip): ")
        result["g"] = g_input
        
        return result


class PredicateManager:
    @staticmethod
    def create_default_grouping_predicate(parameters):
        """Create predicate for grouping variable 0"""
        predicates = parameters["p"]
        default_predicate = ""

        for attr in parameters["v"]:
            default_predicate += f"0.{attr}=={attr} and "

        if default_predicate:
            default_predicate = default_predicate[:-5]  # Remove trailing " and "

        predicates.insert(0, default_predicate)
        return predicates
    
    @staticmethod
    def process_condition(condition, grouping_vars):
        """Process condition strings similar to utils.py"""
        logic_map = {">=": " >= ", "<=": " <= ", "=": " == ", "<>": ' != ', ">": " > ", "<": " < "}
        processed_conditions = []
        
        for piece in condition.split("and"):
            piece = piece.strip()
            for key in logic_map:
                if key in piece:
                    piece = piece.replace(key, logic_map[key])
                    break
            
            processed_conditions.append(piece)
        
        return " and ".join(processed_conditions)


class SchemaManager:
    @staticmethod
    def get_schema_info(db_params):
        """Get database schema information"""
        import psycopg2
        
        try:
            connection = psycopg2.connect(
                user=db_params.get('user', 'postgres'),
                password=db_params.get('password', '1234'),
                host=db_params.get('host', 'localhost'),
                port=db_params.get('port', '5432'),
                database=db_params.get('database', 'sales')
            )
            
            query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'sales';"
            cursor = connection.cursor()
            cursor.execute(query)
            
            if cursor.rowcount == 0:
                Logger.output(LOGGER_PREFIX, "Connected, but no schema data available", True)
                return []
            
            schema = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return schema
        except Exception as error:
            Logger.output(LOGGER_PREFIX, f"Error getting schema information: {error}", True)
            return []


class SqlQueryGenerator:
    @staticmethod
    def generate_sql_query_code(sql_query):
        """Generate code to execute a raw SQL query"""
        return f"""
    # Execute raw SQL query
    sql_query = \"\"\"
{sql_query}
    \"\"\"
    
    # Use a generator to efficiently process results
    def result_generator():
        cur.execute(sql_query)
        while True:
            rows = cur.fetchmany(100)  # Fetch in batches for efficiency
            if not rows:
                break
            for row in rows:
                yield row
    
    # Create PrettyTable for output
    table = PrettyTable()
    
    # Get column names from cursor description
    if cur.description:
        table.field_names = [desc[0] for desc in cur.description]
    
    # Add rows to table
    for row in result_generator():
        if isinstance(row, dict):
            table.add_row([row.get(field) for field in table.field_names])
        else:
            table.add_row(row)
    
    return table
"""


class CodeGenerator:
    @staticmethod
    def generate_query_structure(s, n, v, f, p, g, schema=None):
        """Generate query processing code structure with EMF logic"""
        sql_dtypes_maps = {"character varying": "''", "character": "''", "integer": 0, "numeric": 0.0}
        mf_dtypes = {}
        
        if schema:
            # Create type mapping from schema
            for col, dtype in schema:
                if dtype in sql_dtypes_maps:
                    mf_dtypes[col] = sql_dtypes_maps[dtype]
                else:
                    # Default to string for unknown types
                    mf_dtypes[col] = "''"
        else:
            # Default type inference
            for attr in v:
                mf_dtypes[attr] = "''"  # Default to string
            
            for agg_func in f:
                func_parts = agg_func.split('_')
                if len(func_parts) >= 3:
                    func_type, gv_num, attr_name = func_parts[0], func_parts[1], func_parts[2]
                    
                    if func_type in ["sum", "avg", "max", "min"]:
                        mf_dtypes[agg_func] = 0.0
                    elif func_type == "count":
                        mf_dtypes[agg_func] = 0
                    else:
                        mf_dtypes[agg_func] = "''"
        
        # Initialize structure code
        struct_init_code = ""
        struct_attr_list = "["
        
        # v
        for attr in v:
            struct_init_code += f"""        {attr} = ""\n"""
            struct_attr_list += f"'{attr}', "
        
        # f
        for agg_func in f:
            func_parts = agg_func.split('_')
            if len(func_parts) < 3:
                continue
                
            func_type = func_parts[0]
            struct_attr_list += f"'{agg_func}', "
            
            # agg
            if func_type == "sum" or func_type == "count":
                struct_init_code += f"""        {agg_func} = 0\n"""
            elif func_type == "avg":
                sum_attr = f"{agg_func}_sum"
                count_attr = f"{agg_func}_count"
                struct_init_code += f"""        {sum_attr} = 0\n        {count_attr} = 0\n        {agg_func} = 0\n"""
            elif func_type == "max":
                struct_init_code += f"""        {agg_func} = float('-inf')\n"""
            elif func_type == "min":
                struct_init_code += f"""        {agg_func} = float('inf')\n"""
            else:
                struct_init_code += f"""        {agg_func} = ""\n"""
        
        struct_attr_list = struct_attr_list[:-2] + "]" if struct_attr_list.endswith(", ") else struct_attr_list + "]"
        struct_init_code = struct_init_code[len(INDENT):] if struct_init_code else ""
        
        key_code = "("
        for attr in v:
            key_code += f"row.get('{attr}'), "
        key_code = key_code[:-2] + ")" if key_code.endswith(", ") else key_code + ")"
        
        group_insertion = ""
        for attr in v:
            group_insertion += f"        data[pos].{attr} = row.get('{attr}')\n"
        
        agg_loops = ""
        local_vars = ""
        
        if struct_attr_list != "[]":
            for attr in struct_attr_list[1:-1].replace("'", '').split(", "):
                local_vars += f"        {INDENT}{attr} = data[pos].{attr}\n"
        
        for agg_func in f:
            func_parts = agg_func.split("_")
            if len(func_parts) < 3:
                continue
                
            func_type, gv_num, agg_attr = func_parts[0], func_parts[1], func_parts[2]
            
            try:
                pred_idx = int(gv_num)
                if pred_idx < len(p):
                    pred = p[pred_idx]
                else:
                    pred = "True"  # Default
            except (ValueError, IndexError):
                pred = "True"  
            
            pred = pred.replace(f"{gv_num}.", "row.get('")
            pred = pred.replace("==", "')==")
            pred = pred.replace("!=", "')!=")
            pred = pred.replace(">", "')>")
            pred = pred.replace("<", "')<")
            
            # agg
            agg_code = ""
            if func_type == "sum":
                agg_code = f"data[pos].{agg_func} += row.get('{agg_attr}')"
            elif func_type == "count":
                agg_code = f"data[pos].{agg_func} += 1"
            elif func_type == "min":
                agg_code = f"if row.get('{agg_attr}') is not None:\n                    data[pos].{agg_func} = min(data[pos].{agg_func}, row.get('{agg_attr}'))"
            elif func_type == "max":
                agg_code = f"if row.get('{agg_attr}') is not None:\n                    data[pos].{agg_func} = max(data[pos].{agg_func}, row.get('{agg_attr}'))"
            elif func_type == "avg":
                # Average
                sum_var = f"data[pos].{agg_func}_sum"
                count_var = f"data[pos].{agg_func}_count"
                agg_code = (f"{sum_var} += row.get('{agg_attr}')\n"
                            f"            {INDENT}{count_var} += 1\n\n"
                            f"            {INDENT}if {count_var} != 0:\n"
                            f"            {INDENT}    data[pos].{agg_func} = {sum_var} / {count_var}\n"
                            f"            {INDENT}else:\n"
                            f"            {INDENT}    data[pos].{agg_func} = 'Infinity'")
            
            if USE_EXTENDED_MODE:
                agg_loops += (f"    cur.scroll(0, mode='absolute')\n\n"
                            f"    for row in cur:\n"
                            f"        for pos in range(len(data)):\n"
                            f"{local_vars}\n"
                            f"            if {pred}:\n"
                            f"                {agg_code}\n")
            else:
                agg_loops += (f"    cur.scroll(0, mode='absolute')\n\n"
                            f"    for row in cur:\n"
                            f"        key = {key_code}\n"
                            f"        pos = group_by_map.get(key)\n"
                            f"{local_vars}\n"
                            f"        if {pred}:\n"
                            f"            {agg_code}\n")
        
        # Having
        having_code = ""
        if g:
            having_condition = g
            for agg_func in f:
                having_condition = having_condition.replace(agg_func, f"obj.{agg_func}")
            having_code = f"    data = [obj for obj in data if {having_condition}]\n"
        
        def parse_arithmetic(attr):
            pattern = re.compile(r'([+\-*/])')
            match = pattern.search(attr)
            
            if match:
                op = match.group(1)
                pos = match.start()
                left = attr[:pos].strip()
                right = attr[pos + 1:].strip()
                return {"operator": op, "operand1": left, "operand2": right, "found": True}
            else:
                return {"found": False}
        
        ops_dict = {}
        for attr in s:
            ops_dict[attr] = parse_arithmetic(attr)
        
        select_cols = list(ops_dict.keys())
        
        return f"""
    class QueryStruct:
    {struct_init_code}
    data = []

    group_by_map = dict()

    for row in cur:
        key = {key_code}
        if (not group_by_map.get(key)) and (group_by_map.get(key) != 0):
            data.append(QueryStruct())
            group_by_map[key] = len(data) - 1

        pos = group_by_map.get(key)
{group_insertion}
{agg_loops}
    # Apply HAVING clause if present
{having_code}

    operations_dict = {ops_dict}
    table = PrettyTable()
    table.field_names = {select_cols}

    for obj in data:
        temp = []

        for j in table.field_names:
            if not operations_dict[j]['found']:
                temp.append(getattr(obj, j))
            else:
                if not (operations_dict[j]['operand1'].isnumeric() or operations_dict[j]['operand2'].isnumeric()):
                    value = eval(f"{{getattr(obj, operations_dict[j]['operand1'])}} {{operations_dict[j]['operator']}} {{getattr(obj, operations_dict[j]['operand2'])}}") # Use the template string
                    temp.append(value)
                else:
                    is_1_int = True if operations_dict[j]['operand1'].isnumeric() else False
                    is_2_int = True if operations_dict[j]['operand2'].isnumeric() else False
                    int_expr_str = f"{{operations_dict[j]['operand1']}} {{operations_dict[j]['operator']}} {{getattr(obj, operations_dict[j]['operand2'])}}" if is_1_int else f"{{getattr(obj, operations_dict[j]['operand1'])}} {{operations_dict[j]['operator']}} {{operations_dict[j]['operand2']}}"
                    value = eval(int_expr_str) # Evaluate the constructed expression string
                    temp.append(value)
        table.add_row(temp)

    # Printing the table
    return table
"""


class QueryProcessor:
    @staticmethod
    def execute(input_path, execute_code=True):
        """Generate and optionally execute query code with schema awareness"""
        global INDENT
        if not USE_EXTENDED_MODE:
            INDENT = ""
        
        # db connect
        db_params = {
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '1234'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'sales')
        }
        
        schema = SchemaManager.get_schema_info(db_params)
        
        params = InputParser.extract_parameters(f"{input_path}")
        
        # Check if this is a SQL query
        if 'sql_query' in params:
            code_body = SqlQueryGenerator.generate_sql_query_code(params['sql_query'])
        else:
            # Process as EMF query
            predicates = PredicateManager.create_default_grouping_predicate(params)
            code_body = CodeGenerator.generate_query_structure(
                params['s'], params['n'], params["v"], params["f"], predicates, params["g"], schema
            )
        
        generated_code = f"""
import os
import psycopg2
import psycopg2.extras
from prettytable import PrettyTable
from dotenv import load_dotenv

# DO NOT EDIT THIS FILE, IT IS GENERATED BY generator.py


def query():
    load_dotenv()

    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '1234')
    dbname = os.getenv('DB_NAME', 'sales')

    conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+password,
                            cursor_factory=psycopg2.extras.DictCursor, host='127.0.0.1', port='5432')
    cur = conn.cursor()
    
    # For EMF queries, we need the whole sales table
    if not '{input_path}'.endswith('.sql'):
        cur.execute("SELECT * FROM sales")

    _global = []
    {code_body}

if "__main__" == __name__:
    print(query())
    """
        
        # Determine output directory based on query type
        if 'sql_query' in params:
            output_dir = "sql-outputs"
        else:
            output_dir = "emf-outputs" if USE_EXTENDED_MODE else "mf-outputs"
            
        output_file = f"{basename(input_path.split('.')[0])}_generated.py"
        full_path = join(output_dir, output_file)
        
        if not exists(output_dir):
            makedirs(output_dir)
        
        try:
            with open(full_path, "w") as file:
                file.write(generated_code)
            Logger.output(LOGGER_PREFIX, f"Generated code saved to '{full_path}'")
        except Exception as error:
            Logger.output(LOGGER_PREFIX, f"Error while writing the generated python code to _generated.py: {error}", True)
            exit(1)
        
        if execute_code:
            try:
                Logger.output(LOGGER_PREFIX, f"Executing generated code: python {full_path}")
                subprocess.run(["python", full_path])
                Logger.output(LOGGER_PREFIX, f"Execution of '{full_path}' completed.")
            except FileNotFoundError:
                Logger.output(LOGGER_PREFIX, "Python interpreter not found. Ensure Python is installed and in your system's PATH.", True)
                exit(1)


class Application:
    @staticmethod
    def run():
        global USE_EXTENDED_MODE  
        
        if len(argv) == 1:
            Logger.output(LOGGER_PREFIX, "Usage: python generator.py input_file_path|user [dont-run?] [mf?]", True)
            Logger.output(LOGGER_PREFIX, "Input path or 'user' is required", True)
            exit(1)
        elif len(argv) == 2:
            if argv[1] == "user":
                # Interactive mode - get parameters from user
                params = InputParser.get_parameters_from_user()
                predicates = PredicateManager.create_default_grouping_predicate(params)
                
                # Generate a temporary file name for the output
                temp_file = "user_query.txt"
                
                # Process the user input
                db_params = {
                    'user': os.getenv('DB_USER', 'postgres'),
                    'password': os.getenv('DB_PASSWORD', '1234'),
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': os.getenv('DB_PORT', '5432'),
                    'database': os.getenv('DB_NAME', 'sales')
                }
                
                schema = SchemaManager.get_schema_info(db_params)
                
                code_body = CodeGenerator.generate_query_structure(
                    params['s'], params['n'], params["v"], params["f"], predicates, params["g"], schema
                )
                
                # Create the output directory if it doesn't exist
                output_dir = "emf-outputs" if USE_EXTENDED_MODE else "mf-outputs"
                if not exists(output_dir):
                    makedirs(output_dir)
                
                # Generate the Python code
                generated_code = f"""
import os
import psycopg2
import psycopg2.extras
from prettytable import PrettyTable
from dotenv import load_dotenv

# DO NOT EDIT THIS FILE, IT IS GENERATED BY generator.py

def query():
    load_dotenv()

    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', '1234')
    dbname = os.getenv('DB_NAME', 'sales')

    conn = psycopg2.connect("dbname="+dbname+" user="+user+" password="+password,
                            cursor_factory=psycopg2.extras.DictCursor, host='127.0.0.1', port='5432')
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales")

    _global = []
    {code_body}

if "__main__" == __name__:
    print(query())
"""
                
                # Write and execute the generated code
                output_file = "user_query_generated.py"
                full_path = join(output_dir, output_file)
                
                try:
                    with open(full_path, "w") as file:
                        file.write(generated_code)
                    Logger.output(LOGGER_PREFIX, f"Generated code saved to '{full_path}'")
                    
                    # Execute the generated code
                    Logger.output(LOGGER_PREFIX, f"Executing generated code: python {full_path}")
                    subprocess.run(["python", full_path])
                    Logger.output(LOGGER_PREFIX, f"Execution of '{full_path}' completed.")
                except Exception as error:
                    Logger.output(LOGGER_PREFIX, f"Error: {error}", True)
                    exit(1)
                    
                exit(0)
            else:
                # Normal mode - process input file
                QueryProcessor.execute(argv[1])
                exit(0)
        elif len(argv) == 3:
            if argv[2] == "dont-run":
                QueryProcessor.execute(argv[1], False)
                exit(0)
            elif argv[2] == "mf":
                USE_EXTENDED_MODE = False
                QueryProcessor.execute(argv[1])
                exit(0)
            elif argv[2] == "sql":
                # Ensure the input file is treated as SQL even without .sql extension
                input_path = argv[1]
                with open(input_path, 'r') as file:
                    sql_content = file.read()
                
                sql_path = f"{input_path}.sql"
                with open(sql_path, 'w') as file:
                    file.write(sql_content)
                
                QueryProcessor.execute(sql_path)
                exit(0)
            Logger.output(LOGGER_PREFIX, f"Usage: python generator.py input_file [dont-run?|mf|sql]", True)
            exit(1)
        elif len(argv) == 4:
            if argv[3] == "mf" and argv[2] == "dont-run":
                USE_EXTENDED_MODE = False
                QueryProcessor.execute(argv[1], False)
                exit(0)
            Logger.output(LOGGER_PREFIX, f"Usage: python generator.py input_file [dont-run?] [mf?]", True)
            exit(1)


if "__main__" == __name__:
    Application.run()
