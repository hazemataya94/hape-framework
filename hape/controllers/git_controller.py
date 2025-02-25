import json
from hape.models.git_model import GitModel
from hape.logging import Logging

class GitController:
    def __init__(self):
        self.logger = Logging.get_logger('hape.controllers.git_controller')
        self.git_model = GitModel()
    
    def clone_project_in_group(self, dir, group_id):
        self.logger.debug(f"clone_project_in_group(dir: {dir}, group_id: {group_id})")
        return self.git_model.clone_project_in_group(dir, group_id)
    
    def commit_projects(self, dir, message, prefix):
        self.logger.debug(f"commit_projects(dir: {dir}, message: {message}, prefix: {prefix})")
        repos = self.git_model.get_repositories(dir, prefix)
        
        print("The following projects will be committed and pushed:")
        print(json.dumps(repos, indent=2))
        print(f"Total number of affected projects: {len(repos)}")
        
        user_input = input("Do you want to continue? (y/n): ").strip().lower()
        if user_input != "y":
            print("Aborting task...")
            return
        
        for repo in repos:
            print("==============================")
            print(f"Directory: {repo}")
            if self.git_model.commit_and_push(repo, message):
                print("Changes committed and pushed successfully.")
            else:
                print("No changes to commit.")
    
    def pull_projects(self, dir, prefix):
        self.logger.debug(f"pull_projects(dir: {dir}, prefix: {prefix})")
        repos = self.git_model.get_repositories(dir, prefix)
        
        print("The following projects will be pulled:")
        print(json.dumps(repos, indent=2))
        print(f"Total number of affected projects: {len(repos)}")
        
        for repo in repos:
            print("==============================")
            print(f"Directory: {repo}")
            self.git_model.pull_project(repo)
            print("Repository updated successfully.")
