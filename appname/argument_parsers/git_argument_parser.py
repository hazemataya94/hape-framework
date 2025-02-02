from appname.src.controllers.git_controller import GitController

class GitArgumentParser:

    def create_subparser(self, subparsers):    
        git_parser = subparsers.add_parser("git", help="Commands related to git")
        
        git_parser_subparser = git_parser.add_subparsers(dest="action")

        clone_parser = git_parser_subparser.add_parser("clone", help="Clone all projects in the specified group")
        clone_parser.add_argument("-d", "--dir", required=True, help="Directory where projects will be cloned")
        clone_parser.add_argument("-g", "--group-id", required=True, type=int,
                                help="GitLab group ID.")
                                

        commit_parser = git_parser_subparser.add_parser("commit", help="Commit the git repositories in the specified directory")
        commit_parser.add_argument("-d", "--dir", required=True, help="Directory where projects will be committed")
        commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
        commit_parser.add_argument("-p", "--prefix", required=False, help="A prefix for the project names", default='cicd-')


        pull_parser = git_parser_subparser.add_parser("pull", help="Pull and update the git repositories in the specified directory using the already checked out branch")
        pull_parser.add_argument("-d", "--dir", required=True, help="Directory where projects will be pulled")
        pull_parser.add_argument("-p", "--prefix", required=False, help="A prefix for the project names", default='cicd-')


    def run_action(self, args):
        if args.command != "git":
            return
        
        if args.action == "clone":
            GitController.clone_project_in_group(args.dir, args.group_id)
        elif args.command == "commit":
            GitController.commit_projects(args.dir, args.message, args.prefix)
        elif args.command == "pull":
            GitController.pull_projects(args.dir, args.prefix)
        else:
            print(f"Error: Invalid {args.comman} action. Use `appname {args.comman} --help` for more details.")
            exit(1)