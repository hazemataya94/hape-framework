from hape.logging import Logging

import re
from typing import List, Optional
from datetime import datetime
from gitlab import Gitlab
from gitlab.v4.objects import Group, Project, GroupProject, ProjectCommit
from hape.hape_config import HapeConfig
from hape.services.file_service import FileService

class GitlabService:
    def __init__(self):
        self.logger = Logging.get_logger('hape.services.gitlab_service')
        gitlab_domain = HapeConfig.get_gitlab_domain()
        gitlab_token = HapeConfig.get_gitlab_token()
        self.client = Gitlab(f"https://{gitlab_domain}", private_token=gitlab_token)
        self._per_page = 100
    
    def _get_project(self, id: int) -> Project:
        return self.client.projects.get(id)
    
    def _get_projects(self, ids: list[int]) -> List[Project]:
        return [self.client.projects.get(id) for id in ids]
    
    def _get_group_projects(self, group_id: int, recursive: bool = False, search: Optional[str] = None) -> List[GroupProject]:
        group: Group = self.client.groups.get(group_id)
        return group.projects.list(get_all=True, per_page=self._per_page, include_subgroups=recursive, search=search)        
    
    def _get_project_commits(self, project: Project, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[ProjectCommit]:
        params = {"get_all": True}
        if start_date:
            params["since"] = start_date.isoformat()
        if end_date:
            params["until"] = end_date.isoformat()
        
        return project.commits.list(**params)
    
    def generate_csv_changes_in_cicd_repos(self, group_id: int, output_file: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, file_regex: Optional[str] = None):
        self.logger.debug(f"generate_csv_changes_in_cicd_repos(group_id: int: {group_id: int}, output_file: str: {output_file: str}, start_date: Optional[datetime] : {start_date: Optional[datetime] }, end_date: Optional[datetime] : {end_date: Optional[datetime] }, file_regex: Optional[str] : {file_regex: Optional[str] })")
        
        group_projects = self._get_group_projects(group_id, recursive=True, search="cicd-")
        project_ids = [project.id for project in group_projects]
        projects = self._get_projects(project_ids)

        all_commits = []
        for project in projects:
            project_path = project.path.replace("cicd-", "")
            commits = self._get_project_commits(project, start_date, end_date)
            for commit in commits:
                if commit.author_name == f"{project_path}-ci":
                    continue

                diff = commit.diff()
                for change in diff:
                    if file_regex and re.match(file_regex, change['new_path']):
                        all_commits.append({
                            "project_name": project.name,
                            "commit_date": commit.committed_date,
                            "commit_author": commit.author_name,
                            "commit": commit.id,
                            "web_url": commit.web_url
                        })

        FileService().write_csv_file(output_file, all_commits)
        print(f"CSV report generated: {output_file}")
