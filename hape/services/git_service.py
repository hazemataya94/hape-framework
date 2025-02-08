import subprocess
from dotenv import load_dotenv
import os
import requests
from hape.config import Config

class GitService:
    
    def __init__(self):
        self.dry_run = False
        self.gitlab_token = Config.get_gitlab_token()
        gitlab_domain = Config.get_gitlab_domain()
        self.gitlab_url = f"https://{gitlab_domain}"

    def git_branch_name(self, repo_dir):
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to determine the current branch in {repo_dir}: {result.stderr}")
        return result.stdout.strip()

    def git_pull(self, repo_dir, branch_name):
        print(f"$ git pull origin {branch_name}")
        if not self.dry_run:
            subprocess.run(['git', 'pull', 'origin', branch_name], cwd=repo_dir, check=True)

    def git_has_changes(self, repo_dir):
        result = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_dir, capture_output=True, text=True)
        if result.stdout:
            return True
        else:
            return False

    def git_add(self, repo_dir):
        print(f"$ git add .")
        if not self.dry_run:
            subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
        
    def git_review_and_commit(self, repo_dir):
        print("review and commit")
        if not self.dry_run:
            subprocess.run(['git-cola'], cwd=repo_dir, check=True)
    
    def git_commit(self, repo_dir, commit_message):
        print(f"commit changes, message '{commit_message}'")
        if not self.dry_run:
            subprocess.run(['git', 'commit', '-am', commit_message], cwd=repo_dir, check=True)

    def git_push(self, repo_dir, branch_name = None):
        if not branch_name:
            branch_name = self.git_branch_name(repo_dir)
        print(f"$ git push origin {branch_name}")
        if not self.dry_run:
            subprocess.run(['git', 'push', 'origin', branch_name], cwd=repo_dir, check=True)
    
    def git_clone(self, clone_url, project_path):
        print(f"$ git clone {clone_url} {project_path}")
        subprocess.run(['git', 'clone', clone_url, project_path], check=True)
        
    def get_projects_in_group(self, group_id):
        headers = {'Private-Token': self.gitlab_token}
        page = 1
        all_projects = []
        while True:
            projects_url = f"{self.gitlab_url}/api/v4/groups/{group_id}/projects"
            params = {'include_subgroups': 'true', 'archived': 'false', 'simple': 'true', 'per_page': '100', 'page': page}
            response = requests.get(projects_url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch projects: {response.json().get('message', 'No error message')}")
            projects = response.json()
            if not projects:
                break  # Break the loop if no more projects are returned
            
            all_projects = all_projects + projects
            page += 1

        return all_projects
    
    def get_all_projects(self):
        headers = {'Private-Token': self.gitlab_token}
        page = 1
        all_projects = []
        while True:
            projects_url = f"{self.gitlab_url}/api/v4/projects"
            params = {'include_subgroups': 'true', 'archived': 'false', 'simple': 'true', 'per_page': '100', 'page': page}
            response = requests.get(projects_url, headers=headers, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to fetch projects: {response.json().get('message', 'No error message')}")
            projects = response.json()
            if not projects:
                break  # Break the loop if no more projects are returned
            
            all_projects = all_projects + projects
            page += 1

        return all_projects
            
    def clone_all_projects(self, group_id, clone_dir):
        projects = self.get_projects_in_group(group_id)
        for project in projects:
            clone_url = project['ssh_url_to_repo']
            project_path = os.path.join(clone_dir, project['path_with_namespace'])
            if not os.path.exists(project_path):
                print(f"Cloning {project['name']}...")
                self.git_clone(clone_url, project_path)
            else:
                print(f"{project_path} already exists in {clone_dir}. Skipping clone.")

    def get_git_repositories(self, dir, prefix, recursive=True):
        subdirectories = []
        if recursive:
            for root, dirs, _ in os.walk(dir):
                for subdir in sorted(dirs):
                    full_path = os.path.join(root, subdir)
                    if os.path.isdir(full_path) and \
                       os.path.exists(os.path.join(full_path, ".git")):
                        if prefix and subdir.startswith(prefix):
                            subdirectories.append(full_path)
                        else:
                            subdirectories.append(full_path)
        else:
            subdirectories = [
                os.path.join(dir, subdir) for subdir in sorted(os.listdir(dir))
                if subdir.startswith(prefix) and \
                    os.path.isdir(os.path.join(dir, subdir)) and \
                    os.path.exists(os.path.join(dir, subdir, ".git"))
                ]
        return subdirectories