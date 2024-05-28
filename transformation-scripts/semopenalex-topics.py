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

# method to transform the display_name of a keyword into the keyword URI
#Artificial Intelligence -> https://openalex.org/keywords/artificial-intelligence
#Clinical Decision Support -> https://openalex.org/keywords/clinical-decision-support
def transform_keyword_to_uri(keyword):
    keyword = keyword.lower()
    keyword = keyword.replace(" ", "-")
    keyword = clean_url(keyword)
    keyword = "https://semopenalex.org/keywords/" + keyword
    return keyword



# info for namespaces used in SOA
soa_namespace_class = "https://semopenalex.org/ontology/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"
soa_namespace_topics = "https://semopenalex.org/topic/"
soa_namespace_subfields = "https://semopenalex.org/subfields/"
soa_namespace_fields = "https://semopenalex.org/fields/"
soa_namespace_domains = "https://semopenalex.org/domains/"
soa_namespace_publishers = "https://semopenalex.org/publisher/"
soa_namespace_institutions = "https://semopenalex.org/institution/"

# SOA classes used in this file
soa_class_topic = URIRef(soa_namespace_class + "Topic")
soa_class_counts_by_year = URIRef(soa_namespace_class + "CountsByYear")

# SOA predicates
works_count_predicate = URIRef("https://semopenalex.org/ontology/worksCount")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")
has_keyword_predicate = URIRef("https://semopenalex.org/ontology/hasKeyword")

# topics entity context
context = URIRef("https://semopenalex.org/topics/context")

#topic scheme URI
topic_scheme_uri = URIRef("https://semopenalex.org/topics")

i = 0
error_count = 0
topics_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'topics'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('topics entity files started to download at: '+ data_dump_start_time)
# Copy institutions entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/topics/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('topics entity files finished to download.')

start_time = time.ctime()
print('topics entity started to transform at: '+ start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:

    #Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # topic-ID
                    topic_id = json_data['id'].replace("https://openalex.org/", "")
                    topic_uri = URIRef(soa_namespace_topics+topic_id)
                    topics_graph.add((topic_uri, RDF.type, soa_class_topic))
                    topics_graph.add((topic_uri, RDF.type, SKOS.Concept))

                    #topic Scheme
                    topics_graph.add((topic_uri, SKOS.inScheme, topic_scheme_uri))

                    # display_name
                    topic_display_name = json_data['display_name']
                    if not topic_display_name is None:
                        topic_display_name = clean(topic_display_name)
                        topics_graph.add((topic_uri, SKOS.prefLabel, Literal(topic_display_name,datatype=XSD.string)))

                    # description
                    topic_description = json_data['description']
                    if not topic_description is None:
                        topic_description = clean(topic_description)
                        topics_graph.add((topic_uri, SKOS.note, Literal(topic_description,datatype=XSD.string)))

                    # subfield
                    topic_subfield = json_data['subfield']['id']
                    if not topic_subfield is None:
                        topic_subfield_id = topic_subfield.replace("https://openalex.org/", "")
                        topic_subfield_uri = URIRef(soa_namespace_subfields + topic_subfield_id)
                        topics_graph.add((topic_uri, SKOS.broader, topic_subfield_uri))

                    # field
                    # for now, we are not using the field information in the topics entity and only using the subfield information as the next broader concept

                    # domain
                    # for now, we are not using the domain information in the topics entity and only using the subfield information as the next broader concept

                    # ids (wikipedia)
                    topic_wikipedia = json_data.get('ids').get('wikipedia')
                    if not topic_wikipedia is None:
                        topic_wikipedia = clean_url(topic_wikipedia)
                        topics_graph.add((topic_uri,RDFS.seeAlso, Literal(topic_wikipedia, datatype=XSD.anyURI)))

                    # keywords
                    topic_keywords = json_data['keywords']
                    if not topic_keywords is None:
                        for keyword in topic_keywords:
                            keyword_uri = transform_keyword_to_uri(keyword)
                            topics_graph.add((topic_uri, has_keyword_predicate, URIRef(keyword_uri)))

                    # updated_date
                    topic_updated_date = json_data['updated_date']
                    if not topic_updated_date is None:
                        topic_updated_date = clean_date(topic_updated_date)
                        topics_graph.add((topic_uri, DCTERMS.modified, Literal(topic_updated_date,datatype=XSD.date)))

                    # created_date
                    topic_created_date = json_data['created_date']
                    if not topic_created_date is None:
                        topics_graph.add((topic_uri, DCTERMS.created, Literal(topic_created_date,datatype=XSD.date)))

                    # works_count
                    topic_works_count = json_data['works_count']
                    if not topic_works_count is None:
                        topics_graph.add((topic_uri, works_count_predicate, Literal(topic_works_count,datatype=XSD.integer)))

                    # cited_by_count
                    topic_cited_by_count = json_data['cited_by_count']
                    if not topic_cited_by_count is None:
                        topics_graph.add((topic_uri, cited_by_count_predicate, Literal(topic_cited_by_count,datatype=XSD.integer)))

                    # siblings 
                    topic_siblings = json_data['siblings']
                    if not topic_siblings is None:
                        for sibling in topic_siblings:
                            sibling_id = sibling['id'].replace("https://openalex.org/", "")
                            sibling_uri = URIRef(soa_namespace_topics+sibling_id)
                            topics_graph.add((topic_uri, SKOS.related, sibling_uri))


                    i += 1
                    if i % 100 == 0:
                        print('Processed topics entity {} lines'.format(i))

                    if i % 100 == 0:
                        g.write(topics_graph.serialize(format='trig'))
                        topics_graph = Graph(identifier=context)

                except Exception as e:
                    print(str((e)) + ' Error in topics entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the last part
    if not i % 100 == 0:
        g.write(topics_graph.serialize(format='trig'))
        topics_graph = Graph(identifier=context)

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
