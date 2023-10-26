# Mapping of the OpenAlex Attributes into the SemOpenAlex Ontology

The tables below contain the mapping that is executed in the transformation scripts to create SemOpenAlex.

## Mapping of the Work Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|-------------------|--------------------------|
| id | `<https://semopenalex.org/work/ + id.replace("https://openalex.org/", "")>` |
|doi                    |    `<http://purl.org/spar/datacite/doi>`                          |
|title                    |  `<http://purl.org/dc/terms/title>`                            |
|publication_year                    | `<http://purl.org/spar/fabio/hasPublicationYear>`                             |
|publication_date                    |   `<http://purl.org/dc/terms/date>`                           |
|ids_mag                    |  `<https://semopenalex.org/ontology/magId>`                            |
|ids_pmid                    |  `<http://purl.org/spar/fabio/hasPubMedId>`                            |
|ids_pmcid                    | `<http://purl.org/spar/fabio/hasPubMedCentralId>`                             |
|locations                    | `<https://semopenalex.org/ontology/hasLocation>`                             |
|locations_landing_page_url                   |   `<http://purl.org/spar/fabio/hasURL>`                           |
|locations_pdf_url                    |    `<https://semopenalex.org/ontology/pdfUrl>`                          |
|locations_is_oa                    | `<https://semopenalex.org/ontology/isOa>`                             |
|locations_version                  |  `<https://semopenalex.org/ontology/hasVersion>`                            |
|locations_license                  |  `<http://purl.org/dc/terms/license>`                            |
|primary_location                    |  `<https://semopenalex.org/ontology/hasPrimaryLocation>`                            |
|best_oa_location                    | `<https://semopenalex.org/ontology/hasBestOaLocation>`                             |
|locations_source                    |  `<https://semopenalex.org/ontology/hasSource>`                            |
|primary_location_source                    |   `<https://semopenalex.org/ontology/hasSource>`                              |
|best_oa_location_source                    |   `<https://semopenalex.org/ontology/hasSource>`                           |
|type                    |  `<https://semopenalex.org/ontology/workType>`                            |
|type_crossref                    |  `<https://semopenalex.org/ontology/crossrefType>`                            |
|open_access                    |  `<https://semopenalex.org/ontology/hasOpenAccess>`                            |
|open_access_is_oa                    |`<https://semopenalex.org/ontology/isOa>`                              |
|open_access_oa_status                    |   `<https://semopenalex.org/ontology/oaStatus>`                           |
| open_access_oa_url                   |  `<https://semopenalex.org/ontology/oaUrl>`                            |
|authorships_author_position | `<https://semopenalex.org/ontology/hasAuthorship>`, `<https://semopenalex.org/ontology/position>`  |
|authorships_raw_affiliation_string | `<https://semopenalex.org/ontology/hasAuthorship>`, `<https://semopenalex.org/ontology/rawAffiliation>`  |
|authorships_is_corresponding | `<https://semopenalex.org/ontology/hasAuthorship>`, `<https://semopenalex.org/ontology/isCorresponding>`  |
|authorships_institutions_id | `<https://semopenalex.org/ontology/hasOrganization>`  |
|authorships_author_id                    |   `<https://semopenalex.org/ontology/hasAuthor>`                               |
|cited_by_count                    |   `<https://semopenalex.org/ontology/citedByCount>`                           |
|biblio_volume                    |  `<https://semopenalex.org/ontology/hasVolume>`                            |
|biblio_issue                    |  `<https://semopenalex.org/ontology/hasIssue>`                            |
|biblio_first_page                    |  `<http://prismstandard.org/namespaces/basic/2.0/startingPage>`                            |
|biblio_last_page                    |  `<http://prismstandard.org/namespaces/basic/2.0/endingPage>`                            |
|is_retracted                    |   `<https://semopenalex.org/ontology/isRetracted>`                           |
|is_paratext                    |   `<https://semopenalex.org/ontology/isParatext>`                           |
|concepts                    |   `<https://semopenalex.org/ontology/hasConcept>`                           |
| concepts_score                   |`<https://semopenalex.org/ontology/hasConceptScore>`, `<https://semopenalex.org/ontology/score>` |        
|referenced_works                    | `<http://purl.org/spar/cito/cites>`                             |
|related_works                    |   `<https://semopenalex.org/ontology/hasRelatedWork>`                           |
|counts_by_year                   |`<https://semopenalex.org/ontology/countsByYear>`| 
|counts_by_year (year)                   |   `<https://semopenalex.org/ontology/year>`                |
|counts_by_year (cited_by_count)                   |   `<https://semopenalex.org/ontology/citedByCount>`                |
| updated_date                  |    `<http://purl.org/dc/terms/modified>`               |
|  created_date                 |   `<http://purl.org/dc/terms/created>`                |
| abstract_inverted_index                   |   `<http://purl.org/dc/terms/abstract>`                           |

## Mapping of the Author Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|-------------------|-----------------------------------|
| id   | `<https://semopenalex.org/author/> + id.replace("https://openalex.org/", "")>` |
| orcid | `<https://dbpedia.org/ontology/orcidId>` |
| display_name | `<http://xmlns.com/foaf/0.1/name>` |
| display_name_alternatives | `<https://semopenalex.org/ontology/alternativeName>` |
| works_count | `<https://semopenalex.org/ontology/worksCount>` |
| cited_by_count | `<https://semopenalex.org/ontology/citedByCount>` |
| ids (mag) | `<https://semopenalex.org/ontology/magId>` |
| ids (twitter) | `<https://dbpedia.org/property/twitter>` |
| ids (wikipedia) | `<http://www.w3.org/2000/01/rdf-schema#seeAlso>` |
| ids (scopus) | `<https://dbpedia.org/property/scopus>` |
| last_known_institution | `<http://www.w3.org/ns/org#memberOf>` |
| counts_by_year | `<https://semopenalex.org/ontology/countsByYear>` |
| counts_by_year (year) | `<https://semopenalex.org/ontology/year  >` |
| counts_by_year (works_count) | `<https://semopenalex.org/ontology/worksCount>` |
| counts_by_year (cited_by_count) | `<https://semopenalex.org/ontology/citedByCount>` |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |
| summary_stats (2yr_mean_citedness) | `<https://semopenalex.org/ontology/2YrMeanCitedness>` |
| summary_stats (h_index) | `<http://purl.org/spar/bido/h-index>` |
| summary_stats (i10_index) | `<https://semopenalex.org/ontology/i10Index>` |

## Mapping of the Funder Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|-------------------|--------------------------|
| funder | `<https://semopenalex.org/funder/ + id.replace("https://openalex.org/", "")>` |
| display_name                   |`<http://xmlns.com/foaf/0.1/name>`                          |
| alternate_titles                   | `<https://semopenalex.org/ontology/alternativeName>`                          |
| country_code                   |`<https://dbpedia.org/property/countryCode>`                          |
| description                   |`<http://purl.org/dc/terms/description>`                          |
| homepage_url                   |`<http://xmlns.com/foaf/0.1/homepage>`                          |
| image_url                   |`<http://xmlns.com/foaf/0.1/depiction>`                          |
| image_thumbnail_url                   |`<https://semopenalex.org/ontology/imageThumbnail>`                          |
| grants_count                   |`<https://semopenalex.org/ontology/grantsCount>`                          |
| works_count                   |`<https://semopenalex.org/ontology/worksCount>`                          |
| cited_by_count                   |`<https://semopenalex.org/ontology/citedByCount>`| 
| summary_stats (2yr_mean_citedness) | `<https://semopenalex.org/ontology/2YrMeanCitedness>` |
| summary_stats (h_index) | `<http://purl.org/spar/bido/h-index>` |
| summary_stats (i10_index) | `<https://semopenalex.org/ontology/i10Index>` |
| ids (ror)                |`<https://semopenalex.org/ontology/ror>`|
| ids (wikidata)  | `<http://www.w3.org/2002/07/owl#sameAs>`  | 
| ids (crossref)  | `<https://semopenalex.org/ontology/crossref>`  | 
| ids (doi)  | `<http://prismstandard.org/namespaces/basic/2.0/doi>`  | 
| counts_by_year                   |`<https://semopenalex.org/ontology/countsByYear>`| 
| counts_by_year (year)                   |   `<https://semopenalex.org/ontology/year>`                |
| counts_by_year (works_count)                  |    `<https://semopenalex.org/ontology/worksCount>`               |
| counts_by_year (cited_by_count)                   |   `<https://semopenalex.org/ontology/citedByCount>`                |
| updated_date                  |    `<http://purl.org/dc/terms/modified>`               |
| created_date                 |   `<http://purl.org/dc/terms/created>`                |


## Mapping of the Institution Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|-------------------|--------------------------|
| institution | `<https://semopenalex.org/institution/ + id.replace("https://openalex.org/", "")>` |
|ror                |`<https://semopenalex.org/ontology/ror>`|
|display_name                   |`<http://xmlns.com/foaf/0.1/name>`                          |
|country_code                   |`<https://dbpedia.org/property/countryCode>`                          |
|type                   |`<https://semopenalex.org/ontology/rorType>`                          |
|homepage_url                   |`<http://xmlns.com/foaf/0.1/homepage>`                          |
|image_url                   |`<http://xmlns.com/foaf/0.1/depiction>`                          |
|image_thumbnail_url                   |`<https://semopenalex.org/ontology/imageThumbnail>`                          |
|display_name_acronyms                   |`<https://dbpedia.org/property/acronym>`                          |
|display_name_alternatives                   |`<https://dbpedia.org/ontology/alternativeName>`                          |
|works_count                   |`<https://semopenalex.org/ontology/worksCount>`                          |
|cited_by_count                   |`<https://semopenalex.org/ontology/citedByCount>`| 
|ids_mag                   |`<https://semopenalex.org/ontology/magId>`| 
|ids_grid                   |`<https://semopenalex.org/ontology/grid>`| 
|ids_wikipedia  | `<http://www.w3.org/2000/01/rdf-schema#seeAlso>` | 
|ids_wikidata  | `<http://www.w3.org/2002/07/owl#sameAs>`  | 
|geo_city  | `<https://dbpedia.org/property/city>`  |
|geo_geonames_city_id  |`<http://www.geonames.org/ontology#geonamesID>`  |
|geo_region  |  `<https://dbpedia.org/property/region>`|
|geo_country_code  | `<http://www.geonames.org/ontology#countryCode>` |
|geo_country  |  `<https://dbpedia.org/property/country>`|
|geo_latitude  | `<http://www.geonames.org/ontology#lat>` |
|geo_longitude  |  `<http://www.geonames.org/ontology#long>`|
|associated_institutions                   |  `<https://semopenalex.org/ontology/hasAssociatedInstitution>`                 |
|counts_by_year                   |`<https://semopenalex.org/ontology/countsByYear>`| 
|counts_by_year_year                   |   `<https://semopenalex.org/ontology/year>`                |
|counts_by_year_works_count                  |    `<https://semopenalex.org/ontology/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/ontology/citedByCount>`                |
| updated_date                  |    `<http://purl.org/dc/terms/modified>`               |
|  created_date                 |   `<http://purl.org/dc/terms/created>`                |



## Mapping of the Source Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|---------------|-----------|
| id | `<https://semopenalex.org/source/> + id.replace("https://openalex.org/", "")>` |
| display_name | `<http://xmlns.com/foaf/0.1/name>` |
| host_organization | `<https://semopenalex.org/ontology/hasHostOrganization>` |
| type | `<https://semopenalex.org/ontology/sourceType>` |
| apc_usd | `<https://semopenalex.org/ontology/apcUsd>` |
| country_code | `<http://www.geonames.org/ontology#countryCode>` |
| fatcat_id | `<https://semopenalex.org/ontology/fatcatId>` |
| abbreviated_title | `<https://semopenalex.org/ontology/abbreviatedName>` |
| alternate_titles | `<https://dbpedia.org/ontology/alternativeName>` |
| wikidata | `<http://www.w3.org/2002/07/owl#sameAs>` |
| issn_l | `<http://purl.org/spar/fabio/hasIssnL>` |
| issn | `<http://prismstandard.org/namespaces/basic/2.0/issn>` |
| summary_stats (2yr_mean_citedness) | `<https://semopenalex.org/ontology/2YrMeanCitedness>` |
| summary_stats (h_index) | `<http://purl.org/spar/bido/h-index>` |
| summary_stats (i10_index) | `<https://semopenalex.org/ontology/i10Index>` |
| works_count | `<https://semopenalex.org/ontology/worksCount>` |
| cited_by_count | `<https://semopenalex.org/ontology/citedByCount>` |
| is_oa | `<https://semopenalex.org/ontology/isOa>` |
| is_in_doaj | `<https://semopenalex.org/ontology/isInDoaj>` |
| homepage_url | `<http://xmlns.com/foaf/0.1/homepage>` |
| ids (mag) | `<https://semopenalex.org/ontology/magId>` |
|counts_by_year                   | `<https://semopenalex.org/ontology/countsByYear>` | 
|counts_by_year_year                   |   `<https://semopenalex.org/ontology/year>`               |
|counts_by_year_works_count                  |    `<https://semopenalex.org/ontology/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/ontology/citedByCount>`                |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |


## Mapping of the Publisher Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|---------------|-----------|
| id | `<https://semopenalex.org/publisher/ + id.replace("https://openalex.org/", "")>` |
| display_name | `<http://xmlns.com/foaf/0.1/name>` |
| alternate_titles | `<https://dbpedia.org/ontology/alternativeName>` |
| hierarchy_level | `<https://semopenalex.org/ontology/level>` |
| parent_publisher | `<https://semopenalex.org/ontology/hasParentPublisher>` |
| country_codes | `<http://www.geonames.org/ontology#countryCode>` |
| ror | `<https://semopenalex.org/ontology/ror>` |
| wikidata | `<http://www.w3.org/2002/07/owl#sameAs>` |
|summary_stats (2yr_mean_citedness) | `<https://semopenalex.org/ontology/2YrMeanCitedness>` |
|summary_stats (h_index) | `<http://purl.org/spar/bido/h-index>` |
| summary_stats (i10_index) | `<https://semopenalex.org/ontology/i10Index>` |
| works_count | `<https://semopenalex.org/ontology/worksCount>` |
| cited_by_count | `<https://semopenalex.org/ontology/citedByCount>` |
|counts_by_year                   | `<https://semopenalex.org/ontology/countsByYear>` | 
|counts_by_year_year                   |   `<https://semopenalex.org/ontology/year>`               |
|counts_by_year_works_count                  |    `<https://semopenalex.org/ontology/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/ontology/citedByCount>`                |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |


## Mapping of the Concept Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|---------------|-----------|
| id | `<https://semopenalex.org/concept/ + id.replace("https://openalex.org/", "")>` |
| wikidata | `<http://www.w3.org/2002/07/owl#sameAs>` |
| display_name | `<http://www.w3.org/2004/02/skos/core#prefLabel>` |
| level | `<https://semopenalex.org/ontology/level>` |
| description | `<http://www.w3.org/2004/02/skos/core#note>` |
| works_count | `<https://semopenalex.org/ontology/worksCount>` |
| cited_by_count | `<https://semopenalex.org/ontology/citedByCount>` |
| ids (mag) | `<https://semopenalex.org/ontology/magId>` |
| ids (wikipedia) | `<http://www.w3.org/2000/01/rdf-schema#seeAlso>` |
| ids (umls_aui) | `<https://semopenalex.org/ontology/umlsAui>` |
| ids (umls_cui) | `<https://semopenalex.org/ontology/umlsCui>` |
| image_url | `<http://xmlns.com/foaf/0.1/depiction>` |
| image_thumbnail_url | `<https://semopenalex.org/ontology/imageThumbnail>` |
| ancestors | `<http://www.w3.org/2004/02/skos/core#broader>` |
| related_concepts | `<http://www.w3.org/2004/02/skos/core#related>` |
|counts_by_year                   | `<https://semopenalex.org/ontology/countsByYear>` | 
|counts_by_year_year                   |   `<https://semopenalex.org/ontology/year>`               |
|counts_by_year_works_count                  |    `<https://semopenalex.org/ontology/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/ontology/citedByCount>`                |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |


