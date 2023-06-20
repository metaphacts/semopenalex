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
|ids_mag                    |  `<https://semopenalex.org/property/magId>`                            |
|ids_pmid                    |  `<http://purl.org/spar/fabio/hasPubMedId>`                            |
|ids_pmcid                    | `<http://purl.org/spar/fabio/hasPubMedCentralId>`                             |
|locations                    | `<https://semopenalex.org/property/hasLocation>`                             |
|locations_landing_page_url                   |   `<http://purl.org/spar/fabio/hasURL>`                           |
|locations_pdf_url                    |    `<https://semopenalex.org/property/pdfUrl>`                          |
|locations_is_oa                    | `<https://semopenalex.org/property/isOa>`                             |
|locations_version                  |  `<https://semopenalex.org/property/hasVersion>`                            |
|locations_license                  |  `<http://purl.org/dc/terms/license>`                            |
|primary_location                    |  `<https://semopenalex.org/property/hasPrimaryLocation>`                            |
|best_oa_location                    | `<https://semopenalex.org/property/hasBestOaLocation>`                             |
|locations_source                    |  `<https://semopenalex.org/property/hasSource>`                            |
|primary_location_source                    |   `<https://semopenalex.org/property/hasSource>`                              |
|best_oa_location_source                    |   `<https://semopenalex.org/property/hasSource>`                           |
|type                    |  `<https://semopenalex.org/property/crossrefType>`                            |
|open_access                    |  `<https://semopenalex.org/property/hasOpenAccess>`                            |
|open_access_is_oa                    |`<https://semopenalex.org/property/isOa>`                              |
|open_access_oa_status                    |   `<https://semopenalex.org/property/oaStatus>`                           |
| open_access_oa_url                   |  `<https://semopenalex.org/property/oaUrl>`                            |
|authorships_author_position | `<https://semopenalex.org/property/hasAuthorPosition>`, `<https://semopenalex.org/property/position>`  |
|authorships_author_id                    |   `<https://semopenalex.org/property/hasAuthor>`                               |
|cited_by_count                    |   `<https://semopenalex.org/property/citedByCount>`                           |
|biblio_volume                    |  `<https://semopenalex.org/property/hasVolume>`                            |
|biblio_issue                    |  `<https://semopenalex.org/property/hasIssue>`                            |
|biblio_first_page                    |  `<http://prismstandard.org/namespaces/basic/2.0/startingPage>`                            |
|biblio_last_page                    |  `<http://prismstandard.org/namespaces/basic/2.0/endingPage>`                            |
|is_retracted                    |   `<https://semopenalex.org/property/isRetracted>`                           |
|is_paratext                    |   `<https://semopenalex.org/property/isParatext>`                           |
|concepts                    |   `<https://semopenalex.org/property/hasConcept>`                           |
| concepts_score                   |`<https://semopenalex.org/property/hasConceptScore>`, `<https://semopenalex.org/property/score>` |        
|referenced_works                    | `<http://purl.org/spar/cito/cites>`                             |
|related_works                    |   `<https://semopenalex.org/property/hasRelatedWork>`                           |
|counts_by_year                   |`<https://semopenalex.org/property/countsByYear>`| 
|counts_by_year (year)                   |   `<https://semopenalex.org/property/year>`                |
|counts_by_year (cited_by_count)                   |   `<https://semopenalex.org/property/citedByCount>`                |
| updated_date                  |    `<http://purl.org/dc/terms/modified>`               |
|  created_date                 |   `<http://purl.org/dc/terms/created>`                |
| abstract_inverted_index                   |   `<http://purl.org/dc/terms/abstract>`                           |

## Mapping of the Author Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|-------------------|-----------------------------------|
| id   | `<https://semopenalex.org/author/> + id.replace("https://openalex.org/", "")>` |
| orcid | `<https://dbpedia.org/ontology/orcidId>` |
| display_name | `<http://xmlns.com/foaf/0.1/name>` |
| display_name_alternatives | `<https://semopenalex.org/property/alternativeName>` |
| works_count | `<https://semopenalex.org/property/worksCount>` |
| cited_by_count | `<https://semopenalex.org/property/citedByCount>` |
| ids (mag) | `<https://semopenalex.org/property/magId>` |
| ids (twitter) | `<https://dbpedia.org/property/twitter>` |
| ids (wikipedia) | `<http://www.w3.org/2000/01/rdf-schema#seeAlso>` |
| ids (scopus) | `<https://dbpedia.org/property/scopus>` |
| last_known_institution | `<http://www.w3.org/ns/org#memberOf>` |
| counts_by_year | `<https://semopenalex.org/property/countsByYear>` |
| counts_by_year (year) | `<https://semopenalex.org/property/year  >` |
| counts_by_year (works_count) | `<https://semopenalex.org/property/worksCount>` |
| counts_by_year (cited_by_count) | `<https://semopenalex.org/property/citedByCount>` |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |


## Mapping of the Institution Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|-------------------|--------------------------|
| institution | `<https://semopenalex.org/institution/ + id.replace("https://openalex.org/", "")>` |
|ror                |`<https://semopenalex.org/property/ror>`|
|display_name                   |`<http://xmlns.com/foaf/0.1/name>`                          |
|country_code                   |`<https://dbpedia.org/property/countryCode>`                          |
|type                   |`<https://semopenalex.org/property/rorType>`                          |
|homepage_url                   |`<http://xmlns.com/foaf/0.1/homepage>`                          |
|image_url                   |`<http://xmlns.com/foaf/0.1/depiction>`                          |
|image_thumbnail_url                   |`<https://semopenalex.org/property/imageThumbnail>`                          |
|display_name_acronyms                   |`<https://dbpedia.org/property/acronym>`                          |
|display_name_alternatives                   |`<https://dbpedia.org/ontology/alternativeName>`                          |
|works_count                   |`<https://semopenalex.org/property/worksCount>`                          |
|cited_by_count                   |`<https://semopenalex.org/property/citedByCount>`| 
|ids_mag                   |`<https://semopenalex.org/property/magId>`| 
|ids_grid                   |`<https://semopenalex.org/property/grid>`| 
|ids_wikipedia  | `<http://www.w3.org/2000/01/rdf-schema#seeAlso>` | 
|ids_wikidata  | `<http://www.w3.org/2002/07/owl#sameAs>`  | 
|geo_city  | `<https://dbpedia.org/property/city>`  |
|geo_geonames_city_id  |`<http://www.geonames.org/ontology#geonamesID>`  |
|geo_region  |  `<https://dbpedia.org/property/region>`|
|geo_country_code  | `<http://www.geonames.org/ontology#countryCode>` |
|geo_country  |  `<https://dbpedia.org/property/country>`|
|geo_latitude  | `<http://www.geonames.org/ontology#lat>` |
|geo_longitude  |  `<http://www.geonames.org/ontology#long>`|
|associated_institutions                   |  `<https://semopenalex.org/property/hasAssociatedInstitution>`                 |
|counts_by_year                   |`<https://semopenalex.org/property/countsByYear>`| 
|counts_by_year_year                   |   `<https://semopenalex.org/property/year>`                |
|counts_by_year_works_count                  |    `<https://semopenalex.org/property/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/property/citedByCount>`                |
| updated_date                  |    `<http://purl.org/dc/terms/modified>`               |
|  created_date                 |   `<http://purl.org/dc/terms/created>`                |



## Mapping of the Source Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|---------------|-----------|
| id | `<https://semopenalex.org/source/> + id.replace("https://openalex.org/", "")>` |
| display_name | `<http://xmlns.com/foaf/0.1/name>` |
| host_organization | `<https://semopenalex.org/property/hasHostOrganization>` |
| type | `<https://semopenalex.org/property/sourceType>` |
| apc_usd | `<https://semopenalex.org/property/apcUsd>` |
| country_code | `<http://www.geonames.org/ontology#countryCode>` |
| fatcat_id | `<https://semopenalex.org/property/fatcatId>` |
| abbreviated_title | `<https://semopenalex.org/property/abbreviatedName>` |
| alternate_titles | `<https://dbpedia.org/ontology/alternativeName>` |
| wikidata | `<http://www.w3.org/2002/07/owl#sameAs>` |
| issn_l | `<http://purl.org/spar/fabio/hasIssnL>` |
| issn | `<http://prismstandard.org/namespaces/basic/2.0/issn>` |
| summary_stats (2yr_mean_citedness) | `<https://semopenalex.org/property/2YrMeanCitedness>` |
| summary_stats (h_index) | `<http://purl.org/spar/bido/h-index>` |
| summary_stats (i10_index) | `<https://semopenalex.org/property/i10Index>` |
| works_count | `<https://semopenalex.org/property/worksCount>` |
| cited_by_count | `<https://semopenalex.org/property/citedByCount>` |
| is_oa | `<https://semopenalex.org/property/isOa>` |
| is_in_doaj | `<https://semopenalex.org/property/isInDoaj>` |
| homepage_url | `<http://xmlns.com/foaf/0.1/homepage>` |
| ids (mag) | `<https://semopenalex.org/property/magId>` |
|counts_by_year                   | `<https://semopenalex.org/property/countsByYear>` | 
|counts_by_year_year                   |   `<https://semopenalex.org/property/year>`               |
|counts_by_year_works_count                  |    `<https://semopenalex.org/property/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/property/citedByCount>`                |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |


## Mapping of the Publisher Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|---------------|-----------|
| id | `<https://semopenalex.org/publisher/ + id.replace("https://openalex.org/", "")>` |
| display_name | `<http://xmlns.com/foaf/0.1/name>` |
| alternate_titles | `<https://dbpedia.org/ontology/alternativeName>` |
| hierarchy_level | `<https://semopenalex.org/property/level>` |
| parent_publisher | `<https://semopenalex.org/property/hasParentPublisher>` |
| country_codes | `<http://www.geonames.org/ontology#countryCode>` |
| ror | `<https://semopenalex.org/property/ror>` |
| wikidata | `<http://www.w3.org/2002/07/owl#sameAs>` |
|summary_stats (2yr_mean_citedness) | `<https://semopenalex.org/property/2YrMeanCitedness>` |
|summary_stats (h_index) | `<http://purl.org/spar/bido/h-index>` |
| summary_stats (i10_index) | `<https://semopenalex.org/property/i10Index>` |
| works_count | `<https://semopenalex.org/property/worksCount>` |
| cited_by_count | `<https://semopenalex.org/property/citedByCount>` |
|counts_by_year                   | `<https://semopenalex.org/property/countsByYear>` | 
|counts_by_year_year                   |   `<https://semopenalex.org/property/year>`               |
|counts_by_year_works_count                  |    `<https://semopenalex.org/property/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/property/citedByCount>`                |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |


## Mapping of the Concept Entities

| OpenAlex Attribut | SemOpenAlex Ontology (RDF Property) |
|---------------|-----------|
| id | `<https://semopenalex.org/concept/ + id.replace("https://openalex.org/", "")>` |
| wikidata | `<http://www.w3.org/2002/07/owl#sameAs>` |
| display_name | `<http://www.w3.org/2004/02/skos/core#prefLabel>` |
| level | `<https://semopenalex.org/property/level>` |
| description | `<http://www.w3.org/2004/02/skos/core#note>` |
| works_count | `<https://semopenalex.org/property/worksCount>` |
| cited_by_count | `<https://semopenalex.org/property/citedByCount>` |
| ids (mag) | `<https://semopenalex.org/property/magId>` |
| ids (wikipedia) | `<http://www.w3.org/2000/01/rdf-schema#seeAlso>` |
| ids (umls_aui) | `<https://semopenalex.org/property/umlsAui>` |
| ids (umls_cui) | `<https://semopenalex.org/property/umlsCui>` |
| image_url | `<http://xmlns.com/foaf/0.1/depiction>` |
| image_thumbnail_url | `<https://semopenalex.org/property/imageThumbnail>` |
| ancestors | `<http://www.w3.org/2004/02/skos/core#broader>` |
| related_concepts | `<http://www.w3.org/2004/02/skos/core#related>` |
|counts_by_year                   | `<https://semopenalex.org/property/countsByYear>` | 
|counts_by_year_year                   |   `<https://semopenalex.org/property/year>`               |
|counts_by_year_works_count                  |    `<https://semopenalex.org/property/worksCount>`               |
|counts_by_year_cited_by_count                   |   `<https://semopenalex.org/property/citedByCount>`                |
| updated_date | `<http://purl.org/dc/terms/modified>` |
| created_date | `<http://purl.org/dc/terms/created>` |


