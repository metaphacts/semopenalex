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
soa_namespace_class = "https://semopenalex.org/ontology/"
soa_namespace_geo = "https://semopenalex.org/geo/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"
soa_namespace_funders = "https://semopenalex.org/funder/"
soa_namespace_publishers = "https://semopenalex.org/publisher/"
soa_namespace_institutions = "https://semopenalex.org/institution/"

# SOA classes used in this file
soa_class_funder = URIRef(soa_namespace_class + "Funder")
soa_class_counts_by_year = URIRef(soa_namespace_class + "CountsByYear")

# institutions entity context
context = URIRef("https://semopenalex.org/funders/context")

i = 0
error_count = 0
funders_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'funders'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('funders entity files started to download at: '+ data_dump_start_time)
# Copy institutions entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/funders/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('funders entity files finished to download.')

start_time = time.ctime()
print('funders entity started to transform at: '+ start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:

    #Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # Funder-ID
                    funder_id = json_data['id'].replace("https://openalex.org/", "")
                    funder_uri = URIRef(soa_namespace_funders+funder_id)
                    funders_graph.add((funder_uri, RDF.type, soa_class_funder))

                    # display_name
                    funder_display_name = json_data['display_name']
                    if not funder_display_name is None:
                        funder_display_name = clean(funder_display_name)
                        funders_graph.add((funder_uri, FOAF.name, Literal(funder_display_name,datatype=XSD.string)))

                    # alternate_titles
                    funder_alternate_titles = json_data['alternate_titles']
                    if not funder_alternate_titles is None:
                        for funder_alternative in funder_alternate_titles:
                            funder_alternative = clean(funder_alternative)
                            funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/alternativeName"), Literal(funder_alternative,datatype=XSD.string)))

                    # country_code
                    funder_country_code = json_data['country_code']
                    if not funder_country_code is None:
                        funders_graph.add((funder_uri, URIRef("https://dbpedia.org/property/countryCode"), Literal(funder_country_code,datatype=XSD.string)))

                    # description
                    funder_description = json_data['description']
                    if not funder_description is None:
                        funder_description = clean(funder_description)
                        funders_graph.add((funder_uri, URIRef("http://purl.org/dc/terms/description"), Literal(funder_description,datatype=XSD.string)))

                    # homepage_url
                    funder_homepage_url = json_data['homepage_url']
                    if not funder_homepage_url is None:
                        funders_graph.add((funder_uri, FOAF.homepage, Literal(clean_url(funder_homepage_url), datatype=XSD.string)))

                    # image_url
                    funder_image_url = json_data['image_url']
                    if not funder_image_url is None:
                        funders_graph.add((funder_uri, FOAF.depiction, Literal(clean_url(funder_image_url),datatype=XSD.string)))

                    # image_thumbnail_url
                    funder_image_thumbnail_url = json_data['image_thumbnail_url']
                    if not funder_image_thumbnail_url is None:
                        funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/imageThumbnail"), Literal(clean_url(funder_image_thumbnail_url),datatype=XSD.string)))
                    
                    # grants_count
                    funder_grants_count = json_data['grants_count']
                    if not funder_grants_count is None:
                        funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/grantsCount"), Literal(funder_grants_count,datatype=XSD.integer)))

                    # works_count
                    funder_works_count = json_data['works_count']
                    if not funder_works_count is None:
                        funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/worksCount"), Literal(funder_works_count,datatype=XSD.integer)))

                    # cited_by_count
                    funder_cited_by_count = json_data['cited_by_count']
                    if not funder_cited_by_count is None:
                        funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/citedByCount"), Literal(funder_cited_by_count,datatype=XSD.integer)))

                    # summary stats
                    funder_2yr_mean_citedness = json_data.get('summary_stats').get('2yr_mean_citedness')
                    if not funder_2yr_mean_citedness is None:
                        funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/2YrMeanCitedness"),
                                             Literal(funder_2yr_mean_citedness, datatype=XSD.float)))

                    funder_h_index = json_data.get('summary_stats').get('h_index')
                    if not funder_h_index is None:
                        funders_graph.add(
                            (funder_uri, URIRef("http://purl.org/spar/bido/h-index"), Literal(funder_h_index, datatype=XSD.integer)))

                    funder_i10_index = json_data.get('summary_stats').get('i10_index')
                    if not funder_i10_index is None:
                        funders_graph.add(
                            (funder_uri, URIRef("https://semopenalex.org/ontology/i10Index"), Literal(funder_i10_index, datatype=XSD.integer)))

                    # ids 
                    ror = json_data.get('ids').get('ror')
                    if not ror is None:
                        funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/ror"), Literal(ror, datatype= XSD.anyURI)))
                            
                    wikidata = json_data.get('ids').get('wikidata')
                    if not wikidata is None:
                        funders_graph.add((funder_uri, OWL.sameAs, URIRef(wikidata)))
                            
                    crossref = json_data.get('ids').get('crossref')
                    if not crossref is None:
                        funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/crossref"), Literal(crossref, datatype= XSD.string)))
                            
                    doi = json_data.get('ids').get('doi')
                    if not doi is None:
                        funders_graph.add((funder_uri, URIRef("http://prismstandard.org/namespaces/basic/2.0/doi"), Literal(doi, datatype= XSD.anyURI)))

                    #counts_by_year
                    funder_counts_by_year = json_data['counts_by_year']
                    if not funder_counts_by_year is None:
                        for count_year in funder_counts_by_year:
                            count_year_year = count_year["year"]
                            count_year_works_count = count_year["works_count"]
                            count_year_cited_by_count =  count_year["cited_by_count"]
                            count_year_uri = URIRef(soa_namespace_countsbyyear + funder_id + 'Y' + str(count_year_year))

                            funders_graph.add((count_year_uri,RDF.type,soa_class_counts_by_year))
                            funders_graph.add((funder_uri, URIRef("https://semopenalex.org/ontology/countsByYear"), count_year_uri))
                            funders_graph.add((count_year_uri, URIRef("https://semopenalex.org/ontology/year"), Literal(count_year_year,datatype=XSD.integer)))
                            funders_graph.add((count_year_uri, URIRef("https://semopenalex.org/ontology/worksCount"), Literal(count_year_works_count,datatype=XSD.integer)))
                            funders_graph.add((count_year_uri, URIRef("https://semopenalex.org/ontology/citedByCount"), Literal(count_year_cited_by_count,datatype=XSD.integer)))

                    #roles
                    funder_roles = json_data['roles']
                    if not funder_roles is None:
                        for role in funder_roles:
                            role_role = role["role"]

                            # publisher
                            if role_role == "publisher":
                                role_id = role["id"].replace("https://openalex.org/", "")
                                role_uri = URIRef(soa_namespace_publishers + role_id)
                                funders_graph.add((funder_uri, OWL.sameAs, role_uri))

                            # institution
                            if role_role == "institution":
                                role_id = role["id"].replace("https://openalex.org/", "")
                                role_uri = URIRef(soa_namespace_institutions + role_id)
                                funders_graph.add((funder_uri, OWL.sameAs, role_uri))

                    #updated_date
                    funder_updated_date = json_data['updated_date']
                    if not funder_updated_date is None:
                        funders_graph.add((funder_uri, DCTERMS.modified, Literal(funder_updated_date,datatype=XSD.date)))

                    #created_date
                    funder_created_date = json_data['created_date']
                    if not funder_created_date is None:
                        funders_graph.add((funder_uri, DCTERMS.created, Literal(funder_created_date,datatype=XSD.date)))

                    i += 1
                    if i % 10000 == 0:
                        print('Processed funders entity {} lines'.format(i))

                    if i % 20000 == 0:
                        g.write(funders_graph.serialize(format='trig'))
                        funders_graph = Graph(identifier=context)

                except Exception as e:
                    print(str((e)) + ' Error in funders entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the last part
    if not i % 20000 == 0:
        g.write(funders_graph.serialize(format='trig'))
        funders_graph = Graph(identifier=context)

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
