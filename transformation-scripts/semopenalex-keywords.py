# We use the topics files to create the keywords files because the keywords are not provided in separate files in the data snapshot
# Each topic entry has a list of max 10 keywords

from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, OWL, FOAF, SKOS
from rdflib import term
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
    }, {
        "search": re.compile(r'/'),
        "replace": '',
        "comment": "Slash in URI"
    }, {
        "search": re.compile(r'$'),
        "replace": '',
        "comment": "Dollar sign in URI"
    }, {
        "search": re.compile(r'_'),
        "replace": '',
        "comment": "Underscore in URI"
    }, {
        "search": re.compile(r'{'),
        "replace": '',
        "comment": "Opening curly brace in URI"
    }, {
        "search": re.compile(r'}'),
        "replace": '',
        "comment": "Closing curly brace in URI"
    }
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

# SOA classes used in this file
soa_class_keyword = URIRef(soa_namespace_class + "Keyword")

# SOA predicates

# topics entity context
context = URIRef("https://semopenalex.org/keywords/context")

#topic scheme URI
keyword_scheme_uri = URIRef("https://semopenalex.org/keywords/")

i = 0
error_count = 0
keywords_graph = Graph(identifier=context)

today = date.today()

# Entity type of the snapshot files to be processed
##########
ENTITY_TYPE_INPUT = 'topics'
##########

##########
ENTITY_TYPE_OUTPUT = 'keywords'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE_OUTPUT}-semopenalex-{today}.trig'

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
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE_INPUT}/*'


    # initialize and add domain scheme URI
    keywords_graph.add((keyword_scheme_uri, RDF.type, SKOS.ConceptScheme))
    keywords_graph.add((keyword_scheme_uri, SKOS.prefLabel, Literal("SemOpenAlex Keywords", datatype = XSD.string)))
    keywords_graph.add((keyword_scheme_uri, URIRef("http://purl.org/dc/terms/description"), Literal("SemOpenAlex keywords are based on SemOpenAlex topics. They are specific words or phrases used to capture the essential topics or ideas of an entity.", datatype = XSD.string)))


    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # keyword-URI
                    # keywords
                    topic_keywords = json_data['keywords']
                    if not topic_keywords is None:
                        for keyword in topic_keywords:
                            keyword_uri = transform_keyword_to_uri(keyword)

                            if term._is_valid_uri(keyword_uri):
                                keywords_graph.add((URIRef(keyword_uri), RDF.type, soa_class_keyword))
                                keywords_graph.add((URIRef(keyword_uri), RDF.type, SKOS.Concept))
                                keywords_graph.add((URIRef(keyword_uri), SKOS.inScheme, keyword_scheme_uri))
                                keywords_graph.add((keyword_scheme_uri, SKOS.hasTopConcept, URIRef(keyword_uri)))
                                keywords_graph.add((URIRef(keyword_uri), SKOS.prefLabel, Literal(keyword, datatype=XSD.string)))
                        
                    i += 1
                    if i % 100 == 0:
                        print('Processed topics entity {} lines for the keyword files generation'.format(i))

                except Exception as e:
                    print(str((e)) + ' Error in topics entity line for the keyword files generation' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the graph to the .trig file
    g.write(keywords_graph.serialize(format='trig'))

f.close()
g.close()

print("Done with .trig parsing and graph serialization..")
print("Start zipping the .trig file.. ")

# gzip file directly with command
# -v for live output, --fast for faster compression with about 90% size reduction, -k for keeping the original .trig file
os.system(f'gzip --fast -v {trig_output_file_path}')

end_time = time.ctime()
with open(f"{trig_output_dir_path}{ENTITY_TYPE_OUTPUT}-transformation-summary.txt", "w") as z:
    z.write('Start Time: {} .\n'.format(start_time))
    z.write('Items (lines) processed: {} .\n'.format(i))
    z.write('Errors encountered: {} .\n'.format(error_count))
    z.write('End Time: {} .\n'.format(end_time))
    z.close()


print("Done")
print('Processed {} lines in total'.format(i))
print('Error count: '+str(error_count))
print("#############################")
