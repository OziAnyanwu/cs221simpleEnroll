"""
Code for Simple Enroll: A Course Schedule Recommendation tool.
CS 221 Aut 2019
Authors:
Robert Heckerman, Ozioma-Jesus Anyanwu
"""
import json
import util, math, random
from collections import defaultdict
from util import ValueIteration, simpleEnroll
from itertools import combinations
import time
import sys
############################################################

class CourseMDP(util.MDP):
    def __init__(self, start,bulletin):
        """
        We define all dictionaries necessary to model our Course MDP.
        """
        #Maps letter grades to GPA values. Used in compting reward.
        self.gpaToScore = {"A+": 4.3, "A": 4.0, "A-": 3.0, "B+": 1.5,
                            "B": 1.2, "B-": 1.0, "C+": 0.5, "C": 0.4,
                            "C-": 0.3, "D+": 0.1, "D": 0.05, "D-": 0.02,
                            "NP": 0.0}

        #Maps a time commitment range to the average value of the range.
        #Used in computing total time commitment of a course load.
        self.timeRangeToNum = {"<5": 2.5, "5-10": 7.5, "10-15": 12.5, "15-20": 17.5,
                               "20-25": 22.5, "25-30": 27.5, "30-35": 32.5, "35+": 40}

        #Maps time commitment ranges (in hrs) to reward value. Used in computing reward.
        self.timeToScore = {range(0, 10): 3, range(10, 20): 3.5, range(20, 30): 4,
                            range(30, 40): 3.75, range(40, 50): 2, range(50, 60): 1,
                            range(60, 70): 0.5, range(70, 80): 0, range(80, 90): -1,
                            range(90, 168): -3}

        #Maps the current quarter to the succeeding quarter.
        #Used to advance to the next state.
        self.nextQuarter = {"Aut":"Win","Win":"Spr","Spr":"Aut"}

        #Course bulletin. This maps a course cid (e.g "MATH 19:) to a dict containg the following keys->value pairs
            #1. Key: "grades" -> Val: dict of grade distributions as collected from CARTA. E.g {"A+":4,"A":20,...."D-":2} means 4% of people got A+ etc...
            #2. Key: "times" -> Val: dict of time intensity distribution as collected from CARTA. E.g {"<5":5, "5-10":33} means 5% of people spent <5hrs/week in the calss
            #3. Key: "evals" -> Val: dict containing average evaluation scores for different professors that have taught the class (Evaaluations tab on CARTA)
            #4. Key: "prereqs" -> Val: list of prerequisites of this class.
            #5. Key: "quarters" -> Val: list of quarters the class is offered.
            #6. Key: "units" -> Val: maximum number of units the course can be taken for
            #7. Key: "categories" -> Val: categories the class falls under. We came up with these. These are useful for identifying what "types" of classes a student might perform well in.
            #8. Key: "cid" -> Val: the course id.
        self.bulletin = bulletin

        #User-defined start state.
        self.start = start

        #Complete set of classes that are prerequisites to other classes for CS AI students
        #Used in determining what classes the user has taken are prerequisites to any class.
        self.possiblePreq = {"CS 110", "MATH 19", "MATH 20",
                            "CS 106B", "MATH 51", "CS 103",
                            "MATH 21", "MATH 104", "PHYSICS 41",
                            "CS 106A", "CS 107", "CS 109",
                            "CS 221", "CS 161", "CS 229",
                            "EE 261", "EE 278", "CS 124", "CS 131",
                            "CS 108","CS 140","CS 144","CS 145","CS 154"
                            }

        #Set of absolutely required classes for the CS AI track.
        self.mustHaves = {"MATH 19", "MATH 20", "MATH 21",
                    "CS 103", "CS 109", "PHYSICS 41",
                    "PHYSICS 43", "CS 106A", "CS 106B",
                    "ENGR 40M", "CS 107", "CS 110",
                    "CS 161", "CS 221"}

        #Number of math electives required for the CS AI track
        self.mathNeeded = 2

        #Set of classes that can be used as Math electives for the CS AI track
        self.mathElectives = {"MATH 51", "MATH 52" , "MATH 53",
                            "MATH 104", "MATH 107", "MATH 108",
                            "MATH 109","MATH 110", "MATH 113","CS 157",
                            "CS 205L", "PHIL 151", "CME 100", "CME 102",
                            "CME 103" "CME 104"}

        #Sets of classes that satisfy the tack B and track C requirements for the CS AI track.
        self.trackBi = {"CS 228","CS 229","CS 234","CS 238"}
        self.trackBii = {"CS 124","CS 224N","CS 224U"}
        self.trackBiii = {"CS 131","CS 231N"}
        self.trackBiv = {"CS 223A","CS 237A"}
        self.trackC = { "CS 157","CS 205L", "CS 230", "CS 236", "CS 235", "CS 279", "CS 371",
                        "CS 224W", "CS 276", "CS 151", "CS 227B", "CS 379", "CS 327A", "ENGR 205",
                        "MS&E 251", "MS&E 351"}
        self.trackCNeeded = 1

        #Set of general CS electives
        self.generalElective = {"CS 108", "CS 140",
                                "CS 142","CS 143","CS 144","CS 145","CS 146",
                                "CS 147","CS 148","CS 149","CS 154","CS 155",
                                "CS 166","CS 168","CS 190","CS 195","CS 197",
                                "CS 210A","CS 217",
                                "CS 225A","CS 227B","CS 230",
                                "CS 231A","CS 232","CS 233",
                                "CS 237B","CS 238","CS 240","CS 242","CS 243",
                                "CS 244","CS 244B","CS 245","CS 246","CS 248","CS 251","CS 252",
                                "CS 254","CS 254B","CS 255","CS 261","CS 264","CS 265","CS 269I",
                                "CS 269Q","CS 270","CS 272","CS 273A","CS 273B","CS 274",
                                "CS 278","CS 330","CS 336","CS 352","CS 353","CS 369L","CS 398",
                                "CME 108","EE 180","EE 282","EE 364A"}

        #Set of classes that satisfy the CS elective requirement for the CS AI track
        self.cs_elective = {"CS 237B", "CS 257", "CS 275", "CS 326", "CS 330",
                            "CS 334A", "CS 336", "CS 398", "CS 428", "EE 263",
                            "EE 278", "EE 364B", "ECON 286", "MS&E 252","MS&E 352",
                            "MS&E 355", "PHIL 152", "PSYCH 204A", "PSYCH 204B", "PSYCH 209",
                            "STATS 200", "STATS 202", "STATS 205"}.union(self.generalElective)

        #Number of CS electives needed for the CS AI track
        self.cs_electiveNeeded = 3

        #Maps a number representing the student's year (1 is Frosh, 4 is Senior)
        #to a number representing the importance of taking classes that satisfy graduation requirements.
        #Intuitively, if you're a senior, we attribute a high weight because we assume you want to finish in 4 yrs.
        #If you're a freshman, you're more willing to explore courses that are not necessarily graduation reqruiements.
        self.progWeight = {1:0.25, 2:0.5, 3:1.5, 4:5.0}

        #Maps each letter grade to the succeeding letter grade in decending order.
        #Used in computing grade percentiles. More on this
        self.gradeToNext = {"A+": "A", "A": "A-", "A-": "B+", "B+": "B", "B": "B-",
                            "B-": "C+",  "C+": "C", "C": "C-", "C-": "D+", "D+": "D",
                            "D": "D-", "D-": "NP", "NP": "None"}

        #Set of ways acronyms for testing purposes
        self.ways = {"er", "ce", "ed", "si", "aii"}

        #Subsets of classes for each WAYS that isn't satisfied by the CS core.
        self.er = {"CS 181W", "BIOE 131", "ETHICSOC 171"}
        self.ce = {"MUSIC 19A", "ARTSTUDI 170"}
        self.ed = {"GERMAN 101", "ANTHRO 82", "HISTORY 107"}
        self.si = {"PSYCH 1", "ECON 1", "ANTHRO 1", "COMM 154", "COMM 166"}
        self.aii = {"ARTHIST 1B", "PHIL 1", "PHIL 2"}

    # Return the user-defined start state.
    # Each state is a tuple with 4 elements:
    #   -- The first element of a k-element tuple where k is the number of previous classes the user has takenSet
    #       -Each element e is a 2-element tuple where e[0] is the cid of the course and e[1] is the grade the user got in that courses
    #       -Example: (("MATH 19", "A"),  ("CS 106A", "A"), ("MATH 20", "A")) <- user inputted 3 previous coursese taken
    #   -- The second element is the quarter the user is entering ("Aut", "Win", or "Spr")
    #   -- The third element is the year (integer) the user is currently in (1,2,3,4)
    #   -- The fourth element is a tuple of classes that the user wants to take in the quarter he's registering courses for.
    #       --Any courses included in here will appear in the output recommendation.
    #       --We're adding this option because there are circumstances an optimization algorithm can't account for
    #         For example, some students will take a class in a quarter because they have lots of friends taking it at the same time.
    def startState(self):
        return self.start

    # Return set of actions possible from |state|.
    # This is represented by a list of all valid course schedules
    # --Specifically, this list contains several sets of class combinations, where each set represents a potential course schedule.
    def actions(self, state):
        #No valid actions if we're not at the start state
        if(state[1] == self.nextQuarter[self.start[1]]):
            return ['None']

        ## Add in pre-reqs to satisfy classes constrained by user (classes the user said they want to take) ##
        courseTaken = set([i for i,_ in state[0]])
        preqsTaken = courseTaken.intersection(self.possiblePreq)
        for cid in state[3]:
            for preq in self.bulletin[cid]["prereqs"]:
                preqsTaken.add(preq)

        ## Create a list of all classes the user can take given the classes he's taken ##
        l = []
        for cl in self.bulletin:
            if len(set(self.bulletin[cl]['prereqs']) - preqsTaken) == 0:
                if cl not in courseTaken and state[1] in self.bulletin[cl]['quarters']:
                    l.append(cl)
        newL = l

        ## Generate the possible course schedules ##
        possibleActions = []
        for r in range(3,4):
            l = list(combinations(newL,r))
            for combo in l:
                s = sum([self.bulletin[cid]['units'] for cid in combo])
                if s >= 12 and s <= 20:
                    possibleActions.append(combo)

        ## Filter away all course schedules that don't include the user's constraints ##
        finalActions = [action for action in possibleActions if set(state[3]).issubset(set(action))]

        return finalActions

    # Given a |state| and |action|, return a list of (newState, prob, reward) tuples
    # corresponding to the states reachable from |state| when taking |action|.
    def succAndProbReward(self, state, action):
        #Converts a percentage to a decimal
        def getProb(x):
            return x/100

        ## ----- BEGIN: SUBROUTINES FOR COMPUTING REWARDS ----- ##

        #   Subroutine #1:
        #   Returns a value proportional to the number of classes in |action|
        #   that satisfy some graduation requirment
        #   which you haven't previously satisfied.
        def calcProg(classesDict):
            #Components of the graduation progress reward
            mustHavesProgress = 0
            mathProgress = 0
            bProgress = 0
            cProgress = 0
            totalProgress = 0

            #Initialize 2 sets:
            #   takingSet contains the classes that the student is taking this quarter
            #   takenSet contains the classes that the student has taken so far
            takingSet = set([c for c in classesDict])
            takenSet = set([c[0] for c in state[0]])
            totalClasses = len(takingSet)

            #Calculates the number of classes that the student is taking this quarter which
            #complete a core CS requirement
            taking_for_mustHaves = takingSet.intersection(self.mustHaves.difference(takenSet))
            mustHavesProgress = len(taking_for_mustHaves)
            takingSet = takingSet.difference(taking_for_mustHaves)

            #Calculates the number of classes that the student is taking this quarter which
            #complete a math elective. Notice that only 2 math electives count toward progress.
            #Also notice that if we've already taken one or two math electives, our potential
            #progress is limited to one or zero respectively.
            numMathSoFar = len(takenSet.intersection(self.mathElectives))
            taking_for_math = takingSet.intersection(self.mathElectives)
            numMathThisTime = min(len(taking_for_math), 2)
            mathProgress = max(numMathThisTime - numMathSoFar, 0)
            takingSet = takingSet.difference(taking_for_math)

            oldBi = self.trackBi.intersection(takenSet) #what I've taken that satisfies Bi
            oldBii = self.trackBii.intersection(takenSet)
            oldBiii = self.trackBiii.intersection(takenSet)
            oldBiv = self.trackBiv.intersection(takenSet)
            newBi = self.trackBi.intersection(takingSet) #what I'm taking that satisfies Bi
            newBii = self.trackBii.intersection(takingSet)
            newBiii = self.trackBiii.intersection(takingSet)
            newBiv = self.trackBiv.intersection(takingSet)

            #Things get a bit hairy here. First, we figure out which of the Track B requirements
            #we've satisfied so far. If we use a class to satisfy one of these requirments, let's
            #pop that class from it's set. Observe that we can only use one class per subtrack,
            #that is, if a subtrack has already been satisfied, we can't use another class in that
            #subtrack to move toward graduation.
            bSatisfied = set()
            if len(oldBi) >= 1:
                oldBi.pop()
                bSatisfied.add("bi")
            if len(oldBii) >= 1:
                oldBii.pop()
                bSatisfied.add("bii")
            #if we've already satisfied both Track B requirements, stop checking to see if one of
            #our classes helps satisfy Track B.
            if len(oldBiii) >= 1 and len(bSatisfied) < 2:
                oldBiii.pop()
                bSatisfied.add("biii")
            if len(oldBiv) >= 1 and len(bSatisfied) < 2:
                oldBiv.pop()
                bSatisfied.add("biv")

            #we only make new progress (progress from our takingSet) toward Track B if we haven't satisfied
            #both track B requirements before, and one of our new classes is a Track B class
            if not "bi" in bSatisfied and len(bSatisfied) < 2 and len(newBi) > 0:
                newBi.pop()
                bSatisfied.add("bi")
                bProgress += 1

            if not "bii" in bSatisfied and len(bSatisfied) < 2 and len(newBii) > 0:
                newBii.pop()
                bSatisfied.add("bii")
                bProgress += 1

            if not "biii" in bSatisfied and len(bSatisfied) < 2 and len(newBiii) > 0:
                newBiii.pop()
                bSatisfied.add("biii")
                bProgress += 1

            if not "biv" in bSatisfied and len(bSatisfied) < 2 and len(newBiv) > 0:
                newBiv.pop()
                bSatisfied.add("biv")
                bProgress += 1

            #Since we have been popping the classes we used to satisfy requirements from their
            #respective sets, we can build two new sets which contain the overflow from Track B
            #(classes that satisfy some Track B class, but weren't used to satisfy a subtrack).
            #These classes can be used to either satisfy Track C, or a general CS elective.
            oldBOverflow = oldBi.union(oldBii, oldBiii, oldBiv)
            newBOverflow = newBi.union(newBii, newBiii, newBiv)

            oldC = self.trackC.intersection(takenSet)
            newC = self.trackC.intersection(takingSet)

            if len(oldC) > 0:
                oldC.pop()

            elif len(oldBOverflow) > 0:
                oldBOverflow.pop()

            #if our new classes complete the Track C requirement
            elif len(oldBOverflow) == 0 and len(oldC) == 0 and len(newBOverflow) > 0:
                newBOverflow.pop()
                cProgress = 1

            elif len(oldBOverflow) == 0 and len(oldC) == 0 and len(newC) > 0:
                newC.pop()
                cProgress = 1

            #Build two new sets which contain the general cs electives we have completed so far
            #(oldElectives) and the ones our classes this quarter complete (newElectives). Notice
            #that whatever overflow we have left can still be used as a general CS elective.
            oldElectives = self.cs_elective.intersection(takenSet).union(oldC, oldBOverflow)
            newElectives = self.cs_elective.intersection(takingSet).union(newC, newBOverflow)
            numOldElectives = len(oldElectives)
            numNewElectives = min(len(newElectives),3)
            electiveProgress = max(numNewElectives - numOldElectives,0)


            #lastly, let's deal with our WAYs. An important thing to note here is that a few
            #WAYs are automatically satisfied by the other requirements. We will just be handling
            #the ways that aren't automatically satisfied here.


            #first, let's count how many times they enter each non-distinct WAY
            oldGeneralEr = 0
            oldGeneralCe = 0
            oldGeneralEd = 0
            oldGeneralSi = 0
            oldGeneralAii = 0

            #can't use taken set, since that would not let us enter in a generic
            #ways class multiple times
            for c in state[0]:
                if c[0] == "er":
                    oldGeneralEr += 1
                elif c[0] == "ce":
                    oldGeneralCe += 1
                elif c[0] == "ed":
                    oldGeneralEd += 1
                elif c[0] == "si":
                    oldGeneralSi += 1
                elif c[0] == "aii":
                    oldGeneralAii += 1

            #add on whatever specific WAYs classes they've taken before
            oldGeneralEr += len(self.er.intersection(takenSet))
            oldGeneralCe += len(self.ce.intersection(takenSet))
            oldGeneralEd += len(self.ed.intersection(takenSet))
            oldGeneralSi += len(self.si.intersection(takenSet))
            oldGeneralAii += len(self.aii.intersection(takenSet))

            #find the number of new WAYs classes and cap the amount of progress
            #they can make to the appropriate amount
            newEr = min(1, len(self.er.intersection(takingSet)))
            newCe = min(1, len(self.ce.intersection(takingSet)))
            newEd = min(1, len(self.ed.intersection(takingSet)))
            newSi = min(2, len(self.si.intersection(takingSet)))
            newAii = min(2, len(self.aii.intersection(takingSet)))

            #calculate are progress toward each WAY
            erProgress = max(0, newEr - oldGeneralEr)
            ceProgress = max(0, newCe - oldGeneralCe)
            edProgress = max(0, newEd - oldGeneralEd)
            siProgress = max(0, newSi - oldGeneralSi)
            aiiProgress = max(0, newAii - oldGeneralAii)

            #lastly, add up all of our progress together to figure out how many of our classes
            #make progress toward some requirement
            totalProgress = electiveProgress + mathProgress + mustHavesProgress + bProgress + cProgress \
                            + erProgress + ceProgress + edProgress + siProgress + aiiProgress
            totalProgress /= totalClasses
            totalProgress *= 4.3


            return totalProgress

        #   Subroutine #2:
        #   Returns the GPA obtained by getting a specific
        #   set of grades for the classes in |action|
        #   |classesDict| is |action|, but with a grade associated with each class.
        def calcGPA(classesDict):
            totalUnits = 0
            totalScore = 0
            for c, grade in classesDict.items():
                units = self.bulletin[c]["units"]
                classScore = self.gpaToScore[grade]
                totalUnits += units
                totalScore += units * classScore
            return totalScore/totalUnits

        #  Subroutine #3:
        #  Returns the reward value for the course evaluations
        #  of the teachers teaching each course in |action| (aka |classesDict|)
        def calcEval(classesDict):
            totalEval = 0
            for c in classesDict:
                #Get the professor
                professor = self.bulletin[c]["quarters"][state[1]]

                #If he's taught the class before, use his previous evaluation
                if professor in self.bulletin[c]["evals"]:
                    totalEval += self.bulletin[c]["evals"][professor]

                #Otherwise, get the average of all teachers that have taught the course
                else:
                    tempEval = 0
                    for eval in self.bulletin[c]["evals"].values():
                        tempEval += eval
                    totalEval += tempEval/len(self.bulletin[c]["evals"].values())
            return (totalEval/len(classesDict)) * (4.3/5)

        #  Subroutine #4:
        #  Returns the reward value for the tota time commitment of the quarter--
        #  i.e the total time commitment of each class in |action| (aka |classesDict|)
        def calcTime(classesDict):
            totalTime = 0
            for c in classesDict:
                timeDist = self.bulletin[c]["time"]
                totalPercent = 0

                #Compute median time-commitment and add to totalTime
                for time, percent in timeDist.items():
                    totalPercent += percent
                    if totalPercent >= 50:
                        totalTime += self.timeRangeToNum[time]
                        break
            totalTime = int(totalTime)

            #Find which time-range the totalTime falls into
            # and return the score for that time-range
            for r in self.timeToScore:
                if totalTime in r:
                    return self.timeToScore[r]
        ## ----- END: SUBROUTINES FOR COMPUTING REWARD ----- ##

        #function to convert someone's |grade| in a class |c| into their percentile in
        #that class. places grade in middle of appropriate bar
        def gradeToPercentile(grade, c):
            curGrade = "A+"
            grades = self.bulletin[c]["grades"]
            accumulated = grades[curGrade]

            while curGrade != grade:
                curGrade = self.gradeToNext[curGrade]
                accumulated += grades[curGrade]

            #since we want the middle of the bar for the grade acheieved,
            accumulated -= (1/2) * grades[curGrade]
            #to convert to actually percentile
            accumulated = 100 - accumulated

            if accumulated < 0:
                accumulated = 0.5
            return accumulated

        #function to convert someone's |percentile| in a class |c|
        #into their grade in that class.
        def percentileToGrade(percentile, c):
            toPass = 100 - percentile

            curGrade = "A+"
            grades = self.bulletin[c]["grades"]
            accumulated = grades[curGrade]

            while toPass >= accumulated:
                curGrade = self.gradeToNext[curGrade]
                accumulated += grades[curGrade]
                if curGrade == "NP":
                    break

            return curGrade

        ##--CODE FOR COMPUTING SUCCESSOR STATES AND PROBABILTIES--##

        # Build a dict mapping each category to the students
        # previous performances in that category
        studentPerformance = {}
        for cid, grade in state[0]:
            if cid in self.ways:
                continue
            categories = self.bulletin[cid]["categories"]
            for cat in categories:
                if cat not in studentPerformance:
                    studentPerformance[cat] = [gradeToPercentile(grade, cid)]
                else:
                    studentPerformance[cat].append(gradeToPercentile(grade, cid))

        #Recurrance for computing all potential successors from (|state|,|action|)
        def recurse(taken,prob,available,successors,soFar):
            # Base Case:
            # newState now contains all classes in |action| with a potential set of grades we could have gotten.
            # Compute the reward of reaching that state using the subroutines we defined above.
            # prob is the product of the probablities of getting the specific grade in each of the classes.
            if len(available) == 0:
                newState = (taken,self.nextQuarter[state[1]],state[2],())
                p = prob
                gpaScore = calcGPA(soFar)
                evalScore = calcEval(soFar)
                timeScore = calcTime(soFar)
                progScore = calcProg(soFar)
                reward = gpaScore + evalScore + 1.1 * timeScore + self.progWeight[state[2]]*progScore
                successors.append((newState,p,reward))

            # Recursive Case: #
            else:
                #pick a courseID from the courses recommended in |action|
                cid = available[0]

                # Create a list of percentiles the student was in when taking classes similar to "cid"
                studentsPercentile = []
                categories = self.bulletin[cid]["categories"]
                for cat in categories:
                    if cat in studentPerformance:
                        studentsPercentile += studentPerformance[cat]

                # If student hasn't taken classes in similar categories, use the grade distribution
                # to determine probabilities of him obtaining a certain grade.
                if studentsPercentile == []:
                    for grade in self.bulletin[cid]["grades"]:
                        p = getProb(self.bulletin[cid]["grades"][grade])
                        if (p > 0):
                            newSoFar = soFar.copy()
                            newSoFar[cid] = grade
                            newTaken = list(taken)
                            newTaken.append((cid,grade))
                            newTaken = tuple(newTaken)
                            recurse(newTaken,p*prob,available[1:],successors,newSoFar)

                # Otherwise, convert the percentiles to grades and pick
                # grade with probability proportional to the number of times he's obtained
                # this grade in previous classes of similar category.
                else:
                    gradeMapping = {}
                    for percent in studentsPercentile:
                        grade = percentileToGrade(percent, cid)
                        if grade in gradeMapping:
                            gradeMapping[grade] += 1
                        else:
                            gradeMapping[grade] = 1

                    for grade in gradeMapping:
                        p = gradeMapping[grade] / len(studentsPercentile)
                        newSoFar = soFar.copy()
                        newSoFar[cid] = grade
                        newTaken = list(taken)
                        newTaken.append((cid,grade))
                        newTaken = tuple(newTaken)
                        recurse(newTaken,p*prob,available[1:],successors,newSoFar)

        #No successors if we're at an end state
        if(state[1] == self.nextQuarter[self.start[1]] or action == 'None'):
            return []

        #No successors if the action contains a class i've already taken
        for takenClass,_ in state[0]:
            if takenClass in action:
                return []

        succs = []
        classesDict = {} #will contain each class in |action| with a grade associated
        recurse(state[0],1,action,succs,classesDict)
        return succs

    def discount(self):
        return 1

bulletin = json.loads(open('cartadata.json').read())
#Run  Value Iteration"
startState = simpleEnroll(bulletin)
# startState = ((("MATH 19", "A"), ("MATH 20", "A"), ("CS 106B","B+"),("MATH 21", "A"),("ECON 1","A"),("MATH 51", "A-"),("CS 107", "A-"),
#                 ("CS 106A", "A"), ("CS 109", "A")),
#                  "Aut", 2, ())



courseMDP = CourseMDP(startState,bulletin)
vi = ValueIteration()
vi.solve(courseMDP)
pi_vi = vi.pi
value = vi.V
bestAction = pi_vi[startState]

#Print our recommended schedule!
print("Best Action: ", bestAction)
