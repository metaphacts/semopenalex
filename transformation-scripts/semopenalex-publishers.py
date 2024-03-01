# Copyright Johan Krause, Michael Färber, David Lamprecht; Institute AIFB, Karlsruhe Institute of Technology (KIT)
# this script transforms OpenAlex data dump files for publisher entities to triple form in trig files for SemOpenAlex
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, OWL, FOAF
import json
import os
import glob
import gzip
import re
import time
import boto3
from datetime import date
from pathlib import Path
from botocore import UNSIGNED
from botocore.config import Config


def get_file_folders(s3_client, bucket_name, prefix=""):
    file_names = []
    folders = []

    default_kwargs = {
        "Bucket": bucket_name,
        "Prefix": prefix
    }
    next_token = ""

    while next_token is not None:
        updated_kwargs = default_kwargs.copy()
        if next_token != "":
            updated_kwargs["ContinuationToken"] = next_token

        response = s3_client.list_objects_v2(**default_kwargs)
        contents = response.get("Contents")

        for result in contents:
            key = result.get("Key")
            if key[-1] == "/":
                folders.append(key)
            else:
                file_names.append(key)

        next_token = response.get("NextContinuationToken")

    return file_names, folders


def download_files(s3_client, bucket_name, local_path, file_names, folders):
    local_path = Path(local_path)

    for folder in folders:
        folder_path = Path.joinpath(local_path, folder)
        folder_path.mkdir(parents=True, exist_ok=True)

    for file_name in file_names:
        file_path = Path.joinpath(local_path, file_name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        s3_client.download_file(
            bucket_name,
            file_name,
            str(file_path)
        )


replacements = [
    {
        "search": re.compile(r'"'),
        "replace": '',  # &quot;
        "comment": "Unescaped quotation marks"
    }, {
        "search": re.compile(r'\\'),
        "replace": '',  # &#92;
        "comment": "Unescaped backslash"
    }, {
        "search": re.compile(r'\n'),
        "replace": '',
        "comment": "Newline string"
    }, {
        "search": re.compile(r'\b'),
        "replace": '',
        "comment": "Newline string"
    }, {
        "search": re.compile(r'\t'),
        "replace": '',
        "comment": "Newline string"
    }, {
        "search": re.compile(r'\r'),
        "replace": '',
        "comment": "Newline string"
    }, {
        "search": re.compile(r'\f'),
        "replace": '',
        "comment": "Newline string"
    }
]
replacements_url = [
    {
        "search": re.compile(r'"'),
        "replace": '%22',
        "comment": "Unescaped quotation mark in URI"
    }, {
        "search": re.compile(r'\\'),
        "replace": '%5c',
        "comment": "Unescaped backslash in URI"
    }, {
        "search": re.compile(r'\n'),
        "replace": '',
        "comment": "Newline string"
    }, {
        "search": re.compile(r'\r'),
        "replace": '',
        "comment": "Newline string"
    }, {
        "search": re.compile(r'\t'),
        "replace": '',
        "comment": "Newline string"
    },
]


def clean(nameStr):
    cleaned_str = nameStr
    for r in replacements:
        if re.search(r["search"], nameStr):
            cleaned_str = re.sub(r["search"], r["replace"], cleaned_str)
    return cleaned_str


def clean_url(nameStr):
    cleaned_str = nameStr
    for r in replacements_url:
        if re.search(r["search"], nameStr):
            cleaned_str = re.sub(r["search"], r["replace"], cleaned_str)
    return cleaned_str


# info for namespaces used in SOA
soa_namespace_class = "https://semopenalex.org/ontology/"
soa_namespace_publishers = "https://semopenalex.org/publisher/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"
soa_namespace_institutions = "https://semopenalex.org/institution/"

# SOA classes used in this file
soa_class_publisher = URIRef(soa_namespace_class + "Publisher")
soa_class_counts_by_year = URIRef(soa_namespace_class + "CountsByYear")

# SOA predicates
level_predicate = URIRef("https://semopenalex.org/ontology/level")
has_parent_publisher_predicate = URIRef("https://semopenalex.org/ontology/hasParentPublisher")
counts_by_year_predicate = URIRef("https://semopenalex.org/ontology/countsByYear")
country_code_geo_predicate = URIRef("http://www.geonames.org/ontology#countryCode")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")
works_count_predicate = URIRef("https://semopenalex.org/ontology/worksCount")
alt_name_predicate = URIRef("https://dbpedia.org/ontology/alternativeName")
ror_predicate = URIRef("https://semopenalex.org/ontology/ror")
mean_citedness_predicate = URIRef("https://semopenalex.org/ontology/2YrMeanCitedness")
h_index_predicate = URIRef("http://purl.org/spar/bido/h-index")
i10_index_predicate = URIRef("https://semopenalex.org/ontology/i10Index")
year_predicate = URIRef("https://semopenalex.org/ontology/year")

# publishers entity context
context = URIRef("https://semopenalex.org/publishers/context")

i = 0
error_count = 0
publisher_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'publishers'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/')
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('publishers entity files started to download at: ' + data_dump_start_time)
# Copy publishers entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/publishers/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('publishers entity files finished to download.')

start_time = time.ctime()
print('publishers entity started to transform at: ' + start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:
    # Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # publisher-ID
                    publisher_id = json_data['id'].replace("https://openalex.org/", "")
                    publisher_uri = URIRef(soa_namespace_publishers + publisher_id)
                    publisher_graph.add((publisher_uri, RDF.type, soa_class_publisher))

                    # publisher name
                    publisher_display_name = json_data['display_name']
                    if not publisher_display_name is None:
                        publisher_display_name = clean(publisher_display_name)
                        publisher_graph.add(
                            (publisher_uri, FOAF.name, Literal(publisher_display_name, datatype=XSD.string)))

                    # alternate titles
                    publisher_alternate_names = json_data['alternate_titles']
                    if not publisher_alternate_names is None:
                        if len(publisher_alternate_names) != 0:
                            for alt_name in publisher_alternate_names:
                                publisher_graph.add((publisher_uri, alt_name_predicate,
                                                     Literal(alt_name, datatype=XSD.string)))

                    # hierarchy level
                    publisher_level = json_data['hierarchy_level']
                    if not publisher_level is None:
                        publisher_graph.add(
                            (publisher_uri, level_predicate, Literal(publisher_level, datatype=XSD.integer)))

                    # parent publisher
                    parent_publisher_id = json_data['parent_publisher']
                    if not parent_publisher_id is None:
                        parent_publisher_id = parent_publisher_id.replace("https://openalex.org/", "")
                        parent_publisher_uri = URIRef(soa_namespace_publishers + str(parent_publisher_id))
                        publisher_graph.add((publisher_uri, has_parent_publisher_predicate, parent_publisher_uri))

                    # country code
                    publisher_country_codes = json_data['country_codes']
                    if not publisher_country_codes is None:
                        if len(publisher_country_codes) != 0:
                            for country_code in publisher_country_codes:
                                publisher_graph.add((publisher_uri, country_code_geo_predicate,
                                                     Literal(country_code, datatype=XSD.string)))

                    # ROR
                    publisher_ror = json_data.get('ids').get('ror')
                    if not publisher_ror is None:
                        publisher_graph.add((publisher_uri, ror_predicate, Literal(publisher_ror, datatype=XSD.string)))

                    # wikidata ID
                    publisher_wikidata = json_data.get('ids').get('wikidata')
                    if not publisher_wikidata is None:
                        publisher_graph.add(
                            (publisher_uri, OWL.sameAs, URIRef(clean_url(publisher_wikidata))))

                    # summary stats
                    publisher_2yr_mean_citedness = json_data.get('summary_stats').get('2yr_mean_citedness')
                    if not publisher_2yr_mean_citedness is None:
                        publisher_graph.add((publisher_uri, mean_citedness_predicate,
                                             Literal(publisher_2yr_mean_citedness, datatype=XSD.float)))

                    publisher_h_index = json_data.get('summary_stats').get('h_index')
                    if not publisher_h_index is None:
                        publisher_graph.add(
                            (publisher_uri, h_index_predicate, Literal(publisher_h_index, datatype=XSD.integer)))

                    publisher_i10_index = json_data.get('summary_stats').get('i10_index')
                    if not publisher_i10_index is None:
                        publisher_graph.add(
                            (publisher_uri, i10_index_predicate, Literal(publisher_i10_index, datatype=XSD.integer)))

                    # works_count
                    publisher_works_count = json_data['works_count']
                    if not publisher_works_count is None:
                        publisher_graph.add((publisher_uri, works_count_predicate,
                                             Literal(publisher_works_count, datatype=XSD.integer)))

                    # cited_by_count
                    publisher_cited_by_count = json_data['cited_by_count']
                    if not publisher_cited_by_count is None:
                        publisher_graph.add((publisher_uri, cited_by_count_predicate,
                                             Literal(publisher_cited_by_count, datatype=XSD.integer)))

                    # counts_by_year
                    publisher_counts_by_year = json_data['counts_by_year']
                    if not publisher_counts_by_year is None:
                        for count_year in publisher_counts_by_year:
                            count_year_year = count_year["year"]
                            count_year_uri = URIRef(soa_namespace_countsbyyear + publisher_id + 'Y' + str(count_year_year))

                            publisher_graph.add((count_year_uri, RDF.type, soa_class_counts_by_year))
                            publisher_graph.add((publisher_uri, counts_by_year_predicate, count_year_uri))
                            publisher_graph.add(
                                (count_year_uri, year_predicate, Literal(count_year_year, datatype=XSD.integer)))
                            count_year_works_count = count_year["works_count"]
                            publisher_graph.add((count_year_uri, works_count_predicate,
                                                 Literal(count_year_works_count, datatype=XSD.integer)))
                            count_year_cited_by_count = count_year["cited_by_count"]
                            publisher_graph.add((count_year_uri, cited_by_count_predicate,
                                                 Literal(count_year_cited_by_count, datatype=XSD.integer)))

                    #roles
                    publisher_roles = json_data['roles']
                    if not publisher_roles is None:
                        for role in publisher_roles:
                            role_role = role["role"]

                            # funders
                            # this owl:sameAs link is added in the semopenalex-funders.py script

                            # institution
                            if role_role == "institution":
                                role_id = role["id"].replace("https://openalex.org/", "")
                                role_uri = URIRef(soa_namespace_institutions + role_id)
                                publisher_graph.add((publisher_uri, OWL.sameAs, role_uri))

                    # updated_date
                    publisher_updated_date = json_data['updated_date']
                    if not publisher_updated_date is None:
                        publisher_graph.add(
                            (publisher_uri, DCTERMS.modified, Literal(publisher_updated_date, datatype=XSD.date)))

                    # created_date
                    publisher_created_date = json_data['created_date']
                    if not publisher_created_date is None:
                        publisher_graph.add(
                            (publisher_uri, DCTERMS.created, Literal(publisher_created_date, datatype=XSD.date)))

                    i += 1
                    if i % 10000 == 0:
                        print('Processed publisher entity {} lines'.format(i))

                    if i % 20000 == 0:
                        g.write(publisher_graph.serialize(format='trig'))
                        publisher_graph = Graph(identifier=context)


                except Exception as e:
                    print(str((e)) + ' Error in publishers entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the last part
    if not i % 20000 == 0:
        g.write(publisher_graph.serialize(format='trig'))
        publisher_graph = Graph(identifier=context)

f.close()
g.close()

print("Done with .trig parsing and graph serialization..")
print("Start zipping the .trig file.. ")

# gzip file directly with command
# -v for live output, --fast for faster compression with about 90% size reduction, -k for keeping the original .trig file
os.system(f'gzip --fast -v {trig_output_file_path}')

end_time = time.ctime()
with open(f"{trig_output_dir_path}{ENTITY_TYPE}-transformation-summary.txt", "w") as z:
    z.write('Start Time: {} .\n'.format(start_time))
    z.write('Items (lines) processed: {} .\n'.format(i))
    z.write('Errors encountered: {} .\n'.format(error_count))
    z.write('End Time: {} .\n'.format(end_time))
    z.close()

print("Done")
print('Processed {} lines in total'.format(i))
print('Error count: ' + str(error_count))
print("#############################")
