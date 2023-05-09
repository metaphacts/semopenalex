'''
Send several SPARQL Queries to the SemOpenAlex SPARQL endpoint to get the number of publications 
published in machine learning (<https://semopenalex.org/concept/C119857082>) by researchers from 
Karlsruhe Institute of Technology (<https://semopenalex.org/institution/I102335020>) from 2000 to 2021
'''

import requests

query_template = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX org: <http://www.w3.org/ns/org#>
PREFIX fabio: <http://purl.org/spar/fabio/>
PREFIX soa: <https://semopenalex.org/property/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT (COUNT (?paper) as ?paperCount)
WHERE { 
 ?paper a <https://semopenalex.org/class/Work> .
 ?paper dcterms:creator ?author .
 ?author org:memberOf <https://semopenalex.org/institution/I102335020> .
 ?paper fabio:hasPublicationYear "%d"^^xsd:integer .
 ?paper soa:hasConcept <https://semopenalex.org/concept/C119857082> . 
}
"""

#SemOpenAlex SPARQL Endpoint
endpoint_url = "https://semopenalex.org/sparql"

#Loop through the years 2000 to 2021
for year in range(2000, 2022):

    #Put the current year in the SPARQL query
    query = query_template % year

    response = requests.post(endpoint_url, data={"query": query})

    #Display the result on the terminal
    print("Jahr %d: %s" % (year, response.text))
    