import time
import cProfile
import glob
import os
import re
import fileinput
import pstats
import io
import csv 
from io import StringIO
import operator
from operator import itemgetter
import math



num_vault = 32
num_layer = 1
##num_row = math.pow(2,(32 - (6 + 5 + 2 + 2)))
num_row = 8192


num_bank = 4
req_queue_length = 16

time_vault = 0
time_layer = 1
time_row = 40
time_bank = 2
time_col = 4
initial_latency = 40

s = math.ceil(time_row/(num_layer*(num_bank - 1)*time_layer))
y = int(math.pow(2,math.ceil(math.log(s,2))))

block_size = 256

num_col = 256
expanded_req_queue_length = req_queue_length*block_size


class bank(object):
    def __init__(self):
        self.row = num_row
        self.col = num_col
        self.last_row = 0
        self.time = []
        self.bank_index = 0
        self.last_access_time = 0
        self.instr_count = 0
        self.window_count = 0

class layer(bank):
    def __init__(self):
        self.bank_objs = [bank() for i in range (num_bank)]
        self.last_bank = 0
        self.time = []
        self.layer_index = 0

class req_queue:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

class vault(layer, req_queue):
    def __init__(self):
        self.layer_objs = [layer() for i in range (num_layer)]
        self.req_queue_obj = req_queue()        
        self.time = []
        self.last_layer = 0
        self.vault_index = 0
        self.window_count = 0

class mem(vault):
    def __init__(self):
        self.vault_objs = [vault() for i in range (num_vault)]
        self.last_vault = 0

def reorder_function(queue_obj, field):
    queue_item = []
    curr_req_list = []
    while(int(queue_obj.is_empty()) == 0):
        queue_item = queue_obj.dequeue()
        curr_req_list.append(queue_item)
        queue_item = []


    if(field == 'vault'):
        curr_req_list.sort(key = operator.itemgetter(2))

    elif(field == 'layer'):
        curr_req_list.sort(key = operator.itemgetter(2,3))

    elif(field == 'bank'):
        curr_req_list.sort(key = operator.itemgetter(2,3,4))

    elif(field == 'row'):
        curr_req_list.sort(key = operator.itemgetter(2,3,4,5))

    elif(field == 'last_row_reorder'):
        curr_req_list.sort(key = operator.itemgetter(2,3,4,7))

    elif(field == 'row_time'):
        curr_req_list.sort(key = operator.itemgetter(2,3,4,8))

    elif(field == 'bank_time'):
        curr_req_list.sort(key = operator.itemgetter(2,3,8))

    elif(field == 'layer_time'):
        curr_req_list.sort(key = operator.itemgetter(2,8))

    elif(field == 'vault_time'):
        curr_req_list.sort(key = operator.itemgetter(8))
    
    for item in curr_req_list:
        queue_obj.enqueue(item)


def merge_bank_time_to_layer_time(bank_time, m):
    result = []
    i = j = 0
    total = len(l) + len(m)
    while len(result) != total:
        if len(l) == i:
            result += m[j:]
            break
        elif len(m) == j:
            result += l[i:]
            break
        elif l[i] < m[j]:
            result.append(l[i])
            i += 1
        else:
            result.append(m[j])
            j += 1
    
hmc = mem()

p = 0
q = 0
r = 0
for i in hmc.vault_objs:
    i.vault_index = int(p)
    for j in i.layer_objs:
        j.layer_index = int(q)
        for k in j.bank_objs:
            k.bank_index = int(r)
            r = r + 1
        r = 0
        q = q + 1
    q = 0
    p = p + 1
p = 0



time = 0
count = 0
address_list = []
temp_address_list = []
latency = []
time_vault = []
full_latency = []
expanded_address_list = []


with open("instruction/access_pattern.txt") as infile:
    for line in infile:
        if not line == '\n':
            line.strip()

            
            temp = (line.split('  '))

            for i in temp:
                
                if (i.split('  ', 1)[0]) and (i.split('  ', 1)[0] != '\n'):
                    temp_address_list.append(i.split('  ', 1)[0])

            address_list.append(temp_address_list)
            temp_address_list = []




##for item in address_list:
##    col_start_address = int(item[6].strip())*block_size
##    item[6] = str(col_start_address) + '\n'
##    new_col_address = col_start_address
##    for i in range(block_size):
##        new_col_address = col_start_address + int(i)
##        item[6] = str(new_col_address) + '\n'
##
##        temp = []
##        for j in item:
##            temp.append(j)
##        expanded_address_list.append(temp)        



##with open("E:/google_drive/usc_studies/phd/3d_memory_block_simulator/results/test_expand_baseline.txt", 'w') as outfile:
##    for i in expanded_address_list:
####        print(i)
##        outfile.write(str(i))
##        outfile.write('\n')
    

final_time = 30

for item in address_list:
    address_vault = int(item[2].strip())
    
    for i in hmc.vault_objs:
        if(address_vault == int(i.vault_index)):
            if(i.req_queue_obj.size() < (req_queue_length)):
                i.req_queue_obj.enqueue(item)

            else:
                
                reorder_function(i.req_queue_obj, 'layer')
                reorder_function(i.req_queue_obj, 'bank')
                reorder_function(i.req_queue_obj, 'row')

                temp_item = []
                curr_req_list = []
                while(int(i.req_queue_obj.is_empty()) == 0):
                    temp_item = i.req_queue_obj.dequeue()
                    address_layer = int(temp_item[3].strip())
                    address_bank = int(temp_item[4].strip())
                    address_row= int(temp_item[5].strip())

                    for dummy_layer in i.layer_objs:
                        if(address_layer == (dummy_layer.layer_index)):                            
                            for dummy_bank in dummy_layer.bank_objs:
                                if(address_bank == (dummy_bank.bank_index)):
                                    last_row = dummy_bank.last_row
                    
                    temp_item.append(~(last_row == address_row))
                    curr_req_list.append(temp_item)
                    temp_item = []

                for temp_item in curr_req_list:
                    i.req_queue_obj.enqueue(temp_item)

                reorder_function(i.req_queue_obj, 'last_row_reorder')
                
                curr_req_list = []

                while(int(i.req_queue_obj.is_empty()) == 0):
                    queue_item = i.req_queue_obj.dequeue()
                    address_layer = int(queue_item[3].strip())
                    address_bank = int(queue_item[4].strip())
                    address_row= int(queue_item[5].strip())
                    address_col = int(queue_item[6].strip())
                    address_time = int(queue_item[1].strip())

                    bank_time = 0
                    last_row = 0

                    for element in range(block_size):
                                   
                        for j in i.layer_objs:
                            if(int(address_layer) == int(j.layer_index)):                            
                                for k in j.bank_objs:
                                    if(int(address_bank) == int(k.bank_index)):
                                        if(int(k.instr_count) != 0):
                                            if(int(address_row) == int(k.last_row)):
                                                
                                                k.time.append(k.time[-1] + time_col)
                                                k.last_access_time = k.time[-1]
                                                bank_time = k.last_access_time

                                            else:
                                                k.last_row = address_row                                            
                                                k.time.append(k.time[-1] + time_row)
                                                k.last_access_time = k.time[-1]
                                                bank_time = k.last_access_time                                            

                                        else:

                                            if(i.window_count == 0):
                                                k.last_row = address_row
                                                k.time = []
                                                k.time.append(initial_latency)
                                                k.last_access_time = k.time[-1]
                                                bank_time = k.last_access_time

                                            else:

                                                if(int(address_row) == int(k.last_row)):
                                                    temp_time = max((final_time + time_layer), (k.last_access_time + time_col))
                                                    k.time = []
                                                    k.time.append(temp_time)
                                                    k.last_access_time = k.time[-1]
                                                    bank_time = k.last_access_time

                                                else:

                                                    k.last_row = address_row
                                                    # print(item)
                                                    temp_time = max((final_time + time_layer), (k.last_access_time + time_row))
                                                    k.time = []
                                                    k.time.append(temp_time)
                                                    k.last_access_time = k.time[-1]
                                                    bank_time = k.last_access_time
                                            

                                        

                                    
                                        k.instr_count = k.instr_count + 1
##                                        k.window_count = k.window_count + 1

                    queue_item.append(bank_time)
##                    queue_item.append(last_row_matches)
                    
                    curr_req_list.append(queue_item)





                for dummy_layer in i.layer_objs:
                    for dummy_bank in dummy_layer.bank_objs:
                        if(len(dummy_bank.time) == 1):
                            if(dummy_bank.time[-1] < final_time):
                                dummy_bank.time = []
                        else:
                            dummy_layer.time = dummy_bank.time + dummy_layer.time

                        dummy_layer.time.sort()

                for dummy_layer in i.layer_objs:
                    count = 0
                    for dummy_item in range(len(dummy_layer.time)):
                        if(count != 0):
                            if(dummy_layer.time[dummy_item] <= prev_time):
                                 dummy_layer.time[dummy_item] = prev_time + time_bank

                        prev_time = dummy_layer.time[dummy_item]
                        count = count + 1

##                for dummy_layer in i.layer_objs:
##                    print(dummy_layer.time)                
                

                for dummy_layer in i.layer_objs:
                    i.time = dummy_layer.time + i.time
                i.time.sort()

                for dummy_layer in i.layer_objs:
                    count = 0
                    for dummy_item in range(len(i.time)):
                        if(count != 0):
                            if(i.time[dummy_item] <= prev_time):
##                                print(dummy_item)
                                 i.time[dummy_item] = prev_time + time_layer
##                                print(dummy_item)

                        prev_time = i.time[dummy_item]
                        count = count + 1

##                print((i.time))
##                for temp in range((0), len(i.time), block_size):
##                    print(temp)





                    
                


##                all_vault_time = ''
##                for dummy in hmc.vault_objs:
##                    all_vault_time = all_vault_time + str(dummy.time) + '_'

                instr_index = block_size - 1
                print((i.time))
                for temp_item in curr_req_list:
                    latency.append(str(temp_item[1]) + '  ' + str(temp_item[2]) + '  ' + str(temp_item[3]) + '  ' + str(temp_item[4]) + '  ' + str(temp_item[5]) + '  ' + str(temp_item[6]) + '  ' + str(i.time[instr_index]) + '\n')
                    instr_index = instr_index + block_size

##                for temp in i.time:
##                    full_latency.append(str(temp))
##                    full_latency.append('\n')
                   
                for dummy_layer in i.layer_objs:
                    dummy_layer.time = []
                    for dummy_bank in dummy_layer.bank_objs:
                        if(len(dummy_bank.time) != 0):

                            # temp = max((i.time[-1]), dummy_bank.time[-1] + time_row)
                            temp = dummy_bank.time[-1]
                            dummy_bank.time = []
                            dummy_bank.time.append(temp)
                        # else:
                        #     dummy_bank.time.append((i.time[-1]))
                        dummy_bank.instr_count = 0

##                print(i.time[-1])

                final_time = i.time[-1]
                i. time = []
                i.req_queue_obj.enqueue(item)  
                i.window_count = i.window_count + 1
                


##                print(i.time)
                

                

##print(latency[-1])

temp = []
temp_address_list = []
sorted_latency = []
for item in latency:
    if not item == '\n':
        item.strip()

        temp = (item.split('  '))

        for i in temp:
            
            if (i.split('  ', 1)[0]) and (i.split('  ', 1)[0] != '\n'):
                temp_address_list.append(str(int(i.split('  ', 1)[0])))
        sorted_latency.append(temp_address_list)
        temp_address_list = []




sorted_latency.sort(key=lambda x: int(x[6]))


print(sorted_latency[-1])

with open("results/latency.txt", 'w') as outfile:
    for item in sorted_latency:
        outfile.write(str(item[0]) + '  ' + str(item[1]) + '  ' + str(item[2]) + '  ' + str(item[3]) + '  ' + str(item[4]) + '  ' + str(item[5]) + '  ' + str(item[6]) + '\n')
        
##with open("E:/google_drive/usc_studies/phd/scratchpad_memory_simulator/results/full_latency_baseline.txt", 'w') as outfile:
##    for item in full_latency:
##        outfile.write(item)
        
