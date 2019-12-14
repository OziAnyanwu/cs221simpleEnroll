import json
import util, math, random
from util import ValueIteration
from itertools import combinations
import time


#we don't really care about code cleanliness here

bulletin = json.loads(open('cartadata.json').read())

def getBest(state, classes_to_recommend, desired):

    recommended_classes = []
    if len(desired) > 0:
        recommended_classes += desired
        classes_to_recommend -= len(desired)

    classes_taken = [c[0] for c in state[0]]
    for _ in range(classes_to_recommend):
        max_score = float('-inf')
        max_class = 'None'

        for c in bulletin:
            score = 0

            prereqs_sat = True
            for prereq in bulletin[c]['prereqs']:
                if prereq not in classes_taken:
                    prereqs_sat = False

            if c not in classes_taken and c not in recommended_classes and \
            state[1] in bulletin[c]['quarters'] and prereqs_sat:
                professor = bulletin[c]["quarters"][state[1]]
                if professor in bulletin[c]["evals"]:
                    score = bulletin[c]["evals"][professor]
                else:
                    temp_score = 0
                    for eval in bulletin[c]["evals"].values():
                        temp_score += eval
                    score = temp_score/len(bulletin[c]["evals"].values())
            if score > max_score:
                max_score = score
                max_class = c

        recommended_classes.append(max_class)

    return recommended_classes

# This is just an ugly way to get our output. Sorry! We figured that the user
# won't really be interacting with this much. This code is most to test the efficacy
# of our baseline
print(getBest(((("ce", "A"), ("PSYCH 1", "B+"), ("ECON 1", "A-")), ("Aut")), 3, ["CS 106A"]))
