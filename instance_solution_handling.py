# AUTOGENERATED! DO NOT EDIT! File to edit: 00_gcsp_bc_instance_solution_handling.ipynb (unless otherwise specified).

__all__ = ['Activity', 'csp_bc_instance', 'get_activity_str', 'get_activity_con_str', 'get_duty_str', 'get_pairing_str',
           'write_solution', 'read_solution', 'get_problem_variants', 'get_n_activities_to_range_n_crews',
           'get_instance_and_range_crew_members', 'get_dict_results_ds', 'get_obj_ds', 'claimed_optimal_ds',
           'check_duty', 'check_pairing', 'check_pairings', 'get_number_of_layovers', 'get_number_of_duties',
           'get_number_of_duties_counting_single_duties_twice', 'get_number_of_deadheads',
           'get_maximum_number_of_deadheads_per_duty', 'get_maximum_number_of_deadheads_in_sequence',
           'get_maximum_number_of_deadheads_in_sequence_per_duty', 'get_maximum_number_of_activities_per_duty',
           'get_number_of_work_activities', 'get_maximum_number_of_work_activities_per_duty', 'get_pairings_from_file',
           'check_sol_from_file']

# Cell

import os
from dataclasses import dataclass, field
import csv
from collections import namedtuple
from IPython.display import display, Markdown
import pandas as pd

# Cell

@dataclass(eq=True, order= True, frozen=True)
class Activity:
    index: int
    start_period: int
    end_period: int
    activity_type: str = 'work'

    def get_start_period(self):
        return self.start_period

    def get_end_period(self):
        return self.end_period

    def get_number_of_periods(self):
        return self.end_period - self.start_period

    def is_work(self):
        return self.activity_type == 'work'



# Cell

class csp_bc_instance():

    def __init__(self, filename):
        #line =
        self.instance_name = filename[filename.rfind('/')+1:-4]
        with open(filename) as f:
            line = f.readline().split()
            self.number_of_activities = int(line[0])
            self.max_work_periods = int(line[1])

            self.activities = []
            self.last_end_period = 0


            for i in range(self.number_of_activities):

                line = f.readline().split()

                self.activities.append( Activity(i, int(line[0]),int(line[1])))
                self.last_end_period = max(self.last_end_period, int(line[1]))


            self.earliest_start_after_layover = 240 # 1200 + 480 - 1440
            self.latest_start_after_layover = self.last_end_period + 600 - 1440

            self.start_after_layover_activities = set()
            for activity in self.activities:
                if activity.start_period >= self.earliest_start_after_layover and activity.start_period <=self.latest_start_after_layover:
                    self.start_after_layover_activities.add(activity)

            self.connection_costs = [{} for i in range(self.number_of_activities)]
            self.connection_costs_reversed = [{} for i in range(self.number_of_activities)]

            for line in f.readlines():
                line = line.split()

                self.connection_costs[int(line[0])-1][int(line[1])-1]=int(line[2])
                self.connection_costs_reversed[int(line[1])-1][int(line[0])-1]=int(line[2])

    def get_work_activity_zero_indexed(self,index):
        return self.activities[index]

    def get_deadhead_activity_zero_indexed(self,index):
        work_activity = self.activities[index]
        return Activity(index, work_activity.start_period, work_activity.end_period, "deadhead")







# Cell
def get_activity_str(activity):
    work_time = 0
    if activity.is_work():
        work_time = activity.end_period - activity.start_period

        return f"[ID:{activity.index+1} S:{activity.start_period} WT:{work_time} E:{activity.end_period} ]"
    else:
        return f"(ID:{activity.index+1} S:{activity.start_period} WT:{work_time} E:{activity.end_period})"

# Cell

def get_activity_con_str(act_a, act_b, instance = None):

    cost_str = ""

    if instance:
        cost_str = f" C:{instance.connection_costs[act_a.index][act_b.index]}"

    if act_b.is_work():
        work_time = act_b.start_period - act_a.end_period
        return f" - WC WT:{work_time}{cost_str} - "
    return  f" - DC - "


# Cell

def get_duty_str(duty, instance = None):

    total_cost = 0



    output = "||  "
    total_work_time = 0
    last_activity = None

    for activity in duty:
        if activity.is_work:
            total_work_time += activity.get_number_of_periods()

            if last_activity:
                total_work_time += activity.start_period - last_activity.end_period

        if last_activity:

            if instance:
                total_cost += instance.connection_costs[last_activity.index][activity.index]

            output += get_activity_con_str(last_activity, activity, instance)


        output += get_activity_str(activity)
        last_activity = activity

    if instance:
        output += f" | Total: WT: {total_work_time} Cost: {total_cost} ||"
    else :
        output += f" | Total: WT: {total_work_time}  ||"

    return output




# Cell

def get_pairing_str(pairing, instance = None):

    output = ""
    last_duty = None
    for duty in pairing:

        if last_duty:
            output += f" --- Layover with time  {duty[0].start_period + 1440 - last_duty[-1].end_period}) ---  "

        last_duty = duty
        output += get_duty_str(duty, instance)

    return output



# Cell

def write_solution(instance, pairings, file_name = None):

    if file_name is None:
        file_name = instance.instance_name + "_sol.txt"

    with open(file_name,"w") as file:

        file.write (instance.instance_name + "\n")

        for pairing in pairings:
            line = ""
            for index, duty in enumerate(pairing):
                if index > 0:
                    line += "L "
                for activity in duty:
                        if activity.is_work():
                            line +=  str(activity.index+1) + " "
                        else:
                            line += str(activity.index+1) + "_D "

            file.write (line[:-1] + "\n")




# Cell
def read_solution(solution_file_name, instance_path = "."):

    pairings = []
    with open(solution_file_name) as f:

        instance_name = f.readline().rstrip()

        instance_file_name = instance_path + "/" + instance_name + ".txt"

        instance = csp_bc_instance(instance_file_name)

        for line in f.readlines():
            pairing = []
            duty = []
            for item in line.split():
                if item.isnumeric():
                    duty.append(instance.get_work_activity_zero_indexed(int(item)-1))

                elif item[-2:]=="_D":
                    duty.append(instance.get_deadhead_activity_zero_indexed(int(item[:-2])-1))

                elif item=="L":
                    pairing.append(duty)
                    duty = []

            pairing.append(duty)
            pairings.append(pairing)
    return pairings, instance

# Cell
def get_problem_variants():
    return ["base", "dh","dhl"]


# Cell
def get_n_activities_to_range_n_crews():
    range_crew_members = dict([
     ( 50, range( 27, 32)),
     (100, range( 44 ,49)),
     (150, range( 69, 74)),
     (200, range( 93, 98)),
     (250, range(108,113)),
     (300, range(129,134)),
     (350, range(144,149)),
     (400, range(159,164)),
     (450, range(182,187)),
     (500, range(204,209))])

    return range_crew_members

# Cell
def get_instance_and_range_crew_members(number_of_activities, instance_folder = "./../instances"):

    filename = f"{instance_folder}/csp{number_of_activities}.txt"
    get_n_activities_to_range_n_crews()


    return csp_bc_instance(filename), get_n_activities_to_range_n_crews()[number_of_activities]


# Cell

def get_dict_results_ds(number_of_activities, number_of_crew_members, instance_folder = "./instances"):
    filename =f"{instance_folder}/results_derigs_schaefer.csv"

    with open(filename, 'r') as data:

        for line in csv.DictReader(data,delimiter =";"):
            if int(line['number_act']) == number_of_activities and int(line['number_crew']) == number_of_crew_members:
                return line
    return None

# Cell

def get_obj_ds(number_of_activities, number_of_crew_members, variant, instance_folder = "./instances" ):

    dict_results_ds = get_dict_results_ds(number_of_activities, number_of_crew_members, instance_folder )
    if dict_results_ds is None:
        return -1

    return int(get_dict_results_ds(number_of_activities, number_of_crew_members,instance_folder)[f"{variant}_obj"])

# Cell
def claimed_optimal_ds(number_of_activities, number_of_crew_members, variant, instance_folder = "./instances"):

    dict_results_ds = get_dict_results_ds(number_of_activities, number_of_crew_members, instance_folder )
    if dict_results_ds is None:
        return -1

    return int(get_dict_results_ds(number_of_activities, number_of_crew_members, instance_folder)[f"{variant}_opt"]) > 0

# Cell
def check_duty(instance, duty):

    is_feasible = True

    total_period_span = duty[-1].end_period - duty[0].start_period
    total_cost = 0
    total_deadhead_periods = 0

    last_activity = None

    for activity in duty:
        if not activity.is_work():
            total_deadhead_periods += activity.end_period-activity.start_period

        if last_activity:

            if activity.index in instance.connection_costs[last_activity.index]:

                total_cost += instance.connection_costs[last_activity.index][activity.index]

                if not activity.is_work():
                    total_deadhead_periods += activity.start_period - last_activity.end_period
            else:
                is_feasible = False
                print("Infeasible Connection used from", last_activity, "to", activity, get_duty_str(duty))

        last_activity = activity

    total_work_time = total_period_span - total_deadhead_periods

    if total_work_time > instance.max_work_periods:
        is_feasible = False
        print("Violating max total work time", total_work_time, get_duty_str(duty))

    return is_feasible, total_cost


# Cell

def check_pairing(instance, pairing):

    total_cost = 0
    is_feasible = True
    if len(pairing) > 2:
        is_feasible = False
        print("More than 2 duties in pairing, namely",len(pairing), get_pairing_str(pairing))

    last_duty = None
    for duty in pairing:

        is_duty_feasible, duty_cost = check_duty(instance, duty)
        is_feasible = is_feasible and is_duty_feasible
        total_cost += duty_cost


        if last_duty is not None:

            if last_duty[-1].end_period <= 1200:
                is_feasible = False
                print("layover is only allowed to start after 1200, here: ", last_duty[-1].end_period , get_pairing_str(pairing))

            layover_connection_time = 1440 + duty[0].start_period - last_duty[-1].end_period
            if layover_connection_time < 480 or layover_connection_time > 600:
                is_feasible = False
                print("layover connection time is not within [480,600], but:", layover_connection_time, get_pairing_str(pairing))
        last_duty = duty

    return is_feasible, total_cost

# Cell

def check_pairings(instance, pairings, number_of_crew_members):

    total_cost = 0
    is_feasible = True

    if not len(pairings) ==  number_of_crew_members:
        is_feasible = False
        print ("Wrong number of pairings, namely", len(pairings), "and", number_of_crew_members, "crew members")

    for pairing in pairings:
        is_pairing_feasible, pairing_cost  = check_pairing(instance, pairing)
        is_feasible = is_feasible and is_pairing_feasible
        total_cost += pairing_cost

    return is_feasible, total_cost

# Cell
def get_number_of_layovers(pairings):
    number_of_layovers = 0
    for pairing in pairings:
        number_of_layovers += len(pairing)-1
    return number_of_layovers

def get_number_of_duties(pairings):
    number_of_duties= 0
    for pairing in pairings:
        number_of_duties += len(pairing)
    return number_of_duties

def get_number_of_duties_counting_single_duties_twice(pairings):
    number_of_duties= 0
    for pairing in pairings:
        if (len(pairing)) == 1:
            number_of_duties +=1
        number_of_duties += len(pairing)
    return number_of_duties

# Cell

def get_number_of_deadheads(duty):
    counter = 0
    for activity in duty:
        counter += not activity.is_work()
    return counter

def get_maximum_number_of_deadheads_per_duty(pairings):

    max_counter = 0
    for pairing in pairings:
        for duty in pairing:
            max_counter = max(max_counter, get_number_of_deadheads(duty))
    return max_counter


# Cell
def get_maximum_number_of_deadheads_in_sequence(duty):
    counter = 0
    max_counter = 0
    for activity in duty:
        if not activity.is_work():
            counter += 1
        else:
            max_counter = max(max_counter, counter)
            counter = 0

    return max(max_counter, counter)

def get_maximum_number_of_deadheads_in_sequence_per_duty(pairings):
    max_counter = 0
    for pairing in pairings:
        for duty in pairing:
            max_counter = max(max_counter, get_maximum_number_of_deadheads_in_sequence(duty))
    return max_counter

# Cell
def get_maximum_number_of_activities_per_duty(pairings):
    max_counter = 0
    for pairing in pairings:
        for duty in pairing:
            max_counter = max(max_counter, len(duty))
    return max_counter


# Cell
def get_number_of_work_activities(duty):
    counter = 0
    for activity in duty:
        counter += activity.is_work()
    return counter


def get_maximum_number_of_work_activities_per_duty(pairings):
    max_counter = 0
    for pairing in pairings:
        for duty in pairing:
            max_counter = max(max_counter, get_number_of_work_activities(duty))
    return max_counter

# Cell
def get_pairings_from_file(instance_folder, solution_folder, variant, n_activities, n_crews):
    solution_file_name = solution_folder + f"/csp{n_activities}_{variant}_cm{n_crews}_sol.txt"
    return read_solution(solution_file_name, instance_folder)




# Cell
def check_sol_from_file(instance_folder, solution_folder, variant, n_activities, n_crews):

    pairings, instance = get_pairings_from_file(instance_folder, solution_folder, variant, n_activities, n_crews)

    return check_pairings(instance, pairings, n_crews)