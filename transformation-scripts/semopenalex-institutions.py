# Copyright Johan Krause, Michael Färber, David Lamprecht; Institute AIFB, Karlsruhe Institute of Technology (KIT)
# this script transforms OpenAlex data dump files for institution entities to triple form in trig files for SemOpenAlex
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
soa_namespace_institutions = "https://semopenalex.org/institution/"

# SOA classes used in this file
soa_class_institution = URIRef(soa_namespace_class+"Institution")
soa_class_geo = URIRef(soa_namespace_class+"Geo")
soa_class_counts_by_year = URIRef(soa_namespace_class+"CountsByYear")

# SOA predicates
ror_predicate = URIRef("https://semopenalex.org/ontology/ror")
country_code_dbpedia_predicate = URIRef("https://dbpedia.org/property/countryCode")
ror_type_predicate = URIRef("https://semopenalex.org/ontology/rorType")
image_thumbnail_predicate = URIRef("https://semopenalex.org/ontology/imageThumbnail")
acronym_predicate = URIRef("https://dbpedia.org/property/acronym")
alt_name_predicate = URIRef("https://dbpedia.org/ontology/alternativeName")
works_count_predicate = URIRef("https://semopenalex.org/ontology/worksCount")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")
counts_by_year_predicate = URIRef("https://semopenalex.org/ontology/countsByYear")
mag_id_predicate = URIRef("https://semopenalex.org/ontology/magId")
grid_property = URIRef("https://semopenalex.org/ontology/grid")
location_predicate = URIRef("https://dbpedia.org/ontology/location")
geoname_id_predicate = URIRef("http://www.geonames.org/ontology#geonamesID")
city_predicate = URIRef("https://dbpedia.org/property/city")
region_predicate = URIRef("https://dbpedia.org/property/region")
country_predicate = URIRef("https://dbpedia.org/property/country")
country_code_geo_predicate = URIRef("http://www.geonames.org/ontology#countryCode")
lat_geo_predicate = URIRef("http://www.geonames.org/ontology#lat")
long_geo_predicate = URIRef("http://www.geonames.org/ontology#long")
associated_institution_predicate = URIRef("https://semopenalex.org/ontology/hasAssociatedInstitution")
year_predicate = URIRef("https://semopenalex.org/ontology/year")

# institutions entity context
context = URIRef("https://semopenalex.org/institutions/context")

i = 0
error_count = 0
institutions_graph = Graph(identifier=context)

today = date.today()

##########
ENTITY_TYPE = 'institutions'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}{ENTITY_TYPE}-semopenalex-{today}.trig'

data_dump_start_time = time.ctime()
print('institutions entity files started to download at: '+ data_dump_start_time)
# Copy institutions entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/institutions/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('institutions entity files finished to download.')

start_time = time.ctime()
print('institutions entity started to transform at: '+ start_time)

with open(trig_output_file_path, "w", encoding="utf-8") as g:

    #Path where the OpenAlex data for the current entity type is located
    data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

    for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
        with gzip.open(filename, 'r') as f:
            for line in f:
                try:
                    json_data = json.loads(line.decode('utf-8'))

                    # Institution-ID
                    institution_id = json_data['id'].replace("https://openalex.org/", "")
                    institution_uri = URIRef(soa_namespace_institutions+institution_id)
                    institutions_graph.add((institution_uri,RDF.type,soa_class_institution))

                    # ROR
                    institution_ror = json_data['ror']
                    if not institution_ror is None:
                        institutions_graph.add((institution_uri,ror_predicate,Literal(institution_ror,datatype=XSD.string)))

                    # display_name
                    institution_display_name = json_data['display_name']
                    if not institution_display_name is None:
                        institution_display_name = clean(institution_display_name)
                        institutions_graph.add((institution_uri,FOAF.name,Literal(institution_display_name,datatype=XSD.string)))

                    # country_code
                    institution_country_code = json_data['country_code']
                    if not institution_country_code is None:
                        institutions_graph.add((institution_uri,country_code_dbpedia_predicate,Literal(institution_country_code,datatype=XSD.string)))

                    # type
                    institution_type = json_data['type']
                    if not institution_type is None:
                        institutions_graph.add((institution_uri,ror_type_predicate,Literal(institution_type,datatype=XSD.string)))

                    # homepage_url
                    institution_homepage_url = json_data['homepage_url']
                    if not institution_homepage_url is None:
                        institutions_graph.add((institution_uri,FOAF.homepage,Literal(clean_url(institution_homepage_url),datatype=XSD.string)))

                    # image_url
                    institution_image_url = json_data['image_url']
                    if not institution_image_url is None:
                        institutions_graph.add((institution_uri,FOAF.depiction,Literal(clean_url(institution_image_url),datatype=XSD.string)))

                    # image_thumbnail_url
                    institution_image_thumbnail_url = json_data['image_thumbnail_url']
                    if not institution_image_thumbnail_url is None:
                        institutions_graph.add((institution_uri,image_thumbnail_predicate,Literal(clean_url(institution_image_thumbnail_url),datatype=XSD.string)))


                    # display_name_acronyms
                    institution_display_name_acronyms = json_data['display_name_acronyms']
                    if not institution_display_name_acronyms is None:
                        for institution_dnacronym in institution_display_name_acronyms:
                            institution_dnacronym = clean(institution_dnacronym)
                            institutions_graph.add((institution_uri,acronym_predicate,Literal(institution_dnacronym,datatype=XSD.string)))

                    # display_name_alternatives
                    institution_display_name_alternatives = json_data['display_name_alternatives']
                    if not institution_display_name_alternatives is None:
                        for institution_dnalternative in institution_display_name_alternatives:
                            institution_dnalternative = clean(institution_dnalternative)
                            institutions_graph.add((institution_uri,alt_name_predicate,Literal(institution_dnalternative,datatype=XSD.string)))


                    #works_count
                    institution_works_count = json_data['works_count']
                    if not institution_works_count is None:
                        institutions_graph.add((institution_uri,works_count_predicate,Literal(institution_works_count,datatype=XSD.integer)))

                    #cited_by_count
                    institution_cited_by_count = json_data['cited_by_count']
                    if not institution_cited_by_count is None:
                        institutions_graph.add((institution_uri,cited_by_count_predicate,Literal(institution_cited_by_count,datatype=XSD.integer)))

                    #ids (relevant: mag, grid, wikipedia, wikidata)
                    institution_mag_id = json_data.get('ids').get('mag')
                    if not institution_mag_id is None:
                        institutions_graph.add((institution_uri,mag_id_predicate,Literal(institution_mag_id,datatype=XSD.integer)))
                        mag_id_uri = URIRef("https://makg.org/entity/" + str(institution_mag_id))
                        institutions_graph.add((institution_uri,OWL.sameAs,mag_id_uri))

                    institution_grid = json_data.get('ids').get('grid')
                    if not institution_grid is None:
                        institutions_graph.add((institution_uri,grid_property,Literal(institution_grid,datatype=XSD.string)))

                    institution_wikipedia = json_data.get('ids').get('wikipedia')
                    if not institution_wikipedia is None:
                        institutions_graph.add((institution_uri,RDFS.seeAlso,Literal(clean_url(institution_wikipedia),datatype=XSD.string)))

                    institution_wikidata = json_data.get('ids').get('wikidata')
                    if not institution_wikidata == None:
                        institutions_graph.add((institution_uri,OWL.sameAs,Literal(clean_url(institution_wikidata),datatype=XSD.string)))

                    #geo
                    institution_geo = json_data['geo']
                    if not institution_geo is None:
                        geo_uri = URIRef(soa_namespace_geo+institution_id)
                        institutions_graph.add((geo_uri,RDF.type,soa_class_geo))
                        institutions_graph.add((institution_uri,location_predicate,geo_uri))

                        geo_city = institution_geo['city']
                        if not geo_city is None:
                            institutions_graph.add((geo_uri,city_predicate,Literal(geo_city,datatype=XSD.string)))

                        geo_geonames_city_id = institution_geo['geonames_city_id']
                        if not geo_geonames_city_id is None:
                            institutions_graph.add((geo_uri,geoname_id_predicate,Literal(geo_geonames_city_id,datatype=XSD.string)))

                        geo_region = institution_geo['region']
                        if not geo_region is None:
                            institutions_graph.add((geo_uri,region_predicate,Literal(geo_region,datatype=XSD.string)))

                        geo_country_code = institution_geo['country_code']
                        if not geo_country_code is None:
                            institutions_graph.add((geo_uri,country_code_geo_predicate,Literal(geo_country_code,datatype=XSD.string)))

                        geo_country = institution_geo['country']
                        if not geo_country is None:
                            institutions_graph.add((geo_uri,country_predicate,Literal(geo_country,datatype=XSD.string)))

                        geo_latitude = institution_geo['latitude']
                        if not geo_latitude is None:
                            institutions_graph.add((geo_uri,lat_geo_predicate,Literal(geo_latitude,datatype=XSD.float)))

                        geo_longitude = institution_geo['longitude']
                        if not geo_longitude == None:
                            institutions_graph.add((geo_uri,long_geo_predicate,Literal(geo_longitude,datatype=XSD.float)))


                    #international
                    #to do

                    #associated_institutions
                    institution_associated_institutions = json_data.get('associated_institutions')
                    if not institution_associated_institutions is None:
                        for associated_institution in institution_associated_institutions:
                            associated_institution_id = associated_institution["id"].replace("https://openalex.org/", "")
                            associated_institution_uri = URIRef(soa_namespace_institutions+associated_institution_id)
                            institutions_graph.add((institution_uri,associated_institution_predicate,associated_institution_uri))

                    #counts_by_year
                    institution_counts_by_year = json_data['counts_by_year']
                    if not institution_counts_by_year is None:
                        for count_year in institution_counts_by_year:
                            count_year_year = count_year["year"]
                            count_year_works_count = count_year["works_count"]
                            count_year_cited_by_count =  count_year["cited_by_count"]
                            count_year_uri = URIRef(soa_namespace_countsbyyear + institution_id + 'Y' + str(count_year_year))

                            institutions_graph.add((count_year_uri,RDF.type,soa_class_counts_by_year))
                            institutions_graph.add((institution_uri,counts_by_year_predicate,count_year_uri))
                            institutions_graph.add((count_year_uri,year_predicate,Literal(count_year_year,datatype=XSD.integer)))
                            institutions_graph.add((count_year_uri,works_count_predicate,Literal(count_year_works_count,datatype=XSD.integer)))
                            institutions_graph.add((count_year_uri,cited_by_count_predicate,Literal(count_year_cited_by_count,datatype=XSD.integer)))

                    #works_api_url
                    #to do

                    #updated_date
                    institution_updated_date = json_data['updated_date']
                    if not institution_updated_date is None:
                        institutions_graph.add((institution_uri,DCTERMS.modified,Literal(institution_updated_date,datatype=XSD.date)))

                    #created_date
                    institution_created_date = json_data['created_date']
                    if not institution_created_date is None:
                        institutions_graph.add((institution_uri,DCTERMS.created,Literal(institution_created_date,datatype=XSD.date)))

                    i += 1
                    if i % 10000 == 0:
                        print('Processed institutions entity {} lines'.format(i))

                    if i % 20000 == 0:
                        g.write(institutions_graph.serialize(format='trig'))
                        institutions_graph = Graph(identifier=context)



                except Exception as e:
                    print(str((e)) + ' Error in institutions entity line ' + str(i + 1 + error_count))
                    error_count += 1
                    pass

    # Write the last part
    if not i % 20000 == 0:
        g.write(institutions_graph.serialize(format='trig'))
        institutions_graph = Graph(identifier=context)

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
