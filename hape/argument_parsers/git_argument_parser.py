from hape.logging import Logging
from hape.controllers.git_controller import GitController

class GitArgumentParser:

    def __init__(self):
        self.logger = Logging.get_logger('hape.argument_parsers.git_argument_parser')

    def create_subparser(self, subparsers):    
        self.logger.debug(f"create_subparser(subparsers)")
        git_parser = subparsers.add_parser("git", help="Commands related to git")
        git_parser_subparser = git_parser.add_subparsers(dest="action")

        clone_parser = git_parser_subparser.add_parser("clone", help="Clone all projects in the specified group")
        clone_parser.add_argument("-d", "--dir", required=True, help="Directory where projects will be cloned")
        clone_parser.add_argument("-g", "--group-id", required=True, type=int, help="GitLab group ID.")

        commit_parser = git_parser_subparser.add_parser("commit", help="Commit the git repositories in the specified directory")
        commit_parser.add_argument("-d", "--dir", required=True, help="Directory where projects will be committed")
        commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
        commit_parser.add_argument("-p", "--prefix", required=False, help="A prefix for the project names", default='cicd-')

        pull_parser = git_parser_subparser.add_parser("pull", help="Pull and update the git repositories in the specified directory using the already checked out branch")
        pull_parser.add_argument("-d", "--dir", required=True, help="Directory where projects will be pulled")
        pull_parser.add_argument("-p", "--prefix", required=False, help="A prefix for the project names", default='')

    def run_action(self, args):
        self.logger.debug(f"run_action(args)")
        if args.command != "git":
            return
        
        controller = GitController()

        if args.action == "clone":
            controller.clone_project_in_group(args.dir, args.group_id)
        elif args.action == "commit":
            controller.commit_projects(args.dir, args.message, args.prefix)
        elif args.action == "pull":
            controller.pull_projects(args.dir, args.prefix)
        else:
            self.logger.error(f"Error: Invalid action {args.action} for {args.command}. Use `hape {args.command} --help` for more details.")
            exit(1)
