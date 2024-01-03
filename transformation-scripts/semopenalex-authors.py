# Copyright Johan Krause, Michael Färber, David Lamprecht; Institute AIFB, Karlsruhe Institute of Technology (KIT)
# this script transforms OpenAlex data dump files for author entities to triple form in trig files for SemOpenAlex
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import DCTERMS, FOAF, ORG, OWL, RDF, RDFS, XSD
import json
import os
import glob
import gzip
import re
import time
import boto3
from datetime import date
from multiprocessing import Pool
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
soa_namespace_authors = "https://semopenalex.org/author/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"
soa_namespace_works = "https://semopenalex.org/work/"
soa_namespace_institutions = "https://semopenalex.org/institution/"

# SOA classes used in this file
soa_class_author = URIRef(soa_namespace_class+"Author")
soa_class_counts_by_year = URIRef(soa_namespace_class+"CountsByYear")

# SOA predicates
orcid_predicate = URIRef("https://dbpedia.org/ontology/orcidId")
alt_name_predicate = URIRef("https://semopenalex.org/ontology/alternativeName")
works_count_predicate = URIRef("https://semopenalex.org/ontology/worksCount")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")
mag_id_predicate = URIRef("https://semopenalex.org/ontology/magId")
twitter_predicate = URIRef("https://dbpedia.org/property/twitter")
scopus_predicate = URIRef("https://dbpedia.org/property/scopus")
counts_by_year_predicate = URIRef("https://semopenalex.org/ontology/countsByYear")
year_predicate = URIRef("https://semopenalex.org/ontology/year")
mean_citedness_predicate = URIRef("https://semopenalex.org/ontology/2YrMeanCitedness")
h_index_predicate = URIRef("http://purl.org/spar/bido/h-index")
i10_index_predicate = URIRef("https://semopenalex.org/ontology/i10Index")

# authors entity context
context = URIRef("https://semopenalex.org/authors/context")

today = date.today()

##########
CPU_THREADS = 16
ENTITY_TYPE = 'authors'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'
data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, f'../graphdb-preload/graphdb-import/{ENTITY_TYPE}')

trig_output_file_path = f'{trig_output_dir_path}/{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('authors entity files started to download at: '+ data_dump_start_time)
# Copy authors entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/authors/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('authors entity files finished to download.')

start_time = time.ctime()
print(f"Overall authors entity start -- {start_time}.")


# collect all .gz parts of works data dump to iterate over with multiple workers (see no. of CPU THREADS above)
gz_file_list = []
for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
    gz_file_list.append(filename)


def transform_gz_file(gz_file_path):

    author_graph = Graph(identifier=context)
    gz_file_name = gz_file_path[len(gz_file_list[1])-39:].replace(".gz","").replace("/","_")
    file_error_count = 0

    with open(f"{trig_output_dir_path}/{gz_file_name}.trig", "w", encoding="utf-8") as g:
        with gzip.open(gz_file_path, 'r') as f:
            i = 0
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    #author ID and URI
                    author_id = json_data['id'].replace("https://openalex.org/", "")
                    author_uri = URIRef(soa_namespace_authors+author_id)
                    author_graph.add((author_uri,RDF.type,soa_class_author))

                    #ORCID
                    author_orcid = json_data['orcid']
                    if not author_orcid is None:
                        author_graph.add((author_uri,orcid_predicate,Literal(author_orcid,datatype=XSD.string)))

                    #display name
                    author_display_name = json_data['display_name']
                    if not author_display_name is None:
                        author_display_name = clean(author_display_name)
                        author_graph.add((author_uri, FOAF.name, Literal(author_display_name, datatype=XSD.string)))

                    # display_name_alternatives
                    author_display_name_alternatives = json_data['display_name_alternatives']
                    if not author_display_name_alternatives is None:
                        for alt_name in author_display_name_alternatives:
                            alt_name = clean(alt_name)
                            author_graph.add((author_uri, alt_name_predicate, Literal(alt_name, datatype=XSD.string)))

                    # summary stats
                    author_2yr_mean_citedness = json_data.get('summary_stats').get('2yr_mean_citedness')
                    if not author_2yr_mean_citedness is None:
                        author_graph.add((author_uri, mean_citedness_predicate,
                                             Literal(author_2yr_mean_citedness, datatype=XSD.float)))

                    author_h_index = json_data.get('summary_stats').get('h_index')
                    if not author_h_index is None:
                        author_graph.add(
                            (author_uri, h_index_predicate, Literal(author_h_index, datatype=XSD.integer)))

                    author_i10_index = json_data.get('summary_stats').get('i10_index')
                    if not author_i10_index is None:
                        author_graph.add(
                            (author_uri, i10_index_predicate, Literal(author_i10_index, datatype=XSD.integer)))


                    # works_count
                    author_works_count = json_data['works_count']
                    if not author_works_count is None:
                        author_graph.add((author_uri, works_count_predicate, Literal(author_works_count, datatype=XSD.integer)))

                    # cited_by_count
                    author_cited_by_count = json_data['cited_by_count']
                    if not author_cited_by_count is None:
                        author_graph.add((author_uri, cited_by_count_predicate, Literal(author_cited_by_count, datatype=XSD.integer)))

                    # ids (relevant: mag, twitter, wikipedia, scopus)
                    author_mag_id = json_data.get('ids').get('mag')
                    if not author_mag_id is None:
                        author_graph.add((author_uri,mag_id_predicate,Literal(author_mag_id,datatype=XSD.integer)))
                        mag_id_URI = URIRef("https://makg.org/entity/"+str(author_mag_id))
                        author_graph.add((author_uri,OWL.sameAs,mag_id_URI))

                    author_twitter = json_data.get('ids').get('twitter')
                    if not author_twitter is None:
                        author_graph.add((author_uri, twitter_predicate, Literal(clean_url(author_twitter), datatype=XSD.string)))

                    author_wikipedia = json_data.get('ids').get('wikipedia')
                    if not author_wikipedia is None:
                        author_wikipedia_URI = URIRef(clean_url(author_wikipedia))
                        author_graph.add((author_uri, RDFS.seeAlso, author_wikipedia_URI))

                    author_scopus = json_data.get('ids').get('scopus')
                    if not author_scopus is None:
                        author_graph.add((author_uri, scopus_predicate, Literal(clean_url(author_scopus), datatype=XSD.string)))

                    #last known affiliated institution
                    last_known_institution = json_data['last_known_institution']
                    if not last_known_institution is None:
                        last_known_institution_id = json_data['last_known_institution']['id'].replace("https://openalex.org/", "")
                        last_known_institution_uri = URIRef(soa_namespace_institutions + last_known_institution_id)
                        author_graph.add((author_uri, ORG.memberOf, last_known_institution_uri))

                    #counts by year in separate entity
                    author_counts_by_year = json_data['counts_by_year']
                    if not author_counts_by_year is None:
                        for count_year in author_counts_by_year:  # iterate through yearly dicts
                            count_year_year = count_year["year"]
                            count_year_uri = URIRef(soa_namespace_countsbyyear + author_id + 'Y' + str(count_year_year))
                            author_graph.add((count_year_uri, RDF.type, soa_class_counts_by_year))
                            author_graph.add((author_uri, counts_by_year_predicate, count_year_uri))
                            author_graph.add((count_year_uri, year_predicate, Literal(count_year_year, datatype=XSD.integer)))
                            author_graph.add((count_year_uri, works_count_predicate,Literal(count_year["works_count"], datatype=XSD.integer)))
                            author_graph.add((count_year_uri, cited_by_count_predicate,Literal(count_year["cited_by_count"], datatype=XSD.integer)))


                    # updated_date
                    author_updated_date = json_data['updated_date']
                    if not author_updated_date is None:
                        author_graph.add((author_uri, DCTERMS.modified, Literal(author_updated_date, datatype=XSD.date)))

                    # created_date
                    author_created_date = json_data['created_date']
                    if not author_created_date is None:
                        author_graph.add((author_uri, DCTERMS.created, Literal(author_created_date, datatype=XSD.date)))

                    i += 1
                    if i % 20000 == 0:
                        print('Processed {} lines'.format(i))

                    if i % 100000 == 0:
                        g.write(author_graph.serialize(format='trig'))
                        author_graph = Graph(identifier=context)


                except Exception as e:
                    print(str((e)) + f' Error in file {gz_file_path} in line {i+1}' + str(i + 1 + file_error_count))
                    file_error_count += 1
                    pass

                if i % 50000 == 0:
                    print(f'Processed authors entity {i} lines in file {gz_file_path}')

                if i % 50000 == 0:
                    g.write(author_graph.serialize(format='trig'))
                    author_graph = Graph(identifier=context)

            # Write the last part
            if not i % 50000 == 0:
                g.write(author_graph.serialize(format='trig'))
                author_graph = Graph(identifier=context)

    f.close()
    g.close()

    print(f"Worker completed .trig authors transformation with {i} lines and {file_error_count} errors")

    # gzip file directly with command
    # -v for live output, --fast for faster compression with about 90% size reduction, -k for keeping the original .trig file
    os.system(f'gzip --fast {trig_output_dir_path}/{gz_file_name}.trig')
    print("Worker completed gzip")


if __name__ == '__main__':
    pool = Pool(CPU_THREADS,maxtasksperchild=5)
    pool.map(transform_gz_file, gz_file_list)
    pool.close()

end_time = time.ctime()

with open(f"{trig_output_dir_path}/{ENTITY_TYPE}-transformation-summary.txt", "w") as z:
    z.write('Start Time: {} .\n'.format(start_time))
    z.write('Files processed: {} .\n'.format(len(gz_file_list)))
    z.write('End Time: {} .\n'.format(end_time))
    z.close()

print("Done authors transformation")
print("#############################")

