import json

from appname.src.helpers.git_helper import GitHelper

class GitController:
    
    @classmethod
    def clone_project_in_group(self, dir, group_id):
        GitHelper().clone_all_projects(group_id, dir)

    @classmethod
    def commit_projects(self, dir, message, prefix):
        git_helper = GitHelper()
        repos = git_helper.get_git_repositories(dir, prefix)

        print("The following projects will be committed and pushed:")
        print(json.dumps(repos, indent=2))
        print(f"Total number of affected projects: {len(repos)}")

        user_input = input("Do you want to continue? (y/n): ").strip().lower()
        if user_input != "y":
            print("Aborting task...")
            return

        for repo in repos:
            print("===============================")
            print(f"Directory: {repo}")
            if git_helper.git_has_changes(repo):
                branch_name = git_helper.git_branch_name(repo)
                print(f"Branch: {branch_name}")
                print(f"---")
                git_helper.git_pull(repo, branch_name)
                git_helper.git_add(repo)
                git_helper.git_commit(repo, message)
                git_helper.git_push(repo, branch_name)
            else:
                print("No changes detected.")

    @classmethod
    def pull_projects(self, dir, prefix):
        git_helper = GitHelper()
        repos = git_helper.get_git_repositories(dir, prefix)

        for repo in repos:
            print("===============================")
            print(f"Directory: {repo}")
            branch_name = git_helper.git_branch_name(repo)
            print(f"Branch: {branch_name}")
            print(f"---")
            git_helper.git_pull(repo, branch_name)
    
