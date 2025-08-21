import os
import re
import shutil
from pathlib import Path

def parse_datalog_file(dl_path):
    """Parse a datalog file into declarations, rules, and facts."""
    with open(dl_path, 'r') as f:
        content = f.read()
    
    # Split content into lines
    lines = content.split('\n')
    
    declarations = []
    rules = []
    facts = []
    
    current_item = ""
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith('//'):
            continue
        
        # Handle declaration lines (starting with .)
        if line_stripped.startswith('.'):
            # If we have a current item being accumulated, add it to the appropriate list
            if current_item:
                if ':-' in current_item:
                    rules.append(current_item.strip())
                else:
                    facts.append(current_item.strip())
                current_item = ""
            
            # Add the declaration line as a separate item
            declarations.append(line_stripped)
            continue
        
        # For non-declaration lines, accumulate until we find a complete item
        current_item += line + "\n"
        
        # Check if the item is complete (ends with a period)
        if line_stripped.endswith('.'):
            if ':-' in current_item:
                rules.append(current_item.strip())
            else:
                facts.append(current_item.strip())
            current_item = ""
    
    # Handle any remaining item
    if current_item.strip():
        if ':-' in current_item:
            rules.append(current_item.strip())
        else:
            facts.append(current_item.strip())
    
    return declarations, rules, facts
    
def parse_declarations(declarations):
    """Extract relation names from declarations."""
    relation_names = []
    for decl in declarations:
        # Split the declaration by whitespace and look for .decl
        parts = decl.split()
        if len(parts) >= 2 and parts[0] == '.decl':
            # The second part should be the relation name with parameters
            relation_part = parts[1]
            # Extract just the name (before the opening parenthesis)
            if '(' in relation_part:
                relation_name = relation_part.split('(')[0]
                relation_names.append(relation_name)

    return relation_names

def parse_probability_file(prob_path):
    """Parse the probability file to extract fact and rule probabilities."""
    fact_probs = {}  # {(relation, tuple_of_args): prob}
    rule_probs = {}  # {(head_relation, body_relations): prob}
    
    with open(prob_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(';')
            if len(parts) < 4:
                continue
            
            kind = parts[0]
            
            if kind == 'relation':
                # Format: relation;RelationName;args;probability;ignored
                relation = parts[1]
                args_str = parts[2]
                prob = float(parts[3])
                
                # Split args by comma and create a tuple
                args_tuple = tuple(args_str.split(','))
                
                fact_probs[(relation, args_tuple)] = prob
            
            elif kind == 'rule':
                # Format: rule;HeadRelation;BodyRelations;probability
                head_relation = parts[1]
                body_relations = parts[2]
                prob = float(parts[3])
                
                rule_probs[(head_relation, body_relations)] = prob
    
    return fact_probs, rule_probs

def extract_fact_parts(fact):
    """Extract relation name and arguments from a fact."""
    # Remove trailing period and whitespace
    clean_fact = fact.rstrip('.').strip()
    
    # Extract relation name and arguments
    match = re.match(r'(\w+)\((.*?)\)', clean_fact)
    if match:
        relation = match.group(1)
        args_str = match.group(2)
        
        # Split args by comma and create a tuple
        args_tuple = tuple(arg.strip() for arg in args_str.split(','))
        
        return relation, args_tuple
    
    return None, None

def get_head_relation(rule):
    """Extract the head relation from a rule."""
    if ':-' not in rule:
        return None
    
    head_part = rule.split(':-')[0].strip()
    match = re.match(r'(\w+)\(', head_part)
    if match:
        return match.group(1)
    
    return None

def get_body_relations(rule):
    """Extract the body relations from a rule."""
    if ':-' not in rule:
        return []
    
    body_part = rule.split(':-')[1].strip().rstrip('.')
    relations = []
    
    # Find all relation names in the body
    for match in re.finditer(r'(\w+)\(', body_part):
        relation = match.group(1)
        relations.append(relation)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_relations = [r for r in relations if not (r in seen or seen.add(r))]
    
    return unique_relations

def match_rule_probability(rule, rule_probs):
    """Match a rule to its probability from the rule_probs dictionary."""
    head_relation = get_head_relation(rule)
    if not head_relation:
        return None
    
    body_relations = get_body_relations(rule)
    
    # Try to match with rule probabilities
    for (hr, br_str), prob in rule_probs.items():
        if hr == head_relation:
            br_parts = set(br_str.split(','))
            if br_parts == set(body_relations):
                return prob
    
    return None

def convert_to_problog_syntax(text):
    """
    Convert text to ProBlog syntax:
    1. Convert all relation names to lowercase
    2. Convert all variables to UPPERCASE
    3. Convert negation from ! to \+
    """
    # Step 1: Convert relation names to lowercase
    text = re.sub(r'(\b[A-Z_][A-Za-z0-9_]*)\(', lambda m: m.group(1).lower() + '(', text)
    
    # Step 2: Identify and convert variables to uppercase
    # Common Souffle variable naming patterns
    variable_patterns = [
        r'\bvar_[a-z0-9_]+\b',  # var_x, var_y, var_z, etc.
        r'\bfrom\d*\b',         # from, from1, from2, etc.
        r'\bto\d*\b',           # to, to1, to2, etc.
        r'\bprev\b',            # prev
        r'\bint_res\d+\b',      # int_res0, int_res1, etc.
        r'\bXY\w*\b',           # XY, XY_past, etc.
        r'\bTimes\w*\b',        # Times, Times_New, etc.
        r'\bX\b|\bY\b',         # X, Y (single letter variables)
        r'\bX_[A-Za-z]+\b',     # X_R, X_A, etc.
        r'\bY_[A-Za-z]+\b',     # Y_R, Y_A, etc.
        r'\btmp\b',             # tmp
        r'\bargs\b',            # args
        r'\bhead\b',            # head
        r'\bbody\b'             # body
    ]
    
    # Combine all patterns with OR (|)
    combined_pattern = '|'.join(variable_patterns)
    
    # Replace all variables with uppercase versions
    text = re.sub(combined_pattern, lambda m: m.group(0).upper(), text)
    
    # Step 3: Replace negation
    text = text.replace('!', '\\+')
    
    return text

def deduplicate_rules(rules):
    """Deduplicate rules based on their string representation."""
    return rules
    # seen = set()
    # unique_rules = []
    
    # for rule in rules:
    #     head = get_head_relation(rule)
    #     body = get_body_relations(rule)
    #     id = f"{head}:-{','.join(body)}"
    #     if id not in seen:
    #         seen.add(id)
    #         unique_rules.append(rule)
    
    # return unique_rules

def process_benchmark(folder_path):
    """Process a benchmark folder to generate souffle and problog versions."""
    dl_path = os.path.join(folder_path, 'compute.dl')
    prob_path = os.path.join(folder_path, 'probability-oopsla.txt')
    
    # Check if files exist
    if not os.path.exists(dl_path) or not os.path.exists(prob_path):
        print(f"Required files not found in {folder_path}")
        return
    
    # Create output paths
    souffle_dl_path = os.path.join(folder_path, 'compute.souffle.dl')
    problog_dl_path = os.path.join(folder_path, 'compute.problog.dl')
    input_dir = os.path.join(folder_path, 'input')
    output_dir = os.path.join(folder_path, 'output')
    
    # Create input directory if it doesn't exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse input files
    declarations, rules, facts = parse_datalog_file(dl_path)
    rules = deduplicate_rules(rules)
    fact_probs, rule_probs = parse_probability_file(prob_path)
    
    # Extract relation names from declarations
    relation_names = parse_declarations(declarations)
    # Generate fact files for souffle and track which relations have facts
    relation_facts = {}
    relation_probs = {}
    relations_with_facts = set()
    


    for fact in facts:
        relation, args_tuple = extract_fact_parts(fact)
        if not relation or not args_tuple:
            continue
        
        if relation not in relation_facts:
            relation_facts[relation] = []
            relation_probs[relation] = []
        
        relation_facts[relation].append(args_tuple)
        relations_with_facts.add(relation)
        
        # Get probability for this fact
        prob = 1.0  # Default probability
        if (relation, args_tuple) in fact_probs:
            prob = fact_probs[(relation, args_tuple)]
        
        relation_probs[relation].append(prob)
    
    # Write fact files
    for relation in relation_names:
        facts_file = os.path.join(input_dir, f"{relation}.facts")
        probs_file = os.path.join(input_dir, f"{relation}.prob")
        
        with open(facts_file, 'w') as f_facts, open(probs_file, 'w') as f_probs:
            if relation not in relation_facts or len(relation_facts[relation]) == 0:
                continue

            for i, args_tuple in enumerate(relation_facts[relation]):
                # Write arguments separated by tabs
                f_facts.write('\t'.join(args_tuple) + '\n')
                
                # Write probability
                f_probs.write(f"{relation_probs[relation][i]}\n")
    
    # Generate souffle version

    with open(souffle_dl_path, 'w') as f:
        for decl in declarations:
            f.write(decl + '\n')

        for rel in relation_names:
            if rel in ["KEY_SENSITIVE", "KEY_IND"]:
                f.write(f".input {rel}\n")
                f.write(f".output {rel}\n")
            elif rel in relations_with_facts \
                or rel.startswith('BV') or rel in ["RAND"]:
                f.write(f".input {rel}\n")
            else:
                # intermediate relations
                # if rel in ["equal_assign", "assign"]:
                    # f.write(f".output {rel}\n")
                    # pass
                pass
        f.write('\n')
        
        # Write rules (excluding those with head starting with "BV")
        for rule in rules:
            head_relation = get_head_relation(rule)
            
            # Skip rules with head starting with "BV"
            if head_relation and head_relation.startswith('BV'):
                continue
            
            # Check if rule has a probability
            prob = match_rule_probability(rule, rule_probs)
            
            if prob is not None and prob == 0.0:
                continue 
            elif prob is not None and prob < 1.0:
                f.write(f"{prob}::{rule}\n")
            else:
                f.write(rule + '\n')
    
    # Generate problog version
    with open(problog_dl_path, 'w') as f:
        # Write facts with probabilities
        for fact in facts:
            relation, args_tuple = extract_fact_parts(fact)
            if not relation or not args_tuple:
                continue
            
            # Check for probability
            prob = 1.0  # Default probability
            if (relation, args_tuple) in fact_probs:
                prob = fact_probs[(relation, args_tuple)]
            
            # Convert to ProBlog syntax
            problog_fact = convert_to_problog_syntax(fact)
            
            if prob < 1.0:
                f.write(f"{prob}::{problog_fact}\n")
            else:
                f.write(problog_fact + '\n')
        
        f.write('\n')
        
        # Write rules (excluding those with head starting with "BV" and declarations)
        for rule in rules:
            head_relation = get_head_relation(rule)
            
            # Skip rules with head starting with "BV" or declarations
            if (head_relation and head_relation.startswith('BV')) or rule.startswith('.'):
                continue
            
            # Convert to ProBlog syntax
            problog_rule = convert_to_problog_syntax(rule)
            
            # Check if rule has a probability
            prob = match_rule_probability(rule, rule_probs)
            
            if prob is not None and prob < 1.0:
                if prob == 0.0:
                    continue
                f.write(f"{prob}::{problog_rule}\n")
            else:
                f.write(problog_rule + '\n')
        
        # Add the query for KEY_SENSITIVE at the end (lowercase version)
        f.write('\nquery(key_sensitive(_)).\n')
        f.write('\nquery(key_ind(_)).\n')

def clean_generated_files(base_dir="side_channel_benchmarks"):
    """
    Remove all generated files from the benchmark folders.
    
    This function:
    1. Finds all benchmark folders (P1, P3-P19)
    2. Removes the generated Souffle and ProBlog files
    3. Removes the input directory and all its contents from each folder
    
    Args:
        base_dir (str): The base directory containing the benchmark folders
    
    Returns:
        dict: A summary of what was removed
    """
    # Initialize counters for reporting
    summary = {
        "folders_processed": 0,
        "souffle_files_removed": 0,
        "problog_files_removed": 0,
        "input_dirs_removed": 0
    }
    
    # Find all benchmark folders (P1, P3-P19)
    folders = []
    for i in [1] + list(range(3, 20)):  # P1, P3-P19
        folder = f"P{i}"
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            folders.append(folder_path)
    
    for folder in sorted(folders):
        print(f"Cleaning up {folder}...")
        summary["folders_processed"] += 1
        
        # Remove generated Souffle file
        souffle_file = os.path.join(folder, "compute.souffle.dl")
        if os.path.exists(souffle_file):
            os.remove(souffle_file)
            summary["souffle_files_removed"] += 1
            print(f"  Removed {souffle_file}")
        
        # Remove generated ProBlog file
        problog_file = os.path.join(folder, "compute.problog.dl")
        if os.path.exists(problog_file):
            os.remove(problog_file)
            summary["problog_files_removed"] += 1
            print(f"  Removed {problog_file}")
        
        # Remove input directory and all its contents
        input_dir = os.path.join(folder, "input")
        if os.path.exists(input_dir):
            shutil.rmtree(input_dir)
            summary["input_dirs_removed"] += 1
            print(f"  Removed {input_dir} directory")
    
    # Print summary
    print("\nCleanup Summary:")
    print(f"Folders processed: {summary['folders_processed']}")
    print(f"Souffle files removed: {summary['souffle_files_removed']}")
    print(f"ProBlog files removed: {summary['problog_files_removed']}")
    print(f"Input directories removed: {summary['input_dirs_removed']}")
    
    return summary

import argparse

def main():
    """Main function to process benchmark directories."""
    parser = argparse.ArgumentParser(description="Preprocess benchmark directories.")
    parser.add_argument('--dir', type=str, help="Process only this specific directory (e.g., P5 or ./P5)")
    args = parser.parse_args()

    if args.dir:
        dir_path = os.path.abspath(args.dir)
        if not os.path.isdir(dir_path):
            print(f"Specified directory {dir_path} does not exist.")
            return
        print(f"Processing specified directory: {dir_path}")
        try:
            process_benchmark(dir_path)
            print(f"Finished processing {dir_path}.")
        except Exception as e:
            print(f"Error processing {dir_path}: {e}")
    else:
        # Use the directory containing this script as the base_dir
        base_dir = os.path.dirname(os.path.abspath(__file__))
        clean_generated_files(base_dir=base_dir)
        folders = []
        for i in [1] + list(range(3, 20)):
            folder = f"P{i}"
            folder_path = os.path.join(base_dir, folder)
            if os.path.isdir(folder_path):
                folders.append(folder_path)

        for folder_path in sorted(folders):
            print(f"Processing {folder_path}...")
            try:
                process_benchmark(folder_path)
                print(f"Finished processing {folder_path}.")
            except Exception as e:
                print(f"Error processing {folder_path}: {e}")

        print("All benchmarks processed successfully!")

import os
import shutil
from pathlib import Path

def clean_generated_files(base_dir="."):
    """
    Remove all generated files from the benchmark folders.
    
    This function:
    1. Finds all benchmark folders (P1, P3-P19)
    2. Removes the generated Souffle and ProBlog files
    3. Removes the input directory and all its contents from each folder
    
    Args:
        base_dir (str): The base directory containing the benchmark folders
    
    Returns:
        dict: A summary of what was removed
    """
    # Initialize counters for reporting
    summary = {
        "folders_processed": 0,
        "souffle_files_removed": 0,
        "problog_files_removed": 0,
        "input_dirs_removed": 0
    }
    
    # Find all benchmark folders (P1, P3-P19)
    folders = []
    for i in [1] + list(range(3, 20)):  # P1, P3-P19
        folder = f"P{i}"
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            folders.append(folder_path)
    
    for folder in sorted(folders):
        print(f"Cleaning up {folder}...")
        summary["folders_processed"] += 1
        
        # Remove generated Souffle file
        souffle_file = os.path.join(folder, "compute.souffle.dl")
        if os.path.exists(souffle_file):
            os.remove(souffle_file)
            summary["souffle_files_removed"] += 1
            print(f"  Removed {souffle_file}")
        
        # Remove generated ProBlog file
        problog_file = os.path.join(folder, "compute.problog.dl")
        if os.path.exists(problog_file):
            os.remove(problog_file)
            summary["problog_files_removed"] += 1
            print(f"  Removed {problog_file}")
        
        # Remove input directory and all its contents
        input_dir = os.path.join(folder, "input")
        if os.path.exists(input_dir):
            shutil.rmtree(input_dir)
            summary["input_dirs_removed"] += 1
            print(f"  Removed {input_dir} directory")
    
    # Print summary
    print("\nCleanup Summary:")
    print(f"Folders processed: {summary['folders_processed']}")
    print(f"Souffle files removed: {summary['souffle_files_removed']}")
    print(f"ProBlog files removed: {summary['problog_files_removed']}")
    print(f"Input directories removed: {summary['input_dirs_removed']}")
    
    return summary

if __name__ == "__main__":
    main()