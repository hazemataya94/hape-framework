import os
import sys
import shutil
import csv
from ruamel.yaml import YAML
from hape.logging import Logging

class FileService:

    def __init__(self):
        self.yaml = YAML()
        self.yaml.width = sys.maxsize
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.logger = Logging.get_logger('hape.services.file_service')
        
    def create_directory(self, path: str):
        self.logger.debug(f"create_directory(path: {path})")
        os.makedirs(path, exist_ok=True)
    
    def create_directory(self, path: str):
        self.logger.debug(f"create_directory(path: {path})")
        os.makedirs(path, exist_ok=True)

    def delete_file(self, file_path: str):
        self.logger.debug(f"delete_file(file_path: {file_path})")
        if os.path.exists(file_path):
            os.remove(file_path)
        self.logger.info(f"File '{file_path}' has been removed.")  
        
    def delete_folder(self, folder_path: str):
        self.logger.debug(f"delete_folder(folder_path: {folder_path})")
        self.delete_directory(folder_path)

    def delete_directory(self, directory_path: str):
        self.logger.debug(f"delete_directory(directory_path: {directory_path})")
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            try:
                shutil.rmtree(directory_path)
                self.logger.info(f"Directory '{directory_path}' has been removed.")
            except Exception as e:
                self.logger.error(f"Unable to remove directory '{directory_path}'. {e}")
        else:
            self.logger.warning(f"Directory '{directory_path}' does not exist or is not a directory.")

    def copy_file(self, source: str, destination: str, overwrite: bool):
        self.logger.debug(f"copy_file(source: {source}, destination: {destination}, overwrite: {overwrite})")
        if os.path.exists(source) or overwrite:
            shutil.copy2(source, destination)

    def copy_directory(self, source: str, destination: str):
        self.logger.debug(f"copy_directory(source: {source}, destination: {destination})")
        if os.path.exists(source):
            self.logger.info(f"copying {source} to {destination}")
            shutil.copytree(source, destination, dirs_exist_ok=True)
    
    def file_exists(self, path):
        self.logger.debug(f"path_exists(path: {path})")
        return os.path.exists(path)
    
    def folder_exists(self, path):
        self.logger.debug(f"path_exists(path: {path})")
        return os.path.exists(path)

    def directory_exists(self, path):
        self.logger.debug(f"path_exists(path: {path})")
        return os.path.exists(path)
        
    def path_exists(self, path):
        self.logger.debug(f"path_exists(path: {path})")
        return os.path.exists(path)

    def replace_text_in_file(self, source: str, destination: str, old_text: str, new_text: str):
        self.logger.debug(f"replace_text_in_file(source {source}, destination {destination}, old_text {old_text}, new_text {new_text})")
        if os.path.exists(source):
            with open(source, "r", encoding="utf-8") as src, open(destination, "w", encoding="utf-8") as dest:
                content = src.read().replace(old_text, new_text)
                dest.write(content)

    def write_file(self, file_path, content):
        self.logger.debug(f"write_file(file_path: {file_path}, content)")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def read_file(self, file_path):
        self.logger.debug(f"read_file(file_path: {file_path})")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'r', encoding='utf-8') as source_file:
            content = source_file.read()
        return content

    def read_yaml_file(self, yaml_path):
        self.logger.debug(f"read_yaml_file(yaml_path: {yaml_path})")
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Error: file {yaml_path} does not exist")
        with open(yaml_path, 'r', encoding='utf-8') as file:
            data = self.yaml.load(file)
        return data

    def write_yaml_file(self, yaml_path, data):
        self.logger.debug(f"write_yaml_file(yaml_path: {yaml_path}, data: {data})")
        with open(yaml_path, 'w') as file:
            self.yaml.dump(data, file)

    def append_to_file(self, file_path, content):
        self.logger.debug(f"append_to_file(file_path: {file_path}, content: {content})")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'a', encoding='utf-8') as destination_file:
            destination_file.write(content)

    def prepend_to_file(self, file_path, content):
        self.logger.debug(f"prepend_to_file(file_path: {file_path}, content: {content})")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content + '\n' + file_content)

    def add_string_after_keyword(self, file_path, keyword, string_to_add='\n'):
        self.logger.debug(f"add_string_after_keyword(file_path: {file_path}, keyword: {keyword}, string_to_add: {string_to_add})")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: file {file_path} does not exist")
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.readlines()
            for i, line in enumerate(content):
                if keyword in line:
                    content.insert(i + 1, string_to_add + '\n')
                    break
            file.seek(0)
            file.writelines(content)
            file.truncate()

    def read_csv_file(self, csv_path):
        self.logger.debug(f"read_csv_file(csv_path: {csv_path})")
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
        self.logger.debug(f"write_csv_file(filename: {filename}, data: {data})")
        if not data:
            self.logger.info("No data provided to write CSV file.")
            return

        fieldnames = list(data[0].keys())

        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    def find_files_with_keyword(self, keyword, directory, return_parent_directory=False):
        self.logger.debug(f"find_files_with_keyword(keyword: {keyword}, directory: {directory}, return_parent_directory: {return_parent_directory})")
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
        self.logger.debug(f"get_sorted_subdirectories(dir_path: {dir_path}, prefix: {prefix})")
        subdirectories = sorted(os.listdir(dir_path))
        return [os.path.join(dir_path, subdir) for subdir in subdirectories
                if subdir.startswith(prefix) and os.path.isdir(os.path.join(dir_path, subdir))]
