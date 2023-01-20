import csv
import os

input_dir =  'src/datasets/porto/resources/kspd'
output_dir = 'src/datasets/porto/resources/kspd_fixed'

for filename in os.listdir(input_dir):
    input_path = os.path.join(input_dir, filename)
    print(input_path)

    with open(input_path, newline='', encoding='utf-8') as input_file:
        spamreader = csv.DictReader(input_file, delimiter=',', quotechar='"')
        fieldnames = spamreader.fieldnames
        paths = []
        trip_id = None
        for row in spamreader:
            trip_id = row['TRIP_ID']
            trip_id = "1" + trip_id
            row['TRIP_ID'] = trip_id
            paths.append(row)

        output_path = os.path.join(output_dir, trip_id + ".csv")
        print(output_path)
        with open(output_path, 'w', newline='', encoding='utf-8') as output_file:
            w = csv.DictWriter(output_file, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)
            w.writeheader()
            for row in paths:
                w.writerow(row)
