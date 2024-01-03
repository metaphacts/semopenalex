# Copyright Johan Krause, Michael Färber, David Lamprecht; Institute AIFB, Karlsruhe Institute of Technology (KIT)
# this script transforms OpenAlex data dump files for source entities to triple form in trig files for SemOpenAlex
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
soa_namespace_authors = "https://semopenalex.org/author/"
soa_namespace_sources = "https://semopenalex.org/source/"
soa_namespace_publishers = "https://semopenalex.org/publisher/"  # new
soa_namespace_institutions = "https://semopenalex.org/institution/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"

# SOA classes used in this file
soa_class_source = URIRef(soa_namespace_class + "Source")
soa_class_counts_by_year = URIRef(soa_namespace_class + "CountsByYear")

# SOA predicates
has_issnl_predicate = URIRef("http://purl.org/spar/fabio/hasIssnL")
has_issn_predicate = URIRef("http://prismstandard.org/namespaces/basic/2.0/issn")
works_count_predicate = URIRef("https://semopenalex.org/ontology/worksCount")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")
is_in_doaj_predicate = URIRef("https://semopenalex.org/ontology/isInDoaj")
is_oa_predicate = URIRef("https://semopenalex.org/ontology/isOa")
mag_id_predicate = URIRef("https://semopenalex.org/ontology/magId")
counts_by_year_predicate = URIRef("https://semopenalex.org/ontology/countsByYear")
year_predicate = URIRef("https://semopenalex.org/ontology/year")
# modified:
has_host_organization_predicate = URIRef("https://semopenalex.org/ontology/hasHostOrganization")
country_code_geo_predicate = URIRef("http://www.geonames.org/ontology#countryCode")
apc_usd_predicate = URIRef("https://semopenalex.org/ontology/apcUsd")
source_type_predicate = URIRef("https://semopenalex.org/ontology/sourceType")
fatcat_id_predicate = URIRef("https://semopenalex.org/ontology/fatcatId")
alt_name_predicate = URIRef("https://dbpedia.org/ontology/alternativeName")
abbreviated_name_predicate = URIRef("https://semopenalex.org/ontology/abbreviatedName")
mean_citedness_predicate = URIRef("https://semopenalex.org/ontology/2YrMeanCitedness")
h_index_predicate = URIRef("http://purl.org/spar/bido/h-index")
i10_index_predicate = URIRef("https://semopenalex.org/ontology/i10Index")

# sources entity context
context = URIRef("https://semopenalex.org/sources/context")

i = 0
error_count = 0
source_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'sources'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/')
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('sources entity files started to download at: ' + data_dump_start_time)
# Copy sources entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/sources/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('sources entity files finished to download.')

start_time = time.ctime()
print('sources entity started to transform at: ' + start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:
    # Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # source-ID
                    source_id = json_data['id'].replace("https://openalex.org/", "")
                    source_uri = URIRef(soa_namespace_sources + source_id)
                    source_graph.add((source_uri, RDF.type, soa_class_source))

                    # display_name
                    source_display_name = json_data['display_name']
                    if not source_display_name is None:
                        source_display_name = clean(source_display_name)
                        source_graph.add((source_uri, FOAF.name, Literal(source_display_name, datatype=XSD.string)))

                    host_organization_id = json_data['host_organization']
                    if not host_organization_id is None:
                        host_organization_id = host_organization_id.replace("https://openalex.org/",
                                                                            "")  # can be P4310319909 or I1294671590
                        if host_organization_id[0] == 'P':
                            # publisher case
                            host_organization_uri = URIRef(soa_namespace_publishers + str(host_organization_id))

                        elif host_organization_id[0] == 'I':
                            # institution case
                            host_organization_uri = URIRef(soa_namespace_institutions + str(host_organization_id))

                        source_graph.add((source_uri, has_host_organization_predicate, host_organization_uri))

                    # source type
                    source_type = json_data['type']
                    if not source_type is None:
                        source_graph.add((source_uri, source_type_predicate, Literal(source_type, datatype=XSD.string)))

                    # apcUsd
                    source_apc_usd = json_data['apc_usd']
                    if not source_apc_usd is None:
                        source_graph.add((source_uri, apc_usd_predicate, Literal(source_apc_usd, datatype=XSD.integer)))

                    # country code
                    source_country_code = json_data['country_code']
                    if not source_country_code is None:
                        source_graph.add(
                            (source_uri, country_code_geo_predicate, Literal(source_country_code, datatype=XSD.string)))

                    # fatcat id
                    source_fatcat_id = json_data.get('ids').get('fatcat')
                    if not source_fatcat_id is None:
                        source_graph.add(
                            (source_uri, fatcat_id_predicate, Literal(source_fatcat_id, datatype=XSD.string)))

                    # abbreviated title
                    source_abbreviated_name = json_data['abbreviated_title']
                    if not source_abbreviated_name is None:
                        source_graph.add((source_uri, abbreviated_name_predicate,
                                          Literal(source_abbreviated_name, datatype=XSD.string)))

                    # alternate titles
                    source_alternate_names = json_data['alternate_titles']
                    if not source_alternate_names is None:
                        if len(source_alternate_names) != 0:
                            for alt_name in source_alternate_names:
                                source_graph.add((source_uri, alt_name_predicate,
                                                  Literal(alt_name, datatype=XSD.string)))

                    # wikidata ID
                    source_wikidata = json_data.get('ids').get('wikidata')
                    if not source_wikidata is None:
                        source_graph.add(
                            (source_uri, OWL.sameAs, URIRef(clean_url(source_wikidata))))

                    # issn_l
                    source_issn_l = json_data['issn_l']
                    if not source_issn_l is None:
                        source_graph.add((source_uri, has_issnl_predicate, Literal(source_issn_l, datatype=XSD.string)))

                    # issn
                    source_issn_list = json_data['issn']
                    if not source_issn_list is None:
                        for source_issn in source_issn_list:
                            source_graph.add(
                                (source_uri, has_issn_predicate, Literal(source_issn, datatype=XSD.string)))

                    # summary stats
                    source_2yr_mean_citedness = json_data.get('summary_stats').get('2yr_mean_citedness')
                    if not source_2yr_mean_citedness is None:
                        source_graph.add((source_uri, mean_citedness_predicate,
                                          Literal(source_2yr_mean_citedness, datatype=XSD.float)))

                    source_h_index = json_data.get('summary_stats').get('h_index')
                    if not source_h_index is None:
                        source_graph.add(
                            (
                                source_uri, h_index_predicate, Literal(source_h_index, datatype=XSD.integer)))

                    source_i10_index = json_data.get('summary_stats').get('i10_index')
                    if not source_i10_index is None:
                        source_graph.add(
                            (source_uri, i10_index_predicate,
                             Literal(source_i10_index, datatype=XSD.integer)))

                    # works_count
                    source_works_count = json_data['works_count']
                    if not source_works_count is None:
                        source_graph.add(
                            (source_uri, works_count_predicate, Literal(source_works_count, datatype=XSD.integer)))

                    # cited_by_count
                    source_cited_by_count = json_data['cited_by_count']
                    if not source_cited_by_count is None:
                        source_graph.add((source_uri, cited_by_count_predicate,
                                          Literal(source_cited_by_count, datatype=XSD.integer)))

                    # is_oa
                    source_is_oa = json_data['is_oa']
                    if not source_is_oa is None:
                        source_graph.add((source_uri, is_oa_predicate, Literal(source_is_oa, datatype=XSD.boolean)))

                    # is_in_doaj
                    source_is_in_doaj = json_data['is_in_doaj']
                    if not source_is_in_doaj is None:
                        source_graph.add(
                            (source_uri, is_in_doaj_predicate, Literal(source_is_in_doaj, datatype=XSD.boolean)))

                    # homepage_url
                    source_homepage_url = json_data['homepage_url']
                    if not source_homepage_url is None:
                        source_homepage_url = clean_url(source_homepage_url)
                        source_graph.add((source_uri, FOAF.homepage, Literal(source_homepage_url, datatype=XSD.string)))

                    # ids (relevant: mag)
                    source_mag_id = json_data.get('ids').get('mag')
                    if not source_mag_id is None:
                        source_graph.add((source_uri, mag_id_predicate, Literal(source_mag_id, datatype=XSD.integer)))
                        makg_uri = URIRef("https://makg.org/entity/" + str(source_mag_id))
                        source_graph.add((source_uri, OWL.sameAs, makg_uri))

                    # counts_by_year (neue Klasse; verbindung; plus werte in neue Klasse)
                    source_counts_by_year = json_data['counts_by_year']
                    if not source_counts_by_year is None:
                        for count_year in source_counts_by_year:
                            count_year_year = count_year["year"]
                            count_year_uri = URIRef(soa_namespace_countsbyyear + source_id + 'Y' + str(count_year_year))

                            source_graph.add((count_year_uri, RDF.type, soa_class_counts_by_year))
                            source_graph.add((source_uri, counts_by_year_predicate, count_year_uri))
                            source_graph.add(
                                (count_year_uri, year_predicate, Literal(count_year_year, datatype=XSD.integer)))
                            count_year_works_count = count_year["works_count"]
                            source_graph.add((count_year_uri, works_count_predicate,
                                              Literal(count_year_works_count, datatype=XSD.integer)))
                            count_year_cited_by_count = count_year["cited_by_count"]
                            source_graph.add((count_year_uri, cited_by_count_predicate,
                                              Literal(count_year_cited_by_count, datatype=XSD.integer)))

                    # updated_date
                    source_updated_date = json_data['updated_date']
                    if not source_updated_date is None:
                        source_graph.add(
                            (source_uri, DCTERMS.modified, Literal(source_updated_date, datatype=XSD.date)))

                    # created_date
                    source_created_date = json_data['created_date']
                    if not source_created_date is None:
                        source_graph.add((source_uri, DCTERMS.created, Literal(source_created_date, datatype=XSD.date)))

                    i += 1
                    if i % 10000 == 0:
                        print('Processed source entity {} lines'.format(i))

                    if i % 20000 == 0:
                        g.write(source_graph.serialize(format='trig'))
                        source_graph = Graph(identifier=context)


                except Exception as e:
                    print(str((e)) + ' Error in sources entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the last part
    if not i % 20000 == 0:
        g.write(source_graph.serialize(format='trig'))
        source_graph = Graph(identifier=context)

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
