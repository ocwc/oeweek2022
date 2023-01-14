from django.core.management.base import BaseCommand, CommandError

import web.email_utils as email_utils


class Command(BaseCommand):
    help = "Manage send_email_queue"

    OP_LIST = "list"
    OP_CLEANUP = "clean"
    OP_MR_PROPER = "mrproper"

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[self.OP_LIST, self.OP_CLEANUP, self.OP_MR_PROPER],
            help="list: list; clean: remove old sent entries; mrproper: remove all entries, sent or unsent",
        )
        parser.add_argument(
            "--really-proper",
            action="store_true",
            help="Confirm that we really want to do 'Mr. proper' clean-up",
        )

    def list(self):
        email_utils.list_queue()

    def clean(self):
        email_utils.clean_send_email_queue()

    def mr_proper(self, options):
        if not options["really_proper"]:
            raise CommandError(
                "this will delete all entries in the queue, please use also --really-proper argument to confirm that it is desired"
            )
        email_utils.mrproper()

    def handle(self, *args, **options):
        operation = options["operation"]
        if operation == self.OP_MR_PROPER:
            self.mr_proper(options)
        elif operation == self.OP_CLEANUP:
            self.clean()
        elif operation == self.OP_LIST:
            self.list()
        else:
            raise CommandError("unknown operation: %s" % operation)
