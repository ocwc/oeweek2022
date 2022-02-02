from django.core.management.base import BaseCommand
import xlrd

from web.importer import import_submission


class Command(BaseCommand):
    help = "Imports resources"

    def handle(self, *args, **options):
        wb = xlrd.open_workbook('OEA2OEW.xlsx')
        sheet = wb.sheet_by_index(0)

        for row_idx in range(3, sheet.nrows):
            if sheet.cell(row_idx, 0).value:
                firstname = sheet.cell(row_idx, 1).value
                lastname = sheet.cell(row_idx, 2).value
                email = sheet.cell(row_idx, 3).value
                institution = sheet.cell(row_idx, 4).value
                country = sheet.cell(row_idx, 6).value
                city = sheet.cell(row_idx, 7).value
                title = sheet.cell(row_idx, 8).value
                desc = sheet.cell(row_idx, 9).value
                link = sheet.cell(row_idx, 10).value
                license = sheet.cell(row_idx, 11).value
                language = sheet.cell(row_idx, 12).value
                tags = sheet.cell(row_idx, 13).value

                data = {
                    "email": email,
                    "city": city,
                    "title": title,
                    "license": license,
                    "lastname": lastname,
                    "language": language,
                    "firstname": firstname,
                    "country": country,
                    "description": desc,
                    "link": link,
                    "contributiontype": "resource",
                    "institution": institution,
                    "datetime": "2018-03-08T09:00:00.000Z",
                    "opentags": tags,
                    # "opentags": [
                    #     tags
                    # ]
                }

                import_submission(data)
