import argparse
from onto import Ontology
import os

def normalize(ont, hpid_filename, column=0):
    concepts = [c.strip().split()[column].replace("_",":") for c in open(hpid_filename).readlines()]
    filtered = [ont.real_id[c] for c in concepts if c in ont.real_id] 
    # and x.replace("_",":").strip()!="HP:0003220" and x.replace("_",":").strip()!="HP:0001263"and x.replace("_",":").strip()!="HP:0001999"]
    #raw = [ont.real_id[x.replace("_",":").strip()] for x in open(hpid_filename).readlines()]
    return set([c for c in filtered if c in ont.concepts])

def get_all_ancestors(ont, hit_list):
    return set([ont.concepts[x] for hit in hit_list for x in ont.ancestrs[ont.concept2id[hit]]])

def eval(label_dir, output_dir, file_list, ont, column=0, comp_dir=None):
    total_precision = 0
    total_recall = 0
    total_oprecision = 0
    total_orecall = 0
    total_docs = 0

    total_relevant = 0
    total_positives = 0
    total_true_pos = 0

    jaccard_sum = 0
    false_pos_all = {}

    for filename in file_list:
    #for filename in open(file_list).readlines():
        filename = filename.strip()
        real = normalize(ont, label_dir+"/"+filename)
        #real = normalize(ont, label_dict[filename])

        extended_real = get_all_ancestors(ont, real)

        assert comp_dir == None ## needs to be checked
        if comp_dir!=None:
            comp_positives = normalize(ont, comp_dir+"/"+filename)
            extended_comp_positives = get_all_ancestors(ont, comp_positives)
        positives = normalize(ont, output_dir+"/"+filename, column)
        #positives = normalize(ont, output_dict[filename])

        extended_positives = get_all_ancestors(ont, positives)
        true_pos = [x for x in positives if x in real]
        false_pos = [x for x in positives if x not in real]
  ##      if "HP:0001263" in false_pos:
   ##         print filename
        for x in false_pos:
            if x not in false_pos_all:
                false_pos_all[x] = 0
            false_pos_all[x] += 1


        precision = 0
        oprecision = 0
        if len(positives)!=0:
            precision = 1.0*len(true_pos)/len(positives)
            oprecision = 1.0*len(positives & extended_real)/len(positives)

        recall = 0
        orecall = 0
        if len(real)!=0:
            recall = 1.0*len(true_pos)/len(real)
            orecall = 1.0*len(real & extended_positives)/len(real)

        total_docs += 1
        total_precision += precision
        total_recall += recall
        total_oprecision += oprecision
        total_orecall += orecall
        #print filename, '\t', precision, '\t', recall

        total_relevant += len(real)
        total_positives += len(positives)
        total_true_pos += len(true_pos)
        
        if len(extended_real | extended_positives) == 0:
            jaccard = 1.0
        else:
            jaccard = 1.0 * len(extended_real & extended_positives) / len(extended_real | extended_positives)
            if comp_dir!=None and len(extended_real | extended_comp_positives)!=0:
                jaccard_comp = 1.0 * len(extended_real & extended_comp_positives) / len(extended_real | extended_comp_positives)
                if jaccard<jaccard_comp:
                    print(filename)


        jaccard_sum += jaccard

    precision = total_precision/total_docs
    recall = total_recall/total_docs
    fmeasure = 2.0*precision*recall/(precision+recall)

    oprecision = total_oprecision/total_docs
    orecall = total_orecall/total_docs
    ofmeasure = 2.0*oprecision*orecall/(oprecision+orecall)

    if total_positives>0:
        mprecision = 1.0*total_true_pos/total_positives
    else:
        mprecision = 1.0
    mrecall = 1.0*total_true_pos/total_relevant
    mfmeasure = 2.0*mprecision*mrecall/(mprecision+mrecall)

    jaccard_mean = jaccard_sum/total_docs

    ##for hp,ct in sorted(false_pos_all.iteritems(), key=lambda (k,v): (-v,k)):
##        print hp, ont.names[hp][0], ct
    ret = {"ont":{"precision":oprecision, "recall":orecall, "fmeasure":ofmeasure}, "vanila":{"precision":precision, "recall":recall, "fmeasure":fmeasure}, "micro":{"precision":mprecision, "recall":mrecall, "fmeasure":mfmeasure}, "jaccard":jaccard_mean}
    return ret
    '''
    print "Precision:", precision
    print "Recall:", recall 
    print "F-measure:", 2.0*precision*recall/(precision+recall)

    print "Micro Precision:", mprecision 
    print "Micro Recall:", mrecall 
    print "Micro F-measure:", 2.0*mprecision*mrecall/(mprecision+mrecall)
    '''

'''
def roc(label_dir, output_dir, file_list, rd):
    exps = []
    for i in range(1,10):
        exps.append(eval(label_dir, output_dir+"_0."+str(i), file_list, rd))
#    exps = sorted(exps, key= lambda x: x["micro"]["recall"])
    recalls = [x["micro"]["recall"] for x in exps]
    precisions = [x["micro"]["precision"] for x in exps]
    print recalls
    print precisions

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    plt.plot([x/10.0 for x in range(1,10)], precisions, 'r', label="precision")
    plt.plot([x/10.0 for x in range(1,10)], recalls, 'b', label="recall")
    plt.ylabel('accuracy')
    plt.xlabel('Threshold')
    plt.axis([0.0, 1.0, 0.0, 1.0])
    plt.legend(loc='upper left')
#    plt.show()
    plt.savefig("roc.pdf")
'''


def main():
    parser = argparse.ArgumentParser(description='Hello!')
    parser.add_argument('label_dir', help="Path to the directory where the input text files are located")
    parser.add_argument('output_dir', help="Path to the directory where the output files will be stored")
    parser.add_argument('--obofile', help="address to the ontology .obo file")
    parser.add_argument('--oboroot', help="the concept in the ontology to be used as root (only this concept and its descendants will be used)")

    parser.add_argument('--file_list', help="Path to the directory where the output files will be stored")
    parser.add_argument('--comp_dir', help="Path to the directory where the output files will be stored")
    parser.add_argument('--output_column', type=int, help="", default=0)
    args = parser.parse_args()

    file_list = os.listdir(args.output_dir)
    if args.file_list != None:
        file_list = [x.strip() for x in open(args.file_list).readlines()]

    ont = Ontology(args.obofile, args.oboroot)

    results = eval(args.label_dir, args.output_dir, file_list, ont, column=args.output_column)#, args.comp_dir)
    #results = eval(args.label_dir, args.output_dir, open(args.file_list).readlines(), ont, args.comp_dir)
    res_print = []
    for style in ["micro", "vanila", "ont"]: 
        for acc_type in ["precision", "recall", "fmeasure"]: 
            res_print.append(results[style][acc_type])
    res_print.append(results['jaccard'])

    res_print = [x*100 for x in res_print]
    print("%.1f & %.1f & %.1f & %.1f & %.1f & %.1f & %.1f & %.1f & %.1f & %.1f\\\\" % tuple(res_print))
    #print "%.4f & %.4f & %.4f & %.4f & %.4f & %.4f & %.4f\\\\" % tuple(res_print)

    #roc(args.label_dir, args.output_dir, args.file_list, rd)
if __name__ == "__main__":
	main()
