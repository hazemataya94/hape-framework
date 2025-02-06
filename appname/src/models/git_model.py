from appname.src.helpers.git_helper import GitHelper

class GitModel:
    def __init__(self):
        self._git_helper = GitHelper()
    
    def clone_project_in_group(self, dir, group_id):
        self._git_helper.clone_all_projects(group_id, dir)
    
    def get_repositories(self, dir, prefix):
        return self._git_helper.get_git_repositories(dir, prefix)
    
    def git_has_changes(self, repo):
        return self._git_helper.git_has_changes(repo)
    
    def git_branch_name(self, repo):
        return self._git_helper.git_branch_name(repo)
    
    def commit_and_push(self, repo, message):
        if self.git_has_changes(repo):
            branch_name = self.git_branch_name(repo)
            self._git_helper.git_pull(repo, branch_name)
            self._git_helper.git_add(repo)
            self._git_helper.git_commit(repo, message)
            self._git_helper.git_push(repo, branch_name)
            return True
        return False
    
    def pull_project(self, repo):
        branch_name = self.git_branch_name(repo)
        self._git_helper.git_pull(repo, branch_name)