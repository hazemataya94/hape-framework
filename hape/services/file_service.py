import os
import sys
from ruamel.yaml import YAML
import csv

class FileService():
    def __init__(self):
        self.yaml = YAML()
        self.yaml.width = sys.maxsize
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)

    def write_file(self, file_path, content):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def read_file(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'r', encoding='utf-8') as source_file:
            content = source_file.read()
        return content

    def read_yaml_file(self, yaml_path):
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Error: file {yaml_path} does not exist")
        with open(yaml_path, 'r',  encoding='utf-8') as file:
            data = self.yaml.load(file)
        return data
    
    def write_yaml_file(self, yaml_path, data):
        with open(yaml_path, 'w') as file:
            self.yaml.dump(data, file)

    def append_to_file(self, file_path, content):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'a', encoding='utf-8') as destination_file:
            destination_file.write(content)
    
    def prepend_to_file(self, file_path, content):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content + '\n' + file_content)

    def add_new_line_after_keyword(self, file_path, keyword):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.readlines()
            for i, line in enumerate(content):
                if keyword in line:
                    content.insert(i + 1, '\n')
                    break
            file.seek(0)
            file.writelines(content)
            file.truncate()

    def read_csv_file(self, csv_path):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Error: file {csv_path} does not exist")
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            clean_data = []
            for row in reader:
                clean_row = {key.strip(): value.strip() for key, value in row.items()}
                clean_data.append(clean_row)
            return clean_data
        
    def write_csv_file(self, filename, data):
        if not data:
            print("No data provided to write CSV file.")
            return
        
        fieldnames = list(data[0].keys())
        
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
    def find_files_with_keyword(self, keyword, directory, return_parent_directory=False):
        matching_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if keyword in file:
                    if return_parent_directory:
                        matching_files.append(os.path.dirname(os.path.join(root, file)))
                    else:
                        matching_files.append(os.path.join(root, file))
        return matching_files

    def get_sorted_subdirectories(self, dir_path, prefix):
        subdirectories = sorted(os.listdir(dir_path))
        return [os.path.join(dir_path, subdir) for subdir in subdirectories
                if subdir.startswith(prefix) and os.path.isdir(os.path.join(dir_path, subdir))]
