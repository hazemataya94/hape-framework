from hape.logging import Logging
from hape.services.git_service import GitService

class GitModel:
    def __init__(self):
        self.logger = Logging.get_logger('hape.models.git_model')
        self._git_service = GitService()
    
    def clone_project_in_group(self, dir, group_id):
        self.logger.debug(f"clone_project_in_group(dir: {dir}, group_id: {group_id})")
        self._git_service.clone_all_projects(group_id, dir)
    
    def get_repositories(self, dir, prefix):
        self.logger.debug(f"get_repositories(dir: {dir}, prefix: {prefix})")
        return self._git_service.get_git_repositories(dir, prefix)
    
    def git_has_changes(self, repo):
        self.logger.debug(f"git_has_changes(repo: {repo})")
        return self._git_service.git_has_changes(repo)
    
    def git_branch_name(self, repo):
        self.logger.debug(f"git_branch_name(repo: {repo})")
        return self._git_service.git_branch_name(repo)
    
    def commit_and_push(self, repo, message):
        self.logger.debug(f"commit_and_push(repo: {repo}, message: {message})")
        if self.git_has_changes(repo):
            branch_name = self.git_branch_name(repo)
            self._git_service.git_pull(repo, branch_name)
            self._git_service.git_add(repo)
            self._git_service.git_commit(repo, message)
            self._git_service.git_push(repo, branch_name)
            return True
        return False
    
    def pull_project(self, repo):
        self.logger.debug(f"pull_project(repo: {repo})")
        branch_name = self.git_branch_name(repo)
        self._git_service.git_pull(repo, branch_name)