from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, OWL, FOAF, SKOS
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

# e.g 2024-05-27T05:10:45.699856 to 2024-05-27
def clean_date(dateStr):
    return dateStr.split("T")[0]


# info for namespaces used in SOA
soa_namespace_class = "https://semopenalex.org/ontology/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"
soa_namespace_subfields = "https://semopenalex.org/subfields/"
soa_namespace_fields = "https://semopenalex.org/fields/"
soa_namespace_domains = "https://semopenalex.org/domains/"
soa_namespace_publishers = "https://semopenalex.org/publisher/"
soa_namespace_institutions = "https://semopenalex.org/institution/"

# SOA classes used in this file
soa_class_topic = URIRef(soa_namespace_class + "Topic")
soa_class_subfield = URIRef(soa_namespace_class + "Subfield")
soa_class_field = URIRef(soa_namespace_class + "Field")
soa_class_counts_by_year = URIRef(soa_namespace_class + "CountsByYear")

# SOA predicates
works_count_predicate = URIRef("https://semopenalex.org/ontology/worksCount")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")

# topics entity context
context = URIRef("https://semopenalex.org/topics/context")

#topic scheme URI
topic_scheme_uri = URIRef("https://semopenalex.org/topics")

i = 0
error_count = 0
fields_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'fields'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('fields entity files started to download at: '+ data_dump_start_time)
# Copy institutions entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/fields/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('fields entity files finished to download.')

start_time = time.ctime()
print('fields entity started to transform at: '+ start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:

    #Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # field-ID
                    field_id = json_data['id'].replace("https://openalex.org/fields/", "")
                    field_uri = URIRef(soa_namespace_fields+field_id)
                    fields_graph.add((field_uri, RDF.type, soa_class_field))
                    fields_graph.add((field_uri, RDF.type, SKOS.Concept))

                    #topic Scheme
                    fields_graph.add((field_uri, SKOS.inScheme, topic_scheme_uri))

                    # display_name
                    field_display_name = json_data['display_name']
                    if not field_display_name is None:
                        field_display_name = clean(field_display_name)
                        fields_graph.add((field_uri, SKOS.prefLabel, Literal(field_display_name,datatype=XSD.string)))

                    # display_name_alternatives
                    field_display_name_alternatives = json_data['display_name_alternatives']
                    if not field_display_name_alternatives is None:
                        for display_name_alternative in field_display_name_alternatives:
                            display_name_alternative = clean(display_name_alternative)
                            fields_graph.add((field_uri, SKOS.altLabel, Literal(display_name_alternative,datatype=XSD.string)))

                    # description
                    field_description = json_data['description']
                    if not field_description is None:
                        field_description = clean(field_description)
                        fields_graph.add((field_uri, SKOS.note, Literal(field_description,datatype=XSD.string)))

                    # domain
                    field_domain = json_data['domain']['id']
                    if not field_domain is None:
                        field_domain_id = field_domain.replace("https://openalex.org/domains/", "")
                        field_domain_uri = URIRef(soa_namespace_domains + field_domain_id)
                        fields_graph.add((field_uri, SKOS.broader, field_domain_uri))

                    # ids (wikidata, wikipedia)
                    field_wikidata = json_data.get('ids').get('wikidata')
                    if not field_wikidata is None:
                        field_wikidata = clean_url(field_wikidata)
                        fields_graph.add((field_uri, OWL.sameAs, URIRef(field_wikidata)))

                    field_wikipedia = json_data.get('ids').get('wikipedia')
                    if not field_wikipedia is None:
                        field_wikipedia = clean_url(field_wikipedia)
                        fields_graph.add((field_uri, RDFS.seeAlso, Literal(field_wikipedia, datatype=XSD.anyURI)))

                    # updated_date
                    field_updated_date = json_data['updated_date']
                    if not field_updated_date is None:
                        field_updated_date = clean_date(field_updated_date)
                        fields_graph.add((field_uri, DCTERMS.modified, Literal(field_updated_date,datatype=XSD.date)))

                    # created_date
                    field_created_date = json_data['created_date']
                    if not field_created_date is None:
                        fields_graph.add((field_uri, DCTERMS.created, Literal(field_created_date,datatype=XSD.date)))

                    # works_count
                    field_works_count = json_data['works_count']
                    if not field_works_count is None:
                        fields_graph.add((field_uri, works_count_predicate, Literal(field_works_count,datatype=XSD.integer)))

                    # cited_by_count
                    field_cited_by_count = json_data['cited_by_count']
                    if not field_cited_by_count is None:
                        fields_graph.add((field_uri, cited_by_count_predicate, Literal(field_cited_by_count,datatype=XSD.integer)))

                    # siblings 
                    field_siblings = json_data['siblings']
                    if not field_siblings is None:
                        for sibling in field_siblings:
                            sibling_id = sibling['id'].replace("https://openalex.org/fields/", "")
                            sibling_uri = URIRef(soa_namespace_fields+sibling_id)
                            fields_graph.add((field_uri, SKOS.related, sibling_uri))

                    i += 1
                    print('Processed fields entity {} lines'.format(i))
                    g.write(fields_graph.serialize(format='trig'))
                    fields_graph = Graph(identifier=context)

                except Exception as e:
                    print(str((e)) + ' Error in fields entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

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
