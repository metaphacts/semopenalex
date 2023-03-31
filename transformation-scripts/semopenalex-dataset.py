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

# semopenalex dataset context
context = URIRef("https://semopenalex.org/dataset/context")

# semopenalex dataset subject IRI
dataset = URIRef("http://datasets.metaphacts.com/semopenalex")
 
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

#create empty graph
g = Graph(identifier=context)

g.add((dataset, RDF.type, DCAT.Dataset))
g.add((dataset, DCTERMS.title, Literal("SemOpenAlex", datatype = XSD.string)))
g.add((dataset, DCTERMS.description, Literal("SemOpenAlex is a scientific publications dataset, presently in the form of a knowledge graph. It also offered as the basis for Knowledge Graph augmentation together with some possible use-cases that can enable AI-driven decision making.", datatype = XSD.string)))
g.add((dataset, DCTERMS.issued, Literal(data_issued_time, datatype = XSD.dateTime)))
g.add((dataset, DCAT.keyword, Literal("concepts", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("institutions", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("sources", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("authors", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("publishers", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("works", datatype = XSD.string)))
g.add((dataset, DCAT.keyword, Literal("works", datatype = XSD.string)))
g.add((dataset, namedGraph, concepts_context))
g.add((dataset, namedGraph, institutions_context))
g.add((dataset, namedGraph, sources_context))
g.add((dataset, namedGraph, authors_context))
g.add((dataset, namedGraph, works_context))
g.add((dataset, namedGraph, publishers_context))

with open(trig_output_file_path, "w", encoding="utf-8") as dataset_file:
	dataset_file.write(g.serialize(format='trig'))

dataset_file.close()

print("Done with .trig parsing and graph serialization for SemOpenAlex dataset.")
