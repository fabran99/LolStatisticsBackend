from django.core.management.base import BaseCommand, CommandError
import os
from time import sleep

from stats.get_matches import get_matches_sample_from_player_list


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("server", nargs="+", type=str)

    def handle(self, *args, **options):
        server = options['server'][0]
        while True:
            try:
                get_matches_sample_from_player_list(server)
                sleep(3600 * 8)
            except Exception as e:
                print(e)
