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
soa_namespace_domains = "https://semopenalex.org/domain/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"

# SOA classes used in this file
soa_class_counts_by_year = URIRef(soa_namespace_class+"CountsByYear")
soa_class_domain = URIRef(soa_namespace_class + "Domain")


# SOA predicates
counts_by_year_predicate = URIRef("https://semopenalex.org/ontology/countsByYear")
year_predicate = URIRef("https://semopenalex.org/ontology/year")
level_predicate = URIRef("https://semopenalex.org/ontology/level")
works_count_predicate = URIRef("https://semopenalex.org/ontology/worksCount")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")
mag_id_predicate = URIRef("https://semopenalex.org/ontology/magId")
umls_aui_predicate = URIRef("https://semopenalex.org/ontology/umlsAui")
umls_cui_predicate = URIRef("https://semopenalex.org/ontology/umlsCui")
image_thumbnail_predicate = URIRef("https://semopenalex.org/ontology/imageThumbnail")

#domains entity context (same as topics entity context!)
context = URIRef("https://semopenalex.org/topics/context")

#topic scheme URI
topic_scheme_uri = URIRef("https://semopenalex.org/topics")

i = 0
error_count = 0
domain_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'domains'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('domains entity files started to download at: '+ data_dump_start_time)
# Copy domains entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/domains/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('domains entity files finished to download.')

start_time = time.ctime()
print('domains entity started to transform at: '+ start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:

    #Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    # initialize and add domain scheme URI
    domain_graph.add((topic_scheme_uri, RDF.type, SKOS.ConceptScheme))
    domain_graph.add((topic_scheme_uri, SKOS.prefLabel, Literal("SemOpenAlex Topics", datatype = XSD.string)))
    domain_graph.add((topic_scheme_uri, URIRef("http://purl.org/dc/terms/description"), Literal("SemOpenAlex topics are abstract ideas that works are about. Topics are grouped into subfields, which are grouped into fields, which are grouped into top-level domains.", datatype = XSD.string)))

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:

            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    #domain-ID
                    domain_id = json_data['id'].replace("https://openalex.org/domains/", "")
                    domain_uri = URIRef(soa_namespace_domains+domain_id)
                    domain_graph.add((domain_uri,RDF.type, soa_class_domain))
                    domain_graph.add((domain_uri,RDF.type, SKOS.Concept))

                    #topic Scheme
                    domain_graph.add((domain_uri,SKOS.inScheme,topic_scheme_uri))
                    domain_graph.add((topic_scheme_uri, SKOS.hasTopConcept, URIRef(domain_uri)))

                    # display_name
                    domain_display_name = json_data['display_name']
                    if not domain_display_name is None:
                        domain_display_name = clean(domain_display_name)
                        domain_graph.add((domain_uri, SKOS.prefLabel, Literal(domain_display_name, datatype=XSD.string)))

                    # display_name_alternatives
                    domain_display_name_alternatives = json_data['display_name_alternatives']
                    if not domain_display_name_alternatives is None:
                        for alternative_name in domain_display_name_alternatives:
                            alternative_name = clean(alternative_name)
                            domain_graph.add((domain_uri, SKOS.altLabel, Literal(alternative_name, datatype=XSD.string)))

                    # description
                    domain_description = json_data['description']
                    if not domain_description is None:
                        domain_description = clean(domain_description)
                        domain_graph.add((domain_uri, SKOS.note, Literal(domain_description, datatype=XSD.string)))

                    # siblings
                    domain_siblings = json_data['siblings']
                    if not domain_siblings is None:
                        for sibling in domain_siblings:
                            sibling_id = sibling['id'].replace("https://openalex.org/domains/", "")
                            sibling_uri = URIRef(soa_namespace_domains+sibling_id)
                            domain_graph.add((domain_uri, SKOS.related, sibling_uri))

                    # ids (wikidata, wikipedia)
                    domain_wikidata = json_data.get('ids').get('wikidata')
                    if not domain_wikidata is None:
                        domain_wikidata = clean_url(domain_wikidata)
                        domain_graph.add((domain_uri,OWL.sameAs, URIRef(domain_wikidata)))

                    domain_wikipedia = json_data.get('ids').get('wikipedia')
                    if not domain_wikipedia is None:
                        domain_wikipedia = clean_url(domain_wikipedia)
                        domain_graph.add((domain_uri, RDFS.seeAlso, URIRef(domain_wikipedia)))

                    # works_count
                    domain_works_count = json_data['works_count']
                    if not domain_works_count is None:
                        domain_graph.add((domain_uri, works_count_predicate, Literal(domain_works_count, datatype=XSD.integer)))

                    # cited_by_count
                    domain_cited_by_count = json_data['cited_by_count']
                    if not domain_cited_by_count is None:
                        domain_graph.add((domain_uri, cited_by_count_predicate, Literal(domain_cited_by_count, datatype=XSD.integer)))

                    # created_date
                    domain_created_date = json_data['created_date']
                    if not domain_created_date is None:
                        domain_graph.add((domain_uri, DCTERMS.created, Literal(domain_created_date, datatype=XSD.date)))

                    # updated_date
                    domain_updated_date = json_data['updated_date']
                    if not domain_updated_date is None:
                        domain_updated_date = clean_date(domain_updated_date)
                        domain_graph.add((domain_uri, DCTERMS.modified, Literal(domain_updated_date, datatype=XSD.date)))


                    i += 1
                    print('Processed domains entity {} lines'.format(i))

                except Exception as e:
                    print(str((e)) + ' Error in domains entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the graph to the .trig file
    g.write(domain_graph.serialize(format='trig'))

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
