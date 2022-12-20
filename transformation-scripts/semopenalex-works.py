# Copyright Johan Krause, Michael Färber, Institute AIFB, Karlsruhe Institute of Technology (KIT)
# this script transforms OpenAlex data dump files to triple form in trig files for SemOpenAlex
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD, OWL
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


# info for namespaces used in SOA
soa_namespace_class = "https://semopenalex.org/class/"
soa_namespace_authors = "https://semopenalex.org/author/"
soa_namespace_author_position = "https://semopenalex.org/authorposition/"
soa_namespace_countsbyyear = "https://semopenalex.org/countsbyyear/"
soa_namespace_works = "https://semopenalex.org/work/"
soa_namespace_institutions = "https://semopenalex.org/institution/"
soa_namespace_venues = "https://semopenalex.org/venue/"
soa_namespace_host_venues = "https://semopenalex.org/hostvenue/"
soa_namespace_open_access = "https://semopenalex.org/openaccess/"
soa_namespace_concept = "https://semopenalex.org/concept/"
soa_namespace_concept_score = "https://semopenalex.org/conceptscore/"

# SOA classes used in this file
soa_class_work = URIRef(soa_namespace_class + "Work")
soa_class_host_venue = URIRef(soa_namespace_class + "HostVenue")
soa_class_open_access = URIRef(soa_namespace_class + "OpenAccess")
soa_class_author_position = URIRef(soa_namespace_class + "AuthorPosition")
soa_class_counts_by_year = URIRef(soa_namespace_class + "CountsByYear")
soa_class_concept = URIRef(soa_namespace_class + "Concept")
soa_class_concept_score = URIRef(soa_namespace_class + "ConceptScore")

# SOA predicates
doi_predicate = URIRef("http://purl.org/spar/datacite/doi")
publication_year_predicate = URIRef("http://purl.org/spar/fabio/hasPublicationYear")
mag_id_predicate = URIRef("https://semopenalex.org/property/magId")
pubmed_id_predicate = URIRef("http://purl.org/spar/fabio/hasPubMedId")
pubmed_central_predicate = URIRef("http://purl.org/spar/fabio/hasPubMedCentralId")
host_venue_predicate = URIRef("https://semopenalex.org/property/hasHostVenue")
venue_predicate = URIRef("https://semopenalex.org/property/hasVenue")
alternative_venue_predicate = URIRef("https://semopenalex.org/property/hasAlternativeHostVenue")
url_predicate = URIRef("http://purl.org/spar/fabio/hasURL")
is_oa_predicate = URIRef("https://semopenalex.org/property/isOa")
has_oa_predicate = URIRef("https://semopenalex.org/property/hasOpenAccess")
oa_status_predicate = URIRef("https://semopenalex.org/property/oaStatus")
oa_url_predicate = URIRef("https://semopenalex.org/property/oaUrl")
version_predicate = URIRef("https://semopenalex.org/property/hasVersion")
crossref_type_predicate = URIRef("https://semopenalex.org/property/crossrefType")
has_author_position_predicate = URIRef("https://semopenalex.org/property/hasAuthorPosition")
author_position_predicate = URIRef("https://semopenalex.org/property/position")
has_author_predicate = URIRef("https://semopenalex.org/property/hasAuthor")
cited_by_count_predicate = URIRef("https://semopenalex.org/property/citedByCount")
counts_by_year_predicate = URIRef("https://semopenalex.org/property/countsByYear")
has_volume_predicate = URIRef("https://semopenalex.org/property/hasVolume")
has_issue_predicate = URIRef("https://semopenalex.org/property/hasIssue")
starting_page_predicate = URIRef("http://prismstandard.org/namespaces/basic/2.0/startingPage")
ending_page_predicate = URIRef("http://prismstandard.org/namespaces/basic/2.0/endingPage")
is_retracted_predicate = URIRef("https://semopenalex.org/property/isRetracted")
is_paratext_predicate = URIRef("https://semopenalex.org/property/isParatext")
has_concept_predicate = URIRef("https://semopenalex.org/property/hasConcept")
has_concept_score_predicate = URIRef("https://semopenalex.org/property/hasConceptScore")
score_predicate = URIRef("https://semopenalex.org/property/score")
cites_predicate = URIRef("http://purl.org/spar/cito/cites")
related_work_predicate = URIRef("https://semopenalex.org/property/hasRelatedWork")
year_predicate = URIRef("https://semopenalex.org/property/year")

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
print('works entity files started to download at: '+ data_dump_start_time)
# Copy works entity snapshot
client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
file_names, folders = get_file_folders(client, "openalex", "data/works/")
download_files(
    client,
    "openalex",
   data_dump_input_root_dir,
    file_names,
    folders
)
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
    gz_file_name = gz_file_path[len(gz_file_list[1]) - 39:].replace(".gz", "").replace("/", "_")
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

                        # publication data
                        work_publication_date = json_data['publication_date']
                        if not work_publication_date is None:
                            work_publication_date = clean(work_publication_date)
                            works_graph.add((work_uri, DCTERMS.date,
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

                        # host_venue
                        work_host_venue = json_data['host_venue']
                        if not work_host_venue is None:
                            work_host_venue_id = json_data['host_venue']['id']
                            if not work_host_venue_id is None:
                                work_host_venue_id = work_host_venue_id.replace("https://openalex.org/", "")
                                work_host_venue_uri = URIRef(
                                    soa_namespace_host_venues + str(work_id) + str(work_host_venue_id))
                                works_graph.add((work_host_venue_uri, RDF.type, soa_class_host_venue))
                                works_graph.add((work_uri, host_venue_predicate, work_host_venue_uri))
                                work_venue_uri = URIRef(soa_namespace_venues + str(work_host_venue_id))
                                works_graph.add((work_host_venue_uri, venue_predicate, work_venue_uri))

                                work_host_venue_url = json_data['host_venue']['url']
                                if not work_host_venue_url is None:
                                    work_host_venue_url = clean_url(work_host_venue_url)
                                    works_graph.add((work_host_venue_uri, url_predicate,
                                                     Literal(work_host_venue_url, datatype=XSD.string)))

                                work_host_venue_is_oa = json_data['host_venue']['is_oa']
                                if not work_host_venue_is_oa is None:
                                    works_graph.add((work_host_venue_uri, is_oa_predicate,
                                                     Literal(work_host_venue_is_oa, datatype=XSD.boolean)))

                                work_host_venue_version = json_data['host_venue']['version']
                                if not work_host_venue_version is None:
                                    work_host_venue_version = clean(work_host_venue_version)
                                    works_graph.add((work_host_venue_uri, version_predicate,
                                                     Literal(work_host_venue_version, datatype=XSD.string)))

                                work_host_venue_license = json_data['host_venue']['license']
                                if not work_host_venue_license is None:
                                    work_host_venue_license = clean(work_host_venue_license)
                                    works_graph.add((work_host_venue_uri, DCTERMS.license,
                                                     Literal(work_host_venue_license, datatype=XSD.string)))

                        # type
                        work_type = json_data['type']
                        if not work_type is None:
                            work_type = str("https://api.crossref.org/types/" + str(work_type))
                            works_graph.add(
                                (work_uri, crossref_type_predicate, Literal(work_type, datatype=XSD.string)))

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

                        # authorship
                        work_authorships = json_data['authorships']
                        if not work_authorships is None:
                            for authorship in work_authorships:
                                authorship_id = authorship["author"]["id"].replace("https://openalex.org/", "")
                                authorship_uri = URIRef(soa_namespace_authors + str(authorship_id))
                                works_graph.add((work_uri, DCTERMS.creator, authorship_uri))

                        # author position
                        work_authorships = json_data['authorships']
                        if not work_authorships is None:
                            for authorship in work_authorships:
                                author_position = authorship["author_position"]
                                authorship_id = authorship["author"]["id"].replace("https://openalex.org/", "")
                                work_author_position_uri = URIRef(
                                    soa_namespace_author_position + str(work_id) + str(authorship_id))
                                works_graph.add((work_author_position_uri, RDF.type, soa_class_author_position))
                                works_graph.add((work_uri, has_author_position_predicate, work_author_position_uri))
                                works_graph.add((work_author_position_uri, author_position_predicate,
                                                 Literal(author_position, datatype=XSD.string)))
                                work_author_uri = URIRef(soa_namespace_authors + str(authorship_id))
                                works_graph.add((work_author_position_uri, has_author_predicate, work_author_uri))

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
                                concept_score_uri = URIRef(soa_namespace_concept_score + str(work_id) + str(concept_id))
                                # direkte Verbindung ohne score value
                                works_graph.add((work_uri, has_concept_predicate, concept_uri))
                                works_graph.add((concept_score_uri, RDF.type, soa_class_concept_score))
                                works_graph.add((work_uri, has_concept_score_predicate, concept_score_uri))
                                works_graph.add((concept_score_uri, has_concept_predicate, concept_uri))
                                works_graph.add(
                                    (concept_score_uri, score_predicate, Literal(concept_score, datatype=XSD.integer)))

                        # mesh
                        # to do

                        # alternate_host_venues
                        work_alternate_host_venues = json_data['alternate_host_venues']
                        if not work_alternate_host_venues is None:
                            for alt_venue in work_alternate_host_venues:
                                if not alt_venue["id"] is None:
                                    work_alt_venue_id = alt_venue["id"].replace("https://openalex.org/", "")
                                    work_alt_host_venue_uri = URIRef(
                                        soa_namespace_host_venues + str(work_id) + str(work_alt_venue_id))
                                    works_graph.add((work_alt_host_venue_uri, RDF.type, soa_class_host_venue))
                                    works_graph.add((work_uri, alternative_venue_predicate, work_alt_host_venue_uri))
                                    work_alt_venue_uri = URIRef(soa_namespace_venues + str(work_alt_venue_id))
                                    works_graph.add((work_alt_host_venue_uri, venue_predicate, work_alt_venue_uri))

                                    if not alt_venue["url"] is None:
                                        alt_venue_url = alt_venue["url"]
                                        alt_venue_url = clean_url(alt_venue_url)
                                        works_graph.add((work_alt_host_venue_uri, url_predicate,
                                                         Literal(alt_venue_url, datatype=XSD.string)))

                                    if not alt_venue["is_oa"] is None:
                                        alt_venue_is_oa = alt_venue["is_oa"]
                                        works_graph.add((work_alt_host_venue_uri, is_oa_predicate,
                                                         Literal(alt_venue_is_oa, datatype=XSD.boolean)))

                                    if not alt_venue["version"] is None:
                                        alt_venue_version = alt_venue["version"]
                                        alt_venue_version = clean(alt_venue_version)
                                        works_graph.add((work_alt_host_venue_uri, version_predicate,
                                                         Literal(alt_venue_version, datatype=XSD.string)))

                                    if not alt_venue["license"] is None:
                                        alt_venue_license = alt_venue["license"]
                                        alt_venue_license = clean(alt_venue_license)
                                        works_graph.add((work_alt_host_venue_uri, DCTERMS.license,
                                                         Literal(alt_venue_license, datatype=XSD.string)))

                        # referenced_works
                        work_referenced_works = json_data['referenced_works']
                        for ref_work in work_referenced_works:
                            if not ref_work is None:
                                ref_work = ref_work.replace("https://openalex.org/", "")
                                referenced_work_uri = URIRef(soa_namespace_works + str(ref_work))
                                works_graph.add((work_uri, cites_predicate, referenced_work_uri))

                        # related_works
                        work_related_works = json_data['related_works']
                        for rel_work in work_related_works:
                            if not rel_work is None:
                                rel_work = rel_work.replace("https://openalex.org/", "")
                                related_work_uri = URIRef(soa_namespace_works + str(rel_work))
                                works_graph.add((work_uri, related_work_predicate, related_work_uri))

                        # cited_by_api_url
                        # is missing atm

                        # counts_by_year
                        work_counts_by_year = json_data['counts_by_year']
                        if not work_counts_by_year is None:
                            for count_year in work_counts_by_year:
                                count_year_year = count_year["year"]
                                count_year_uri = URIRef(soa_namespace_countsbyyear + work_id + str(count_year_year))

                                works_graph.add((count_year_uri, RDF.type, soa_class_counts_by_year))
                                works_graph.add((work_uri, counts_by_year_predicate, count_year_uri))
                                works_graph.add(
                                    (count_year_uri, year_predicate, Literal(count_year_year, datatype=XSD.integer)))
                                count_year_cited_by_count = count_year["cited_by_count"]
                                works_graph.add((count_year_uri, cited_by_count_predicate,
                                                 Literal(count_year_cited_by_count, datatype=XSD.integer)))

                        work_updated_date = json_data['updated_date']
                        if not work_updated_date is None:
                            works_graph.add((work_uri, DCTERMS.modified, Literal(work_updated_date, datatype=XSD.date)))

                        # created_date
                        work_created_date = json_data['created_date']
                        if not work_created_date is None:
                            works_graph.add((work_uri, DCTERMS.created, Literal(work_created_date, datatype=XSD.date)))

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
                    g.write(works_graph.serialize(format='trig'))
                    works_graph = Graph(identifier=context)

            # Write the last part of current file
            if not i % 50000 == 0:
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
