# Copyright Johan Krause, Michael Färber, David Lamprecht; Institute AIFB, Karlsruhe Institute of Technology (KIT)
# this script transforms OpenAlex data dump files for work entities to triple form in trig files for SemOpenAlex
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, OWL
from rdflib import term
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


def inverted_to_plain_text(invertedIndex):
    abstract_index = {}
    for key_string, word_positions in invertedIndex.items():
        for position in word_positions:
            abstract_index[position] = key_string
    abstract = ' '.join(abstract_index[k] for k in sorted(abstract_index.keys()))
    return abstract

def clean_date(dateStr):
    return dateStr.split("T")[0]

def correct_uri_from_https_to_http(uri):
    return uri.replace("https://", "http://")

# method to validate the keyword URIs. Only valid URIs are returned, otherwise None.
def validate_keyword_uri(keyword_uri):
    if keyword_uri.startswith('https://semopenalex.org/keyword/'):
        suffix = keyword_uri[len('https://semopenalex.org/keyword/'):]
        suffix = suffix.replace(',', '-')
        if re.match(r'^[a-zA-Z0-9\-]+$', suffix):
            return 'https://semopenalex.org/keyword/' + suffix
        else:
            return None
    else:
        return None

# info for namespaces used in SOA
soa_namespace_class = "https://semopenalex.org/ontology/"
soa_namespace_authors = "https://semopenalex.org/author/"
soa_namespace_authorship = "https://semopenalex.org/authorship/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsByYear/"
soa_namespace_works = "https://semopenalex.org/work/"
soa_namespace_institutions = "https://semopenalex.org/institution/"
soa_namespace_open_access = "https://semopenalex.org/openaccess/"
soa_namespace_concept = "https://semopenalex.org/concept/"
soa_namespace_concept_score = "https://semopenalex.org/conceptscore/"
soa_namespace_sources = "https://semopenalex.org/source/"
soa_namespace_funders = "https://semopenalex.org/funder/"
soa_namespace_locations = "https://semopenalex.org/location/"
soa_namespace_apc_list = "https://semopenalex.org/articleProcessingChargeList/"
soa_namespace_apc_paid = "https://semopenalex.org/articleProcessingChargePaid/"
soa_namespace_topics = "https://semopenalex.org/topic/"

# SOA classes used in this file
soa_class_work = URIRef(soa_namespace_class + "Work")
soa_class_location = URIRef(soa_namespace_class + "Location")
soa_class_open_access = URIRef(soa_namespace_class + "OpenAccess")
soa_class_authorship = URIRef(soa_namespace_class + "Authorship")
soa_class_counts_by_year = URIRef(soa_namespace_class + "CountsByYear")
soa_class_concept = URIRef(soa_namespace_class + "Concept")
soa_class_concept_score = URIRef(soa_namespace_class + "ConceptScore")
soa_class_apc = URIRef(soa_namespace_class + "ArticleProcessingCharge")

# SOA predicates
doi_predicate = URIRef("http://purl.org/spar/datacite/doi")
publication_year_predicate = URIRef("http://purl.org/spar/fabio/hasPublicationYear")
publication_date_predicate = URIRef("http://prismstandard.org/namespaces/basic/2.0/publicationDate")
mag_id_predicate = URIRef("https://semopenalex.org/ontology/magId")
pubmed_id_predicate = URIRef("http://purl.org/spar/fabio/hasPubMedId")
pubmed_central_predicate = URIRef("http://purl.org/spar/fabio/hasPubMedCentralId")
url_predicate = URIRef("http://purl.org/spar/fabio/hasURL")
is_oa_predicate = URIRef("https://semopenalex.org/ontology/isOa")
has_oa_predicate = URIRef("https://semopenalex.org/ontology/hasOpenAccess")
oa_status_predicate = URIRef("https://semopenalex.org/ontology/oaStatus")
oa_url_predicate = URIRef("https://semopenalex.org/ontology/oaUrl")
oa_any_repository_has_fulltext_predicate = URIRef("https://semopenalex.org/ontology/anyRepositoryHasFulltext")
version_predicate = URIRef("https://semopenalex.org/ontology/hasVersion")
crossref_type_predicate = URIRef("https://semopenalex.org/ontology/crossrefType")
work_type_predicate = URIRef("https://semopenalex.org/ontology/workType")
has_authorship_predicate = URIRef("https://semopenalex.org/ontology/hasAuthorship")
has_organization_predicate = URIRef("https://semopenalex.org/ontology/hasOrganization")
author_position_predicate = URIRef("https://semopenalex.org/ontology/position")
author_corresponding_predicate = URIRef("https://semopenalex.org/ontology/isCorresponding")
author_raw_affiliation_predicate = URIRef("https://semopenalex.org/ontology/rawAffiliation")
has_author_predicate = URIRef("https://semopenalex.org/ontology/hasAuthor")
cited_by_count_predicate = URIRef("https://semopenalex.org/ontology/citedByCount")
counts_by_year_predicate = URIRef("https://semopenalex.org/ontology/countsByYear")
has_volume_predicate = URIRef("https://semopenalex.org/ontology/hasVolume")
has_issue_predicate = URIRef("https://semopenalex.org/ontology/hasIssue")
starting_page_predicate = URIRef("http://prismstandard.org/namespaces/basic/2.0/startingPage")
ending_page_predicate = URIRef("http://prismstandard.org/namespaces/basic/2.0/endingPage")
is_retracted_predicate = URIRef("https://semopenalex.org/ontology/isRetracted")
is_paratext_predicate = URIRef("https://semopenalex.org/ontology/isParatext")
has_concept_predicate = URIRef("https://semopenalex.org/ontology/hasConcept")
has_concept_score_predicate = URIRef("https://semopenalex.org/ontology/hasConceptScore")
score_predicate = URIRef("https://semopenalex.org/ontology/score")
cites_predicate = URIRef("http://purl.org/spar/cito/cites")
related_work_predicate = URIRef("https://semopenalex.org/ontology/hasRelatedWork")
year_predicate = URIRef("https://semopenalex.org/ontology/year")
country_code_dbpedia_predicate = URIRef("https://dbpedia.org/property/countryCode")
has_apc_list = URIRef("https://semopenalex.org/ontology/hasAPCList")
has_apc_paid = URIRef("https://semopenalex.org/ontology/hasAPCPaid")
has_value = URIRef("https://semopenalex.org/ontology/hasValue")
has_currency = URIRef("https://semopenalex.org/ontology/hasCurrency")
has_value_usd = URIRef("https://semopenalex.org/ontology/hasValueUSD")
has_provenance = URIRef("https://semopenalex.org/ontology/hasProvenance")
has_countries_distinct_count = URIRef("https://semopenalex.org/ontology/countriesDistinctCount")
indexed_in = URIRef("https://semopenalex.org/ontology/indexedIn")
has_institutions_distinct_count = URIRef("https://semopenalex.org/ontology/institutionsDistinctCount")
has_metadata_language = URIRef("https://semopenalex.org/ontology/metadataLanguage")
has_locations_count = URIRef("https://semopenalex.org/ontology/locationsCount")
has_sustainable_development_goal = URIRef("https://semopenalex.org/ontology/hasSustainableDevelopmentGoal")
has_topic_predicate = URIRef("https://semopenalex.org/ontology/hasTopic")
has_primary_topic_predicate = URIRef("https://semopenalex.org/ontology/hasPrimaryTopic")
has_keyword_predicate = URIRef("https://semopenalex.org/ontology/hasKeyword")
has_mesh_predicate = URIRef("https://semopenalex.org/ontology/hasMesh")
## changed:
has_location_predicate = URIRef("https://semopenalex.org/ontology/hasLocation")
has_primary_location_predicate = URIRef("https://semopenalex.org/ontology/hasPrimaryLocation")
has_best_oa_location_predicate = URIRef("https://semopenalex.org/ontology/hasBestOaLocation")
pdf_url_predicate = URIRef("https://semopenalex.org/ontology/pdfUrl")
has_source_predicate = URIRef("https://semopenalex.org/ontology/hasSource")

# works entity context
context = URIRef("https://semopenalex.org/works/context")

##########
CPU_THREADS = 16
ENTITY_TYPE = 'works'
##########

data_dump_input_root_dir = '/opt/openalex-snapshot'
data_dump_input_entity_dir = f'{data_dump_input_root_dir}/data/{ENTITY_TYPE}/*'

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, f'../graphdb-preload/graphdb-import/{ENTITY_TYPE}')

data_dump_start_time = time.ctime()
print('works entity files started to download at: ' + data_dump_start_time)
# Copy works entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/works/")
download_files(client, "openalex", data_dump_input_root_dir, file_names, folders)
print('works entity files finished to download.')

start_time = time.ctime()
today = date.today()
print(f"Overall work entity start -- {start_time}.")

# collect all .gz parts of works data dump to iterate over with multiple workers (see no. of CPU THREADS above)
gz_file_list = []
for filename in glob.glob(os.path.join(data_dump_input_entity_dir, '*.gz')):
    gz_file_list.append(filename)


def transform_gz_file(gz_file_path):
    works_graph = Graph(identifier=context)
    gz_file_name = gz_file_path[len(gz_file_list[1]) - 41:].replace(".gz", "").replace("/", "_")
    file_error_count = 0

    with open(f"{trig_output_dir_path}/{gz_file_name}.trig", "w", encoding="utf-8") as g:
        with gzip.open(gz_file_path, 'r') as f:
            i = 0
            for line in f:
                # read json object from current line in .jsonl
                try:
                    i += 1
                    json_data = json.loads(line.decode('utf-8'))

                except Exception as e:
                    print(
                        str((e)) + f'loading did not work in line (probably empty line in dump files) in line {i}')
                    pass

                # only continue reading of JSON if loading of line was successful and exception was not raised above
                else:
                    try:

                        # Work-ID
                        work_id = json_data['id'].replace("https://openalex.org/", "")
                        work_uri = URIRef(soa_namespace_works + work_id)
                        works_graph.add((work_uri, RDF.type, soa_class_work))

                        # doi
                        work_doi = json_data['doi']
                        if not work_doi is None:
                            works_graph.add((work_uri, doi_predicate, Literal(work_doi, datatype=XSD.string)))

                        # title
                        work_title = json_data['title']
                        if not work_title is None:
                            work_title = clean(work_title)
                            works_graph.add((work_uri, DCTERMS.title, Literal(work_title, datatype=XSD.string)))

                        # publication year
                        work_publication_year = json_data['publication_year']
                        if not work_publication_year is None:
                            works_graph.add((work_uri, publication_year_predicate,
                                            Literal(work_publication_year, datatype=XSD.integer)))

                        # publication date
                        work_publication_date = json_data['publication_date']
                        if not work_publication_date is None:
                            work_publication_date = clean(work_publication_date)
                            works_graph.add((work_uri, publication_date_predicate,
                                            Literal(work_publication_date, datatype=XSD.date)))

                        # ids (relevant: mag, pmid, pmcid)
                        work_mag_id = json_data.get('ids').get('mag')
                        if not work_mag_id is None:
                            works_graph.add((work_uri, mag_id_predicate, Literal(work_mag_id, datatype=XSD.integer)))
                            mag_id_uri = URIRef("https://makg.org/entity/" + str(work_mag_id))
                            works_graph.add((work_uri, OWL.sameAs, mag_id_uri))

                        work_pmid_id = json_data.get('ids').get('pmid')
                        if not work_pmid_id is None:
                            works_graph.add((work_uri, pubmed_id_predicate, Literal(work_pmid_id, datatype=XSD.string)))

                        work_pmcid_id = json_data.get('ids').get('pmcid')
                        if not work_pmcid_id is None:
                            works_graph.add(
                                (work_uri, pubmed_central_predicate, Literal(work_pmcid_id, datatype=XSD.string)))

                        # work location
                        work_locations = json_data['locations']
                        if not work_locations is None:
                            location_iter = 1
                            for work_location in work_locations:
                                work_location_uri = URIRef(soa_namespace_locations + str(work_id) + str(location_iter))
                                location_iter += 1
                                works_graph.add((work_location_uri, RDF.type, soa_class_location))
                                works_graph.add((work_uri, has_location_predicate, work_location_uri))

                                work_location_page_url = work_location['landing_page_url']
                                if not work_location_page_url is None:
                                    work_location_page_url = clean_url(work_location_page_url)
                                    works_graph.add((work_location_uri, url_predicate,
                                                    Literal(work_location_page_url, datatype=XSD.string)))

                                work_location_pdf_url = work_location['pdf_url']
                                if not work_location_pdf_url is None:
                                    work_location_pdf_url = clean_url(work_location_pdf_url)
                                    works_graph.add((work_location_uri, pdf_url_predicate,
                                                    Literal(work_location_pdf_url, datatype=XSD.string)))

                                work_location_is_oa = work_location['is_oa']
                                if not work_location_is_oa is None:
                                    works_graph.add((work_location_uri, is_oa_predicate,
                                                    Literal(work_location_is_oa, datatype=XSD.boolean)))

                                work_location_version = work_location['version']
                                if not work_location_version is None:
                                    work_location_version = clean(work_location_version)
                                    works_graph.add((work_location_uri, version_predicate,
                                                    Literal(work_location_version, datatype=XSD.string)))

                                work_location_license = work_location['license']
                                if not work_location_license is None:
                                    work_location_license = clean(work_location_license)
                                    works_graph.add((work_location_uri, DCTERMS.license,
                                                    Literal(work_location_license, datatype=XSD.string)))

                                # add additional relation if current location is the primary one
                                if work_location == json_data['primary_location']:
                                    works_graph.add((work_uri, has_primary_location_predicate, work_location_uri))

                                # add additional relation if current location is the best oa one, if any
                                work_best_oa_location = json_data['best_oa_location']
                                if not work_best_oa_location is None:
                                    if work_location == work_best_oa_location:
                                        works_graph.add((work_uri, has_best_oa_location_predicate, work_location_uri))

                                # link from location to source (was venue)
                                if not work_location['source'] is None:
                                    work_location_source_id = work_location['source']['id']
                                    if not work_location_source_id is None:
                                        work_location_source_id = work_location_source_id.replace(
                                            "https://openalex.org/", "")
                                        work_location_source_uri = URIRef(
                                            soa_namespace_sources + str(work_location_source_id))
                                        works_graph.add(
                                            (work_location_uri, has_source_predicate, work_location_source_uri))
                        # grants
                        work_grants = json_data.get('grants')
                        for grant in work_grants:
                            grant_id = grant.get('funder').replace("https://openalex.org/", "")
                            grant_uri = URIRef(soa_namespace_funders + str(grant_id))
                            works_graph.add((work_uri, URIRef("https://semopenalex.org/ontology/hasFunder"), grant_uri))

                        # type
                        work_type = json_data['type']
                        if not work_type is None:
                            work_type = str(work_type)
                            works_graph.add(
                                (work_uri, work_type_predicate, Literal(work_type, datatype=XSD.string)))

                        # crossref_type
                        work_crossref_type = json_data.get('type_crossref')
                        if not work_crossref_type is None:
                            work_crossref_type = str(work_crossref_type)
                            works_graph.add(
                                (work_uri, crossref_type_predicate, Literal(work_crossref_type, datatype=XSD.string)))

                        # open_access
                        work_open_access = json_data['open_access']
                        if not work_open_access is None:
                            work_open_access_uri = URIRef(soa_namespace_open_access + str(work_id))
                            works_graph.add((work_open_access_uri, RDF.type, soa_class_open_access))
                            works_graph.add((work_uri, has_oa_predicate, work_open_access_uri))

                            work_is_oa = json_data['open_access']['is_oa']
                            if not work_is_oa is None:
                                works_graph.add(
                                    (work_open_access_uri, is_oa_predicate, Literal(work_is_oa, datatype=XSD.boolean)))

                            work_oa_status = json_data['open_access']['oa_status']
                            if not work_oa_status is None:
                                works_graph.add((work_open_access_uri, oa_status_predicate,
                                                Literal(work_oa_status, datatype=XSD.string)))

                            work_oa_url = json_data['open_access']['oa_url']
                            if not work_oa_url is None:
                                work_oa_url = clean_url(work_oa_url)
                                works_graph.add(
                                    (work_open_access_uri, oa_url_predicate, Literal(work_oa_url, datatype=XSD.string)))
                                
                            work_oa_any_repository_has_fulltext = json_data['open_access']['any_repository_has_fulltext']
                            if not work_oa_any_repository_has_fulltext is None:
                                works_graph.add((
                                    work_open_access_uri, oa_any_repository_has_fulltext_predicate, Literal(work_oa_any_repository_has_fulltext, datatype=XSD.boolean)))

                        # authorship
                        work_authorships = json_data['authorships']
                        if not work_authorships is None:
                            for authorship in work_authorships:
                                authorship_id = authorship["author"]["id"].replace("https://openalex.org/", "")
                                authorship_uri = URIRef(soa_namespace_authors + str(authorship_id))
                                works_graph.add((work_uri, DCTERMS.creator, authorship_uri))

                        work_authorships = json_data['authorships']
                        if not work_authorships is None:
                            index = 0
                            for authorship in work_authorships:
                                author_isCorresponding = authorship["is_corresponding"]
                                authorship_id = authorship["author"]["id"].replace("https://openalex.org/", "")
                                work_authorship_uri = URIRef(
                                    soa_namespace_authorship + str(work_id) + str(authorship_id))
                                works_graph.add((work_authorship_uri, RDF.type, soa_class_authorship))
                                works_graph.add((work_uri, has_authorship_predicate, work_authorship_uri))
                                works_graph.add((work_authorship_uri, author_position_predicate,
                                                Literal(index, datatype=XSD.integer)))
                                works_graph.add((work_authorship_uri, author_corresponding_predicate,
                                                Literal(author_isCorresponding, datatype=XSD.boolean)))
                                author_raw_affiliation_string = authorship["raw_affiliation_strings"]
                                if not author_raw_affiliation_string is None:
                                    for affiliation in author_raw_affiliation_string:
                                        author_raw_affiliation_string = clean(affiliation)
                                        works_graph.add((work_authorship_uri, author_raw_affiliation_predicate, Literal(author_raw_affiliation_string, datatype=XSD.string)))
                                        
                                work_author_uri = URIRef(soa_namespace_authors + str(authorship_id))
                                works_graph.add((work_authorship_uri, has_author_predicate, work_author_uri))
                                index += 1

                                #institutions
                                institutions = authorship['institutions']
                                for institution in institutions:
                                    institution_id = institution["id"].replace("https://openalex.org/", "")
                                    institution_uri = URIRef(soa_namespace_institutions + str(institution_id))
                                    works_graph.add((work_authorship_uri, has_organization_predicate, institution_uri))
                                
                                #countries
                                author_country_code = authorship.get('countries')
                                if not author_country_code is None:
                                    for country in author_country_code:
                                        works_graph.add((work_authorship_uri, country_code_dbpedia_predicate, Literal(country, datatype=XSD.string)))


                        # cited_by_count
                        work_cited_by_count = json_data['cited_by_count']
                        if not work_cited_by_count is None:
                            works_graph.add((work_uri, cited_by_count_predicate,
                                            Literal(work_cited_by_count, datatype=XSD.integer)))

                        # biblo (bibliographic info)
                        work_biblio_volume = json_data['biblio']['volume']
                        if not work_biblio_volume is None:
                            work_biblio_volume = clean(work_biblio_volume)
                            works_graph.add(
                                (work_uri, has_volume_predicate, Literal(work_biblio_volume, datatype=XSD.string)))

                        work_biblio_issue = json_data['biblio']['issue']
                        if not work_biblio_issue is None:
                            work_biblio_issue = clean(work_biblio_issue)
                            works_graph.add(
                                (work_uri, has_issue_predicate, Literal(work_biblio_issue, datatype=XSD.string)))

                        work_biblio_first_page = json_data['biblio']['first_page']
                        if not work_biblio_first_page is None:
                            work_biblio_first_page = clean(work_biblio_first_page)
                            works_graph.add((work_uri, starting_page_predicate,
                                            Literal(work_biblio_first_page, datatype=XSD.string)))

                        work_biblio_last_page = json_data['biblio']['last_page']
                        if not work_biblio_last_page is None:
                            work_biblio_last_page = clean(work_biblio_last_page)
                            works_graph.add(
                                (work_uri, ending_page_predicate, Literal(work_biblio_last_page, datatype=XSD.string)))

                        # is_retracted
                        work_is_retracted = json_data['is_retracted']
                        if not work_is_retracted is None:
                            works_graph.add(
                                (work_uri, is_retracted_predicate, Literal(work_is_retracted, datatype=XSD.boolean)))

                        # is_paratext
                        work_is_paratext = json_data['is_paratext']
                        if not work_is_paratext is None:
                            works_graph.add(
                                (work_uri, is_paratext_predicate, Literal(work_is_paratext, datatype=XSD.boolean)))

                        # concepts
                        work_concepts = json_data['concepts']
                        if not work_concepts is None:
                            for concept in work_concepts:
                                concept_id = concept["id"].replace("https://openalex.org/", "")
                                concept_uri = URIRef(soa_namespace_concept + str(concept_id))
                                concept_score = concept["score"]
                    
                                ############## way of modeling concepts without scores as plain RDF triples if the concept score is greater than 0.3
                                if concept_score >= 0.3:
                                    works_graph.add((work_uri, has_concept_predicate, concept_uri))
                        

                        # referenced_works
                        work_referenced_works = json_data['referenced_works']
                        for ref_work in work_referenced_works:
                            if not ref_work is None:
                                ref_work = ref_work.replace("https://openalex.org/", "")
                                referenced_work_uri = URIRef(soa_namespace_works + str(ref_work))
                                works_graph.add((work_uri, cites_predicate, referenced_work_uri))

                        # related_works
                        work_related_works = json_data.get('related_works', [])[:5]  # Limit to maximum of 5 related works
                        if work_related_works:
                                for rel_work in work_related_works:
                                    if rel_work is not None:
                                        rel_work = rel_work.replace("https://openalex.org/", "")
                                        related_work_uri = URIRef(soa_namespace_works + str(rel_work))
                                        works_graph.add((work_uri, related_work_predicate, related_work_uri))

                        # cited_by_api_url
                        # is missing atm

                        # updated_date
                        work_updated_date = json_data['updated_date']
                        if not work_updated_date is None:
                            work_updated_date = clean_date(work_updated_date)
                            works_graph.add((work_uri, DCTERMS.modified, Literal(work_updated_date, datatype=XSD.date)))

                        # created_date
                        work_created_date = json_data['created_date']
                        if not work_created_date is None:
                            works_graph.add((work_uri, DCTERMS.created, Literal(work_created_date, datatype=XSD.date)))

                        # apc_list
                        work_apc_list = json_data.get('apc_list')
                        if not work_apc_list is None:
                            work_apc_list_value = work_apc_list.get('value')
                            work_apc_list_currency = work_apc_list.get('currency')
                            work_apc_list_value_usd = work_apc_list.get('value_usd')
                            work_apc_list_provenance = work_apc_list.get('provenance')

                            apc_list_uri = URIRef(soa_namespace_apc_list + str(work_id))
                            works_graph.add((apc_list_uri, RDF.type, soa_class_apc))
                            works_graph.add((work_uri, has_apc_list, apc_list_uri))

                            # check None values
                            if not work_apc_list_value is None:
                                works_graph.add((apc_list_uri, has_value, Literal(work_apc_list_value, datatype=XSD.integer)))

                            if not work_apc_list_currency is None:
                                works_graph.add((apc_list_uri, has_currency, Literal(work_apc_list_currency, datatype=XSD.string)))

                            if not work_apc_list_value_usd is None:
                                works_graph.add((apc_list_uri, has_value_usd, Literal(work_apc_list_value_usd, datatype=XSD.integer)))

                            if not work_apc_list_provenance is None:
                                works_graph.add((apc_list_uri, has_provenance, Literal(work_apc_list_provenance, datatype=XSD.string)))
            
                        # apc_paid
                        work_apc_paid = json_data.get('apc_paid')
                        if not work_apc_paid is None:
                            work_apc_paid_value = work_apc_paid.get('value')
                            work_apc_paid_currency = work_apc_paid.get('currency')
                            work_apc_paid_value_usd = work_apc_paid.get('value_usd')
                            work_apc_paid_provenance = work_apc_paid.get('provenance')

                            apc_paid_uri = URIRef(soa_namespace_apc_paid + str(work_id))
                            works_graph.add((apc_paid_uri, RDF.type, soa_class_apc))
                            works_graph.add((work_uri, has_apc_paid, apc_paid_uri))
                            
                            # check None values
                            if not work_apc_paid_value is None:
                                works_graph.add((apc_paid_uri, has_value, Literal(work_apc_paid_value, datatype=XSD.integer)))

                            if not work_apc_paid_currency is None:
                                works_graph.add((apc_paid_uri, has_currency, Literal(work_apc_paid_currency, datatype=XSD.string)))

                            if not work_apc_paid_value_usd is None:
                                works_graph.add((apc_paid_uri, has_value_usd, Literal(work_apc_paid_value_usd, datatype=XSD.integer)))

                            if not work_apc_paid_provenance is None:
                                works_graph.add((apc_paid_uri, has_provenance, Literal(work_apc_paid_provenance, datatype=XSD.string)))

                        # countries_distinct_count
                        work_countries_distinct_count = json_data.get('countries_distinct_count')
                        if not work_countries_distinct_count is None:
                            works_graph.add((work_uri, has_countries_distinct_count, Literal(work_countries_distinct_count, datatype=XSD.integer)))

                        # indexed_in
                        work_indexed_in = json_data.get('indexed_in')
                        if not work_indexed_in is None:
                            for index_source in work_indexed_in:
                                works_graph.add((work_uri, indexed_in, Literal(index_source, datatype=XSD.string)))

                        # institutions_distinct_count
                        work_institutions_distinct_count = json_data.get('institutions_distinct_count')
                        if not work_institutions_distinct_count is None:
                            works_graph.add((work_uri, has_institutions_distinct_count, Literal(work_institutions_distinct_count, datatype=XSD.integer)))

                        # keywords
                        work_keywords = json_data.get('keywords')
                        if not work_keywords is None:
                            for keyword in work_keywords:
                                keyword_uri = keyword['id'].replace("https://openalex.org/keywords/", "https://semopenalex.org/keyword/")
                                keyword_uri = validate_keyword_uri(keyword_uri)
                                keyword_score = keyword['score']
                                if not keyword_uri is None:
                                    keyword_uri = URIRef(keyword_uri)
                                    if term._is_valid_uri(keyword_uri):
                                        if keyword_score >= 0.5:
                                            works_graph.add((work_uri, has_keyword_predicate, keyword_uri))

                        # language
                        work_language = json_data['language']
                        if not work_language is None:
                            works_graph.add((work_uri, has_metadata_language, Literal(work_language, datatype=XSD.string)))

                        # locations_count
                        work_locations_count = json_data['locations_count']
                        if not work_locations_count is None:
                            works_graph.add((work_uri, has_locations_count, Literal(work_locations_count, datatype=XSD.integer)))

                        # mesh
                        work_mesh = json_data['mesh']
                        if not work_mesh is None:
                            for mesh in work_mesh:
                                descriptor_ui = mesh['descriptor_ui']
                                descriptor_ui = clean_url(descriptor_ui)
                                descriptor_ui_uri = URIRef("http://id.nlm.nih.gov/mesh/" + descriptor_ui)
                                works_graph.add((work_uri, has_mesh_predicate, descriptor_ui_uri))
                    
                        # primary_topic
                        work_primary_topic = json_data.get('primary_topic')
                        if not work_primary_topic is None:
                            primary_topic_id = work_primary_topic['id'].replace("https://openalex.org/", "")
                            primary_topic_uri = URIRef(soa_namespace_topics + str(primary_topic_id))
                            #primary_topic_score = work_primary_topic['score']

                            ############## way of modeling primary_topic without scores as plain RDF triple
                            works_graph.add((work_uri, has_primary_topic_predicate, primary_topic_uri))

                        # sustainable_development_goals
                        # see: https://research.un.org/en/thesaurus/downloads 
                        work_sustainable_development_goals = json_data['sustainable_development_goals']
                        if not work_sustainable_development_goals is None:
                            for goal in work_sustainable_development_goals:
                                goal_uri = goal['id']
                                goal_uri = correct_uri_from_https_to_http(goal_uri)
                                goal_uri = URIRef(goal_uri)
                                goal_score = goal['score']

                                ############## way of modeling sustainable_development_goals without scores as plain RDF triples if the goal score is greater than 0.4 (same threshold as OpenAlex)
                                if goal_score >= 0.4:
                                    works_graph.add((work_uri, has_sustainable_development_goal, goal_uri))


                        # topics
                        work_topics = json_data.get('topics')
                        if not work_topics is None:
                            for topic in work_topics:
                                topic_id = topic['id'].replace("https://openalex.org/", "")
                                topic_uri = URIRef(soa_namespace_topics + str(topic_id))
                                #topic_score = topic['score']

                                ############## way of modeling topics without scores as plain RDF triples
                                works_graph.add((work_uri, has_topic_predicate, topic_uri))


                    except Exception as e:
                        print(str((e)) + f' error - in file {gz_file_path} in line {i}')
                        file_error_count += 1
                        pass

                    # read abstract
                    try:
                        abstract_inverted_index = json_data['abstract_inverted_index']
                        # skip building build triples for abstracts that are either not maintained (null) or empty strings ("")
                        if not abstract_inverted_index is None and len(abstract_inverted_index) != 0:
                            abstract_inverted_index = inverted_to_plain_text(abstract_inverted_index)
                            # Escape newlines
                            abstract_inverted_index = clean(abstract_inverted_index)
                            works_graph.add(
                                (work_uri, DCTERMS.abstract, Literal(abstract_inverted_index, datatype=XSD.string)))

                    except Exception as e:
                        print(str((e)) + f' error - abstract key not found in file {gz_file_path} in line {i}')
                        pass

                if i % 50000 == 0:
                    print(f'Processed works entity {i} lines in file {gz_file_path}')

                if i % 50000 == 0:
                    # write works_graph to file
                    g.write(works_graph.serialize(format='trig'))
                    works_graph = Graph(identifier=context)

            # Write the last part of current file
            if not i % 50000 == 0:
                # write works_graph to file
                g.write(works_graph.serialize(format='trig'))
                works_graph = Graph(identifier=context)

            f"{trig_output_dir_path}/{gz_file_name}.trig"   

    f.close()
    g.close()

    print(f"Worker completed .trig transformation with {i} lines and {file_error_count} errors")

    # gzip file directly with command
    # -v for live output, --fast for faster compression with about 90% size reduction, -k for keeping the original .trig file
    os.system(f'gzip --fast {trig_output_dir_path}/{gz_file_name}.trig')
    print("Worker completed gzip")


if __name__ == '__main__':
    pool = Pool(CPU_THREADS, maxtasksperchild=5)
    pool.map(transform_gz_file, gz_file_list)
    pool.close()

end_time = time.ctime()

with open(f"{trig_output_dir_path}/{ENTITY_TYPE}-transformation-summary.txt", "w") as z:
    z.write('Start Time: {} .\n'.format(start_time))
    z.write('Files processed: {} .\n'.format(len(gz_file_list)))
    z.write('End Time: {} .\n'.format(end_time))
    z.close()

print("Done")
print("#############################")
