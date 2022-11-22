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
        "search"  : re.compile(r'"'),
        "replace" : '', #&quot;
        "comment" : "Unescaped quotation marks"
    },{
        "search"  : re.compile(r'\\'),
        "replace" : '', #&#92;
        "comment" : "Unescaped backslash"
    },{
        "search"  : re.compile(r'\n'),
        "replace" : '',
        "comment" : "Newline string"
    },{
        "search"  : re.compile(r'\b'),
        "replace" : '',
        "comment" : "Newline string"
    },{
        "search"  : re.compile(r'\t'),
        "replace" : '',
        "comment" : "Newline string"
    },{
        "search"  : re.compile(r'\r'),
        "replace" : '',
        "comment" : "Newline string"
    },{
        "search"  : re.compile(r'\f'),
        "replace" : '',
        "comment" : "Newline string"
    }
]
replacements_url = [
    {
        "search"  : re.compile(r'"'),
        "replace" : '%22',
        "comment" : "Unescaped quotation mark in URI"
    },{
        "search"  : re.compile(r'\\'),
        "replace" : '%5c',
        "comment" : "Unescaped backslash in URI"
    },{
        "search"  : re.compile(r'\n'),
        "replace" : '',
        "comment" : "Newline string"
    },{
        "search"  : re.compile(r'\r'),
        "replace" : '',
        "comment" : "Newline string"
    },{
        "search"  : re.compile(r'\t'),
        "replace" : '',
        "comment" : "Newline string"
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
soa_namespace_class = "https://semopenalex.org/class/"
soa_namespace_authors = "https://semopenalex.org/author/"
soa_namespace_venues = "https://semopenalex.org/venue/"
soa_namespace_host_venues = "https://semopenalex.org/hostvenue/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsbyyear/"

# SOA classes used in this file
soa_class_venue = URIRef(soa_namespace_class+"Venue")
soa_class_counts_by_year = URIRef(soa_namespace_class+"CountsByYear")

# SOA predicates
has_issnl_predicate = URIRef("http://purl.org/spar/fabio/hasIssnL")
has_issn_predicate = URIRef("http://prismstandard.org/namespaces/basic/2.0/issn")
works_count_predicate = URIRef("https://semopenalex.org/property/worksCount")
cited_by_count_predicate = URIRef("https://semopenalex.org/property/citedByCount")
is_in_doaj_predicate = URIRef("https://semopenalex.org/property/isInDoaj")
is_oa_predicate = URIRef("https://semopenalex.org/property/isOa")
mag_id_predicate = URIRef("https://semopenalex.org/property/magId")
counts_by_year_predicate = URIRef("https://semopenalex.org/property/countsByYear")
year_predicate = URIRef("https://semopenalex.org/property/year")

# venues entity context
context = URIRef("https://semopenalex.org/venues/context")

i = 0
error_count = 0
venue_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'venues'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('venues entity files started to download at: '+ data_dump_start_time)
# Copy venues entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/venues/")
download_files(
    client,
    "openalex",
    data_dump_input_root_dir,
    file_names,
    folders
)
print('venues entity files finished to download.')

start_time = time.ctime()
print('venues entity started to transform at: '+ start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:

    #Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # Venue-ID
                    venue_id = json_data['id'].replace("https://openalex.org/", "")
                    venue_uri = URIRef(soa_namespace_venues+venue_id)
                    venue_graph.add((venue_uri,RDF.type,soa_class_venue))

                    #issn_l
                    venue_issn_l = json_data['issn_l']
                    if not venue_issn_l is None:
                        venue_graph.add((venue_uri,has_issnl_predicate,Literal(venue_issn_l,datatype=XSD.string)))

                    #issn
                    venue_issn_list = json_data['issn']
                    if not venue_issn_list is None:
                        for venue_issn in venue_issn_list:
                            venue_graph.add((venue_uri,has_issn_predicate,Literal(venue_issn,datatype=XSD.string)))


                    #display_name
                    venue_display_name = json_data['display_name']
                    if not venue_display_name is None:
                        venue_display_name = clean(venue_display_name)
                        venue_graph.add((venue_uri,FOAF.name,Literal(venue_display_name,datatype=XSD.string)))

                    #publisher
                    venue_publisher = json_data['publisher']
                    if not venue_publisher is None:
                        venue_publisher = clean(venue_publisher)
                        venue_graph.add((venue_uri,DCTERMS.publisher,Literal(venue_publisher,datatype=XSD.string)))

                    #works_count
                    venue_works_count = json_data['works_count']
                    if not venue_works_count is None:
                        venue_graph.add((venue_uri,works_count_predicate,Literal(venue_works_count,datatype=XSD.integer)))

                    #cited_by_count
                    venue_cited_by_count = json_data['cited_by_count']
                    if not venue_cited_by_count is None:
                        venue_graph.add((venue_uri,cited_by_count_predicate,Literal(venue_cited_by_count,datatype=XSD.integer)))

                    #is_oa
                    venue_is_oa = json_data['is_oa']
                    if not venue_is_oa is None:
                        venue_graph.add((venue_uri,is_oa_predicate,Literal(venue_is_oa,datatype=XSD.boolean)))

                    #is_in_doaj
                    venue_is_in_doaj = json_data['is_in_doaj']
                    if not venue_is_in_doaj is None:
                        venue_graph.add((venue_uri,is_in_doaj_predicate,Literal(venue_is_in_doaj,datatype=XSD.boolean)))

                    #homepage_url
                    venue_homepage_url = json_data['homepage_url']
                    if not venue_homepage_url is None:
                        venue_homepage_url = clean_url(venue_homepage_url)
                        venue_graph.add((venue_uri,FOAF.homepage,Literal(venue_homepage_url,datatype=XSD.string)))

                    #ids (relevant: mag)
                    venue_mag_id = json_data.get('ids').get('mag')
                    if not venue_mag_id is None:
                        venue_graph.add((venue_uri,mag_id_predicate,Literal(venue_mag_id,datatype=XSD.integer)))
                        makg_uri = URIRef("https://makg.org/entity/" + str(venue_mag_id))
                        venue_graph.add((venue_uri,OWL.sameAs,makg_uri))




                    #counts_by_year (neue Klasse; verbindung; plus werte in neue Klasse)
                    venue_counts_by_year = json_data['counts_by_year']
                    if not venue_counts_by_year is None:
                        for count_year in venue_counts_by_year:
                            count_year_year = count_year["year"]
                            count_year_uri = URIRef(soa_namespace_countsbyyear + venue_id + str(count_year_year))

                            venue_graph.add((count_year_uri,RDF.type, soa_class_counts_by_year))
                            venue_graph.add((venue_uri,counts_by_year_predicate,count_year_uri))
                            venue_graph.add((count_year_uri,year_predicate,Literal(count_year_year, datatype=XSD.integer)))
                            count_year_works_count = count_year["works_count"]
                            venue_graph.add((count_year_uri,works_count_predicate,Literal(count_year_works_count,datatype=XSD.integer)))
                            count_year_cited_by_count = count_year["cited_by_count"]
                            venue_graph.add((count_year_uri,cited_by_count_predicate,Literal(count_year_cited_by_count,datatype=XSD.integer)))

                    #works_api_url
                    #to do

                    #updated_date
                    venue_updated_date = json_data['updated_date']
                    if not venue_updated_date is None:
                        venue_graph.add((venue_uri,DCTERMS.modified,Literal(venue_updated_date,datatype=XSD.date)))

                    #created_date
                    venue_created_date = json_data['created_date']
                    if not venue_created_date is None:
                        venue_graph.add((venue_uri,DCTERMS.created,Literal(venue_created_date,datatype=XSD.date)))

                    i += 1
                    if i % 10000 == 0:
                        print('Processed venues entity {} lines'.format(i))

                    if i % 20000 == 0:
                        g.write(venue_graph.serialize(format='trig'))
                        venue_graph = Graph(identifier=context)


                except Exception as e:
                    print(str((e)) + ' Error in venues entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the last part
    if not i % 20000 == 0:
        g.write(venue_graph.serialize(format='trig'))
        venue_graph = Graph(identifier=context)

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
print('Error count: '+str(error_count))
print("#############################")
