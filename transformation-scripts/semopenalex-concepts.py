# Copyright Johan Krause, Michael Färber, David Lamprecht; Institute AIFB, Karlsruhe Institute of Technology (KIT)
# this script transforms OpenAlex data dump files for concept entities to triple form in trig files for SemOpenAlex
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


# info for namespaces used in SOA
soa_namespace_class = "https://semopenalex.org/ontology/"
soa_namespace_concepts = "https://semopenalex.org/concept/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"

# SOA classes used in this file
soa_class_counts_by_year = URIRef(soa_namespace_class+"CountsByYear")

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

#concepts entity context
context = URIRef("https://semopenalex.org/concepts/context")

#concept scheme URI
concept_scheme_uri = URIRef("https://semopenalex.org/concepts")

i = 0
error_count = 0
concept_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'concepts'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('concepts entity files started to download at: '+ data_dump_start_time)
# Copy concepts entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/concepts/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('concepts entity files finished to download.')

start_time = time.ctime()
print('concepts entity started to transform at: '+ start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:

    #Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    # initialize and add concept scheme URI
    concept_graph.add((concept_scheme_uri, RDF.type, SKOS.ConceptScheme))
    concept_graph.add((concept_scheme_uri, SKOS.prefLabel, Literal("SemOpenAlex Concepts", datatype = XSD.string)))
    concept_graph.add((concept_scheme_uri, URIRef("http://purl.org/dc/terms/description"), Literal("SemOpenAlex concepts are abstract ideas that works are about.", datatype = XSD.string)))

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:

            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    #Concept-ID
                    concept_id = json_data['id'].replace("https://openalex.org/", "")
                    concept_uri = URIRef(soa_namespace_concepts+concept_id)
                    concept_graph.add((concept_uri,RDF.type,SKOS.Concept))

                    #Concept Scheme
                    concept_graph.add((concept_uri,SKOS.inScheme,concept_scheme_uri))

                    #wikidata
                    concept_wikidata = json_data['wikidata']
                    if not concept_wikidata is None:
                        concept_wikidata = clean_url(concept_wikidata)
                        concept_wikidata_canonical = concept_wikidata.replace("/wiki/","/entity/").replace("https","http")
                        concept_wikidata_uri = URIRef(concept_wikidata_canonical)
                        #aus 'https://www.wikidata.org/wiki/Q1231558' wird 'http://www.wikidata.org/entity/Q1231558'

                        concept_graph.add((concept_uri,OWL.sameAs,concept_wikidata_uri))

                    #display_name
                    concept_display_name = json_data['display_name']
                    if not concept_display_name is None:
                        concept_display_name = clean(concept_display_name)
                        concept_graph.add((concept_uri,SKOS.prefLabel,Literal(concept_display_name,datatype=XSD.string)))

                    #level
                    concept_level = json_data['level']
                    if not concept_level is None:
                        concept_graph.add((concept_uri,level_predicate,Literal(concept_level,datatype=XSD.integer)))
                        if concept_level == 0:
                            concept_graph.add((concept_scheme_uri,SKOS.hasTopConcept,concept_uri))


                    #description
                    concept_description = json_data['description']
                    if not concept_description is None:
                        concept_description = clean(concept_description)
                        concept_graph.add((concept_uri,SKOS.note,Literal(concept_description,datatype=XSD.string)))

                    # works_count
                    concept_works_count = json_data['works_count']
                    if not concept_works_count is None:
                        concept_graph.add((concept_uri,works_count_predicate,Literal(concept_works_count,datatype=XSD.integer)))

                    # cited_by_count
                    concept_cited_by_count = json_data['cited_by_count']
                    if not concept_cited_by_count is None:
                        concept_graph.add((concept_uri,cited_by_count_predicate,Literal(concept_cited_by_count,datatype=XSD.integer)))


                    # ids (relevant: mag, wikipedia, umls_aui, umls_cui)
                    concept_mag_id = json_data.get('ids').get('mag')
                    if not concept_mag_id is None:
                        concept_graph.add((concept_uri,mag_id_predicate,Literal(concept_mag_id,datatype=XSD.integer)))
                        mag_id_uri = URIRef("https://makg.org/entity/" + str(concept_mag_id))
                        concept_graph.add((concept_uri,OWL.sameAs,mag_id_uri))

                    concept_wikipedia = json_data.get('ids').get('wikipedia')
                    if not concept_wikipedia is None:
                        concept_wikipedia = clean_url(concept_wikipedia)
                        concept_graph.add((concept_uri,RDFS.seeAlso,Literal(concept_wikipedia,datatype=XSD.string)))

                    concept_umls_aui = json_data.get('ids').get('umls_aui')
                    if not concept_umls_aui is None:
                        for uml_aui in concept_umls_aui:
                            concept_graph.add((concept_uri,umls_aui_predicate,Literal(uml_aui,datatype=XSD.string)))

                    concept_umls_cui = json_data.get('ids').get('umls_cui')
                    if not concept_umls_cui is None:
                        for uml_cui in concept_umls_cui:
                            concept_graph.add((concept_uri,umls_cui_predicate,Literal(uml_cui,datatype=XSD.string)))

                    # image_url
                    concept_image_url = json_data['image_url']
                    if not concept_image_url is None:
                        concept_image_url = clean_url(concept_image_url)
                        concept_graph.add((concept_uri,FOAF.depiction,Literal(concept_image_url,datatype=XSD.string)))

                    # image_thumbnail_url
                    concept_image_thumbnail_url = json_data['image_thumbnail_url']
                    if not concept_image_thumbnail_url is None:
                        concept_image_thumbnail_url = clean_url(concept_image_thumbnail_url)
                        concept_graph.add((concept_uri,image_thumbnail_predicate,Literal(concept_image_thumbnail_url,datatype=XSD.string)))


                    # international
                    # to do

                    #ancestors
                    concept_ancestors = json_data['ancestors']
                    if not concept_ancestors is None:
                        for ancestor in concept_ancestors:
                            ancestor_id = ancestor["id"].replace("https://openalex.org/", "")
                            ancestor_uri = URIRef(soa_namespace_concepts+ancestor_id)
                            concept_graph.add((concept_uri,SKOS.broader,ancestor_uri))

                    #related_concepts
                    concept_related_concepts = json_data['related_concepts']
                    if not concept_related_concepts is None:
                        for related_concept in concept_related_concepts:
                            related_concept_id = related_concept["id"].replace("https://openalex.org/", "")
                            related_concept_uri = URIRef(soa_namespace_concepts+related_concept_id)
                            concept_graph.add((concept_uri,SKOS.related,related_concept_uri))

                    #counts_by_year
                    concept_counts_by_year = json_data['counts_by_year']
                    if not concept_counts_by_year is None:
                        for count_year in concept_counts_by_year:
                            count_year_year = count_year["year"]
                            count_year_uri = URIRef(soa_namespace_countsbyyear + concept_id + 'Y' + str(count_year_year))
                            concept_graph.add((count_year_uri,RDF.type,soa_class_counts_by_year))
                            concept_graph.add((concept_uri,counts_by_year_predicate,count_year_uri))
                            concept_graph.add((count_year_uri,year_predicate,Literal(count_year_year,datatype=XSD.integer)))
                            count_year_works_count = count_year["works_count"]
                            concept_graph.add((count_year_uri,works_count_predicate,Literal(count_year_works_count,datatype=XSD.integer)))
                            count_year_cited_by_count = count_year["cited_by_count"]
                            concept_graph.add((count_year_uri,cited_by_count_predicate,Literal(count_year_cited_by_count,datatype=XSD.integer)))

                    #works_api_url
                    #to-do

                    #updated_date
                    concept_updated_date = json_data['updated_date']
                    if not concept_updated_date is None:
                        concept_graph.add((concept_uri,DCTERMS.modified,Literal(concept_updated_date,datatype=XSD.date)))


                    #created_date
                    concept_created_date = json_data['created_date']
                    if not concept_created_date is None:
                        concept_graph.add((concept_uri,DCTERMS.created,Literal(concept_created_date,datatype=XSD.date)))

                    i += 1
                    if i % 10000 == 0:
                        print('Processed concepts entity {} lines'.format(i))

                    if i % 20000 == 0:
                        g.write(concept_graph.serialize(format='trig'))
                        concept_graph = Graph(identifier=context)


                except Exception as e:
                    print(str((e)) + ' Error in concepts entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the last part
    if not i % 20000 == 0:
        g.write(concept_graph.serialize(format='trig'))
        concept_graph = Graph(identifier=context)

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
