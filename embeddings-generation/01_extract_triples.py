# this files takes raw semantic triple files and extracts specific triples based on the relations

import sys

pred_list = [
    "<https://semopenalex.org/property/crossrefType>",
    "<http://purl.org/spar/cito/cites>",
    "<https://semopenalex.org/property/hasHostVenue>",
    "<http://purl.org/spar/fabio/hasPublicationYear>",
    "<https://semopenalex.org/property/hasConcept>",
    "<https://semopenalex.org/property/hasAuthor>",
    "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>",
    "<http://www.w3.org/ns/org#memberOf>",
    "<http://www.geonames.org/ontology#countryCode>",
    "<https://semopenalex.org/property/hasAssociatedInstitution>"
]

lvl_0_concepts = set(['17744445', '138885662', '162324750', '144133560', '15744967', '33923547', '71924100', '86803240',
                      '41008148', '127313418', '185592680', '142362112', \
                      '144024400', '127413603', '205649164', '95457728', '192562407', '121332964', '39432304'])

lvl_1_concepts = set(
    ['6303427', '19417346', '26271046', '2524010', '3079626', '46141821', '61696701', '41895202', '47768531',
     '126348684', '74909509', '165205528', '107053488', '121864883', '169760540', '126322002', '195094911', '512399662',
     '147597530', '164705383', '166957645', '171146098', '19165224', '29595303', '29694066', '33332235', '54355233',
     '73484699', '78519656', '112930515', '162118730', '11413529', '12554922', '13736549', '27206212', '29456083',
     '41999313', '24326235', '42219234', '43617362', '49774154', '77088390', '61434518', '126838900', '105639569',
     '108827166', '112698675', '195244886', '204321447', '2522767166', '149635348', '154945302', '97355855',
     '185544564', '187212893', '107826830', '524765639', '138496976', '139719470', '199289684', '505870484',
     '556758197', '70410870', '70721500', '78458016', '79403827', '105702510', '105795698', '120314980', '120665830',
     '177322064', '177713679', '548259974', '49204034', '114793014', '147789679', '167562979', '175444787', '178790620',
     '188147891', '2989005', '9390403', '91586092', '115903868', '134018914', '194828623', '199639397', '5900021',
     '21547014', '22212356', '31903555', '33070731', '74916050', '94375191', '119767625', '133731056', '144237770',
     '170154142', '8058405', '24667770', '46312422', '49040817', '87717796', '88463610', '111472728', '95444343',
     '145236788', '180747234', '13280743', '18903297', '24890656', '62649853', '118552586', '126255220', '131872663',
     '153294291', '87355193', '144027150', '526734887', '556039675', '6557445', '15708023', '66938386', '80444323',
     '90856448', '116915560', '118524514', '121684516', '136229726', '175605778', '528095902', '542102704', '1276947',
     '2549261', '36289849', '45355965', '75630572', '138921699', '147176958', '539667460', '1862650', '30475298',
     '50522688', '54286561', '73283319', '110354214', '133425853', '159110408', '159467904', '190253527', '199539241',
     '8010536', '77595967', '136264566', '153349607', '159390177', '161191863', '162853370', '165556158', '179104552',
     '188027245', '97137747', '100970517', '118487528', '148383697', '151730666', '40700', '4249254', '16674752',
     '21951064', '44154836', '48824518', '76155785', '111919701', '118615104', '136764020', '145420912', '150903083',
     '173608175', '178550888', '184779094', '187736073', '201995342', '548081761', '10138342', '58640448', '459310',
     '74363100', '107993555', '117671659', '16005928', '23123220', '38652104', '55493867', '56739046', '57879066',
     '202444582', '502942594', '98274493', '106159729', '140793950', '11171543', '13965031', '18547055', '31972630',
     '59822182', '62520636', '99508421', '124101348', '149782125', '159985019', '549774020', '16685009', '28490314',
     '37621935', '42475967', '53553401', '90924648', '121955636', '124952713', '171250308', '199104240', '200601418',
     '37914503', '71240020', '74650414', '113775141', '199360897', '3116431', '42972112', '44870925', '89423630',
     '100001284', '107457646', '155647269', '191897082', '509550671', '19527891', '31258907', '34447519', '39549134',
     '42407357', '55587333', '78762247', '118084267', '141071460', '149923435', '178802073', '199343813', '119857082',
     '42360764', '60644358', '77805123', '99454951', '545542383', '21880701', '26873012', '75473681', '107038049',
     '111368507', '126894567', '142724271', '155202549', '186060115', '187320778', '203014093', '28826006', '95124753',
     '114614502', '119599485', '134306372', '134560507', '143998085', '159047783', '1965285', '17409809', '52119013',
     '54750564', '91375879', '107872376', '109214941', '146978453', '153911025', '183696295'])

lvl_0_1_concepts = lvl_1_concepts.union(lvl_0_concepts)
ent_types = ['Work', 'Author', 'Venue', 'Institution']
root_path = ""


def extract_triples_from_file(fn):
    with open(str(root_path + fn),
              "w", encoding="utf-8") as g:
        with open(
                str(root_path + fn),
                "r", encoding="utf-8") as f:

            i = 0
            for line in f:
                line = line.replace("|", "").replace("> ",
                                                     ">|")  # del pipes first, then insert pipes as separators between objects
                pred = line.split("|")[1]

                if pred in pred_list:

                    if pred == "<https://semopenalex.org/property/hasAuthor>":
                        # remove author substring from subject of "authorposition" class
                        # <https://semopenalex.org/authorposition/W2100563011A2464960693>
                        # to maintain relation work -> author directly (no intermediary authorposition object)

                        line = (line[:line.index("A")] + line[line.index(">"):])
                        line = line.replace("authorposition", "work")
                        g.write(line.replace("|", " "))

                    elif pred == "<https://semopenalex.org/property/hasConcept>":
                        # use 0-level concepts only
                        # <https://semopenalex.org/conceptscore/W1578179182C121332964>
                        # length check excludes conceptscore subject relation
                        if len(line.split("|")[0]) in range(40, 49) and "work" in line.split("|")[0]:
                            if line.split("|")[2].replace("<https://semopenalex.org/concept/C", "").replace(">",
                                                                                                            "") in lvl_0_1_concepts:
                                g.write(line.replace("|", " "))

                    elif pred == "<http://www.geonames.org/ontology#countryCode>":
                        # country code relation for institutions. Remove intermediary geo object

                        line = line.replace("https://semopenalex.org/geo/", "https://semopenalex.org/institution/")
                        g.write(line.replace("|", " "))

                    elif pred == "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>":
                        # extract the type relation for works, authors, venues and institutions
                        if line.split("|")[2].replace("<https://semopenalex.org/class/", "").replace(">",
                                                                                                     "") in ent_types:
                            g.write(line.replace("|", " "))

                    elif pred == "<https://semopenalex.org/property/crossrefType>":
                        # shorten the extracted work type, remove crossref prefix
                        line = line.replace("https://api.crossref.org/types/", "")
                        g.write(line.replace("|", " "))

                    elif pred == "<https://semopenalex.org/property/hasHostVenue>":
                        # remove auxiliary hostvenue class, build link from work to venue directly
                        # object in triple (the hostvenue) is modified such that it resembles the actual venue URI
                        obj = line.split("|")[2]
                        obj_no_hops = (obj[:obj.index("W")] + obj[obj.index("V"):]).replace("hostvenue", "venue")

                        line = line.replace(obj, obj_no_hops)
                        g.write(line.replace("|", " "))

                    else:
                        g.write(line.replace("|", " "))

                if i % 1000000000 == 0:
                    print(f"{i / 1000000}mio. lines processed..")
                i += 1

    return True


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(('usage: python3 extract_triples_on_lsdf.py <file_to_process.txt/.nt>'))
        sys.exit()
    text_file_to_process = sys.argv[1]
    ret = extract_triples_from_file(text_file_to_process)
    if not ret:
        print("### Done ###")
        sys.exit()
