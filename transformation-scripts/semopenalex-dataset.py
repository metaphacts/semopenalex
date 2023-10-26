from rdflib import Graph, URIRef, Literal, Dataset
from rdflib.namespace import RDFS, XSD, SKOS, RDF
from rdflib import Namespace
from datetime import datetime
from datetime import date
from pathlib import Path
import time
import os

start_time = time.ctime()
print('Start to create .trig parsing and graph serialization for SemOpenAlex dataset at: '+ start_time)

today = date.today()

absolute_path = os.path.dirname(__file__)
trig_output_dir_path = os.path.join(absolute_path, '../graphdb-preload/graphdb-import/') 
trig_output_file_path = f'{trig_output_dir_path}semopenalex-dataset-{today}.trig'

DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

# semopenalex dataset context
context = URIRef("https://semopenalex.org/dataset/context")

# semopenalex dataset subject IRI
dataset = URIRef("http://datasets.semopenalex.org/dcat/semopenalex")
 
# namedGraph predicate
namedGraph = URIRef("http://www.w3.org/ns/sparql-service-description#namedGraph")

# dataset issued time
data_issued_time = datetime.now()

# list of semopenalex predefined named graphs
concepts_context = URIRef("https://semopenalex.org/concepts/context")
institutions_context = URIRef("https://semopenalex.org/institutions/context")
sources_context = URIRef("https://semopenalex.org/sources/context")
authors_context = URIRef("https://semopenalex.org/authors/context")
works_context = URIRef("https://semopenalex.org/works/context")
publishers_context = URIRef("https://semopenalex.org/publishers/context")
funders_context = URIRef("https://semopenalex.org/funders/context")

#create empty graph
g = Graph(identifier=context)

g.add((dataset, RDF.type, DCAT.Dataset))
g.add((dataset, DCTERMS.title, Literal("SemOpenAlex", datatype = XSD.string)))
g.add((dataset, DCTERMS.description, Literal("SemOpenAlex is a scientific publications dataset, presently in the form of a knowledge graph. It also offered as the basis for Knowledge Graph augmentation together with some possible use-cases that can enable AI-driven decision making.", datatype = XSD.string)))
g.add((dataset, DCTERMS.issued, Literal(data_issued_time, datatype = XSD.dateTime)))
g.add((dataset, DCTERMS.license, Literal("https://creativecommons.org/publicdomain/zero/1.0/legalcode", datatype = XSD.anyURI)))

# keywords 
g.add((dataset, DCAT.version, Literal("3.0.1", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("concepts", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("institutions", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("sources", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("authors", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("publishers", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("works", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("funders", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("geo", datatype = XSD.string)))

# linked named graphs
g.add((dataset, namedGraph, concepts_context))
g.add((dataset, namedGraph, institutions_context))
g.add((dataset, namedGraph, sources_context))
g.add((dataset, namedGraph, authors_context))
g.add((dataset, namedGraph, works_context))
g.add((dataset, namedGraph, publishers_context))
g.add((dataset, namedGraph, funders_context))

# creators
metaphacts = URIRef("http://www.wikidata.org/entity/Q22132500") 
g.add((dataset, DCTERMS.creator, metaphacts))
g.add((metaphacts, RDF.type, FOAF.Organization))
g.add((metaphacts, FOAF.name, Literal("metaphacts GmbH", datatype = XSD.string)))
aifb = URIRef("http://dbpedia.org/resource/Karlsruhe_Institute_of_Technology") 
g.add((dataset, DCTERMS.creator, aifb))
g.add((aifb, RDF.type, FOAF.Organization))
g.add((aifb, FOAF.name, Literal("Institute AIFB, Karlsruhe Institute of Technology (KIT)", datatype = XSD.string)))

# distributions
format = URIRef("http://purl.org/dc/terms/format")
dist_v1 = URIRef("http://datasets.semopenalex.org/v1/semopenalex-distribution")
g.add((dataset, DCAT.distribution, dist_v1))
g.add((dist_v1, RDF.type, DCAT.Distribution))
g.add((dist_v1, DCTERMS.issued, Literal("2022-05-12", datatype = XSD.date)))
g.add((dist_v1, DCTERMS.title, Literal("SemOpenAlex RDF dump", datatype = XSD.string)))
g.add((dist_v1, format, Literal("N-Triples", datatype = XSD.string)))
g.add((dist_v1, DCAT.mediaType, Literal("text/plain", datatype = XSD.string)))
g.add((dist_v1, DCAT.accessURL, Literal("https://semopenalex.s3.amazonaws.com/browse.html", datatype = XSD.anyURI)))

dist_v2 = URIRef("http://datasets.semopenalex.org/v2/semopenalex-distribution")
g.add((dataset, DCAT.distribution, dist_v2))
g.add((dist_v2, RDF.type, DCAT.Distribution))
g.add((dist_v2, DCTERMS.issued, Literal("2022-11-21", datatype = XSD.date)))
g.add((dist_v2, DCTERMS.title, Literal("SemOpenAlex RDF dump", datatype = XSD.string)))
g.add((dist_v2, format, Literal("TriG", datatype = XSD.string)))
g.add((dist_v2, DCAT.mediaType, Literal("application/x-trig", datatype = XSD.string)))
g.add((dist_v2, DCAT.accessURL, Literal("https://semopenalex.s3.amazonaws.com/browse.html", datatype = XSD.anyURI)))

dist_v3 = URIRef("http://datasets.semopenalex.org/v3/semopenalex-distribution")
g.add((dataset, DCAT.distribution, dist_v3))
g.add((dist_v3, RDF.type, DCAT.Distribution))
g.add((dist_v3, DCTERMS.issued, Literal("2023-04-24", datatype = XSD.date)))
g.add((dist_v3, DCTERMS.title, Literal("SemOpenAlex RDF dump", datatype = XSD.string)))
g.add((dist_v3, format, Literal("TriG", datatype = XSD.string)))
g.add((dist_v3, DCAT.mediaType, Literal("application/x-trig", datatype = XSD.string)))
g.add((dist_v3, DCAT.accessURL, Literal("https://semopenalex.s3.amazonaws.com/browse.html", datatype = XSD.anyURI)))

dist_v4 = URIRef("http://datasets.semopenalex.org/v4/semopenalex-distribution")
g.add((dataset, DCAT.distribution, dist_v4))
g.add((dist_v4, RDF.type, DCAT.Distribution))
g.add((dist_v4, DCTERMS.issued, Literal(today, datatype = XSD.date)))
g.add((dist_v4, DCTERMS.title, Literal("SemOpenAlex RDF dump", datatype = XSD.string)))
g.add((dist_v4, format, Literal("TriG", datatype = XSD.string)))
g.add((dist_v4, DCAT.mediaType, Literal("application/x-trig", datatype = XSD.string)))
g.add((dist_v4, DCAT.accessURL, Literal("https://semopenalex.s3.amazonaws.com/browse.html", datatype = XSD.anyURI)))

with open(trig_output_file_path, "w", encoding="utf-8") as dataset_file:
	dataset_file.write(g.serialize(format='trig'))

dataset_file.close()

print("Done with .trig parsing and graph serialization for SemOpenAlex dataset.")
