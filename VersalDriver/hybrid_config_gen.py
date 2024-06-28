from tvb_algo import data
from math import *
import random
import struct
import time
import numpy as np
import os

def get_model(model):
    if model == 'tvb76':
        return data.tvb76_weights_lengths()
    elif model == 'tvb192':
        return data.tvb192_weights_lengths()
    else:
        return data.tvb998_weights_lengths()


def hybrid_config_gen(model, speed=4.0):

    W, D = get_model(model) #data.tvb76_weights_lengths()
    H_OUTPUT = True
    BIN_OUTPUT = True
    WORKLOAD_DIST_MODE = 1


    MAX_HISTORY_MEM = 64000

    ################# SIMULATION PARAMETERS #################

    N = W.shape[0]
    # N = 600 # no working with 343 and 1 / 374 and 2 (when weights are zero or not)
    M = 2
    CC_E = 32
    CC_C = 1
    MLP_E = 64
    CMI = 1
    CMO = 0
    # speed = 10.0
    dt = 0.05
    tf = 3000 * dt #150.0
    num_param = 7

    initial_states = [-1.0]*(N*M)

    MLP_H = 1
    MLP_L = 64
    MLP_P = ((M+1)*MLP_L) + ((MLP_H-1)*(MLP_L+1)*MLP_L) + ((MLP_L+1)*M)

    #########################################################
    #################### PRE PROCESSING #####################

    D = ((D / dt)/speed).astype('i')
    d = [] # non-zero-weight delays
    di = [] # non-zero-weight delay indexes
    w = [] # non-zero weights
    dl = []
    nnz = [] # number of non-zero weights
    nnzc = []
    snzd = [] # sum of non-zero-weight delays
    d_max = []
    d_min = []
    for c in range(CC_C):
        d.append([])
        di.append([])
        w.append([])
        dl.append([])
        nnz.append(0)
        snzd.append(0)
        d_max.append(0)
        d_min.append(100000000)

    for i in range(N):
        nnzc.append(0)

    ####### Assigning Centers to MLPFE Engines #######

    cpe_min = floor(N/MLP_E)
    cpe_max = ceil(N/MLP_E)

    center_w_s = [cpe_min]*MLP_E
    cpe_max_no = N - cpe_min*MLP_E

    for i in range(cpe_max_no):
        center_w_s[i] = cpe_max

    # random.shuffle(center_w_s)

    ##################################################
    ##################################################
    ######## Calculating the CCEs Data ############### 

    epc = int(MLP_E/CC_C)
    for c in range(CC_C):
        nnz[c] = 0
        d_max[c] = 0
        i_start = sum(center_w_s[0:c*epc])
        i_end = sum(center_w_s[0:((c+1)*epc)])
        for i in range(i_start, i_end):
            t = []
            ti = []
            twi = []
            for j in range(N):
                # W[i][j] = 0.0
                if W[i][j] > 0:
                    # if D[i][j] < 400:# and D[i][j] < 352:
                    t.append(D[i][j])
                    ti.append(j)
                    twi.append(W[i][j])
                    dl[c].append(D[i][j])
                    nnz[c] = nnz[c] + 1
                    snzd[c] = snzd[c] + D[i][j]
                    if D[i][j] > d_max[c]:
                        d_max[c] = D[i][j]
                    if D[i][j] < d_min[c]:
                        d_min[c] = D[i][j]

            d[c].append(t)
            di[c].append(ti)
            w[c].append(twi)

    ####### History window ##########

    if WORKLOAD_DIST_MODE == 0: ## Equal delay windows for everyone
        avg_d_u = []
        avg_d_d = []
        for c in range(CC_C):
            dm = d_max[c] + 1
            avg_d_u.append(ceil(dm/CC_E))
            avg_d_d.append(floor(dm/CC_E))

        db = 0
        d_borders = []
        for c in range(CC_C):
            db = 0
            dbl = [db]
            dm = d_max[c] + 1
            for i in range(1,CC_E):
                if i < (dm%CC_E):
                    db += (avg_d_u[c])
                else:
                    db += (avg_d_d[c])
                dbl.append(db)
            d_borders.append(dbl)

        for c in range(CC_C):
            d_borders[c].append(max(d_borders[c][-1] + avg_d_u[c], d_max[c]+1))

    elif WORKLOAD_DIST_MODE == 1: # Trying equal workload without crossing delay boundries
        
        delay_hist = []
        d_borders = []
        avg_d_u = []
        for c in range(CC_C):
            delay_hist.append({})

            for i in dl[c]:
                if i in delay_hist[c].keys():
                    delay_hist[c][i] += 1
                else:
                    delay_hist[c][i] = 1

            delay_hist[c] = dict(sorted(delay_hist[c].items()))
            dkey = list(delay_hist[c].keys())
            dval = list(delay_hist[c].values())

            
            d_borders.append([0])
            avg_cpe = floor(nnz[c]/CC_E)
            e_index = 0
            cpe = 0
            for i in range(d_max[c]):
                if i in dkey:
                    index = dkey.index(i)
                    cpe += dval[index]
                    if cpe > avg_cpe:
                        try:
                            d_borders[c].append(dkey[index+1])
                        except:
                            d_borders[c].append(d_max[c]+1)
                        cpe = 0
                        e_index += 1

            # if len(d_borders[c]) == CC_E:
            #     d_borders[c].appedn(d_max[c]+1)
            
            if not (len(d_borders[c]) == (CC_E+1)):
                avg_d_left = ceil((d_max[c]+1-d_borders[c][-1])/(CC_E + 1 - len(d_borders[c])))
                for i in range(CC_E + 1 - len(d_borders[c])):
                    d_borders[c].append(d_borders[c][-1]+avg_d_left)

            avg_d_u.append(0)
            max_hw_possible = int(MAX_HISTORY_MEM / N)
            for i in range(1, len(d_borders[c])):
                if (d_borders[c][i] - d_borders[c][i-1]) > avg_d_u[c]:
                    avg_d_u[c] = (d_borders[c][i] - d_borders[c][i-1])


    #################################


    de = [] # delays for each engine 
    dei = [] # delay indexed for each engine
    we = [] # weights for each engine
    npe = [] # number of delay points/calculations per engine
    for i in range(CC_C):
        de.append([])
        dei.append([])
        we.append([])
        npe.append([])
        for j in range(CC_E):
            npe[i].append(0)


    for c in range(CC_C):
        for i in range(len(d[c])):
            det = []
            deti = []
            wet = []
            for e in range(1, len(d_borders[c])):
                te = []
                tei = []
                wtei = []
                for j in range(len(d[c][i])):
                    try:
                        if (d[c][i][j] >= d_borders[c][e-1]) and (d[c][i][j] < d_borders[c][e]):
                            te.append(d[c][i][j])
                            tei.append(di[c][i][j])
                            wtei.append(w[c][i][j])

                    except:
                        if (d[c][i][j] >= d_borders[c][e-1]):
                            te.append(d[c][i][j])
                            tei.append(di[c][i][j])
                            wtei.append(w[c][i][j])

                if(len(te) == 0):
                    te.append(max(int(tf / dt), d_max[c] + 1))
                    tei.append(0)
                    wtei.append(0.0)

                det.append(te)
                deti.append(tei)
                wet.append(wtei)
                npe[c][e-1] = npe[c][e-1] + len(te)

            de[c].append(det)
            dei[c].append(deti)
            we[c].append(wet)


    print("N:", N, "| M:", M, "| CC_C:", CC_C, "| CC_E:", CC_E)
    print("MLP Hidden Layers:", MLP_H, "| MLP Neurons/Layer:", MLP_L, "| Number of Paramters:", MLP_P)
    print("Maximum Delay (For Each CCE Chain): ", d_max,)
    print("History Memory Requirement: ", 4 * max(avg_d_u) * N, " Bytes", "(", max(avg_d_u) * N, "Words )")
    print("Maximum Connectivity Memory Requirement: ", 4*(2*N + (3*max([max(p) for p in npe]))), " Bytes", "(", (2*N + (3*max([max(p) for p in npe]))), "Words )")
    print("Total Memory Requirement: ", 4 * ((max(avg_d_u) * N) + (4*N + (3*max([max(p) for p in npe])))), " Bytes")
    print("Sparsity: ", 100*(sum(nnz)/(N**2)), '% (# of Calculations: ', sum(nnz), ")")
    print("Average Calculation per CC Engine: ", (sum(nnz)/(CC_E*CC_C)), " | Maximum Calculation per CC Engine: ", max([max(p) for p in npe]), "@ CCE", np.argmax(npe[np.argmax([max(p) for p in npe])]))


    #########################################################
    ########## GENERATING CONFIGURATION HEADER FILE #########

    if(H_OUTPUT):
        f = open("Data/config_hybrid.h", 'w')
        f.write("/* NMM CONFIGURATION HEADER FILE */\n\n")

        f.write("/* Device Information */\n")
        f.write("#define CC_E\t\t" + str(CC_E) + '\n')
        f.write("#define CC_C\t\t" + str(CC_C) + '\n')
        f.write("#define MLP_E\t\t" + str(MLP_E) + '\n')
        f.write("/* Device Information */\n\n\n")

        f.write("/* Simulation Parameters */\n")
        f.write("#define NMM_N\t\t" + str(N) + '\n')
        f.write("#define NMM_M\t\t" + str(M) + '\n')
        f.write("#define NMM_CMI\t\t" + str(CMI) + '\n')
        f.write("#define NMM_CMO\t\t" + str(CMO) + '\n')
        f.write("#define NMM_SP\t\t" + str(speed) + 'f\n')
        f.write("#define NMM_SP_H\t" + str(hex(struct.unpack('<I', struct.pack('<f', speed))[0])) + '\n')
        f.write("#define NMM_dt\t\t" + str(dt) + 'f\n')
        f.write("#define NMM_dt_H\t" + str(hex(struct.unpack('<I', struct.pack('<f', dt))[0])) + '\n')
        f.write("#define NMM_tf\t\t" + str(int(tf/dt)) + '\n\n')
        f.write("#define NUM_PAR\t\t" + str(num_param) + '\n')
        f.write("const int32 sim_param[NUM_PAR] = {NMM_N, NMM_M, NMM_CMI, NMM_CMO, NMM_SP_H, NMM_dt_H, NMM_tf};\n")
        f.write("/* Simulation Parameters */\n\n\n")

        f.write("/* Initial States */\n")
        f.write("const float init_states[NMM_N*NMM_M] = {\n")
        for i in range(len(initial_states)):
            if not (i == (len(initial_states)-1)):
                f.write(str(initial_states[i]) + ',\n')
            else:
                f.write(str(initial_states[i]) + '\n};\n')
        f.write("/* Initial States */\n\n\n")

        f.write("/* Engine Data */\n")
        f.write("#define ENGINE_DATA_SIZE\t\t" + str((N*CC_E) + (3*sum([sum(p) for p in npe]))) + '\n\n')

        f.write("const int32 connectivity_size[CC_C][CC_E] = {")
        f.write(str(npe)[1:-1].replace('[', '\n{').replace(']', '}') + '\n};\n\n')


        f.write("const int32 history_window[CC_C][CC_E][7] = {\n")
        # d_borders.append(d_max)
        h4 = 0
        for c in range(CC_C):
            f.write("\t{\n")
            for i in range(len(d_borders[c])-1): 
                f.write("\t\t{" + str(d_borders[c][i]) + ", " + str(d_borders[c][i+1]) + ", " + str(i) + ", " + str(h4) + ", " + str((N*CC_E) + (3*sum([sum(p) for p in npe]))) + ', ' + str(sum(center_w_s[0:c*epc])) + ', ' + str(sum(center_w_s[0:(c+1)*epc])) + "},\n")
                # f.write("\t\t{" + str(d_borders[c][i]) + ", " + str(d_borders[c][i+1]) + ", " + str(i) + ", " + str(h4) + ", " + str((N*CC_E) + (3*sum([sum(p) for p in npe]))) + ', ' + str(sum(center_w_s[0:sl_index[c][0]])) + ', ' + str(sum(center_w_s[0:sl_index[c][1]])) + "},\n")

                h4 += (sum(center_w_s[0:(c+1)*epc]) - sum(center_w_s[0:c*epc]))
                # h4 += (sum(center_w_s[0:sl_index[c][1]]) - sum(center_w_s[0:sl_index[c][0]]))
                h4 += 3*npe[c][i]
            
            f.write("\t},\n")
        
        f.write("};\n\n")

        f.write("const int32 center_window[MLP_E][5] = {\n")
        ind = 0
        for i in range(MLP_E):
            f.write("{" + str(ind) + ", " + str(ind+center_w_s[i]) + ", " + str(i) + ', ' + str(sum(center_w_s[0:int(i/epc)*epc])) + ', ' + str(sum(center_w_s[0:(int(i/epc)+1)*epc])) +  "},\n")
            
            ind = ind + center_w_s[i]

        f.write("};\n\n")

        f.write("const float en_data[ENGINE_DATA_SIZE] = {\n")

        count = 0
        for c in range(CC_C):
            n_range = sum(center_w_s[0:(c+1)*epc]) - sum(center_w_s[0:c*epc])
            for e in range(CC_E):
                b = 0
                for n in range(n_range):
                    if(count == (((N*CC_E) + (3*sum([sum(p) for p in npe]))) - 1)):
                        f.write(str(b) + "\n};")
                        b = b + len(de[c][n][e])
                        count += 1
                    else:
                        f.write(str(b) + ",\n")
                        b = b + len(de[c][n][e])
                        count += 1

                for n in range(n_range):
                    for j in dei[c][n][e]:
                        f.write(str(j) + ",\n")
                        count += 1

                for n in range(n_range):
                    for j in de[c][n][e]:
                        f.write(str(j) + ",\n")
                        count += 1

                for n in range(n_range):
                    for j in range(len(we[c][n][e])):
                        if(count == (((N*CC_E) + (3*sum([sum(p) for p in npe]))) - 1)):
                            f.write(str(we[c][n][e][j]) + "\n};")
                        else:
                            f.write(str(we[c][n][e][j]) + ",\n")
                            count += 1

        f.close()

    if(BIN_OUTPUT):
        fb = open("Data/config_hybrid.bin", 'wb')
        fb.write(struct.pack("i", 0x12345678))
        fb.write(struct.pack("i", CC_E))
        fb.write(struct.pack("i", CC_C))
        fb.write(struct.pack("i", MLP_E))
        fb.write(struct.pack("i", N))
        fb.write(struct.pack("i", M))
        fb.write(struct.pack("i", CMI))
        fb.write(struct.pack("i", CMO))
        fb.write(struct.pack("f", speed))
        fb.write(struct.pack("i", struct.unpack('<I', struct.pack('<f', speed))[0]))
        fb.write(struct.pack("f", dt))
        fb.write(struct.pack("i", struct.unpack('<I', struct.pack('<f', dt))[0]))
        fb.write(struct.pack("i", int(tf/dt)))
        fb.write(struct.pack("i", num_param))

        for i in range(N*M):
            fb.write(struct.pack("f", initial_states[i]))

        fb.write(struct.pack("i", ((N*CC_E) + (3*sum([sum(p) for p in npe])))))

        for c in range(CC_C):
            for i in range(CC_E):
                fb.write(struct.pack("i", npe[c][i]))
        

        h4 = 0
        for c in range(CC_C):
            for i in range(len(d_borders[c])-1):
                fb.write(struct.pack("i", d_borders[c][i]))
                fb.write(struct.pack("i", d_borders[c][i+1]))
                fb.write(struct.pack("i", i))
                fb.write(struct.pack("i", h4))
                fb.write(struct.pack("i", ((N*CC_E) + (3*sum([sum(p) for p in npe])))))
                fb.write(struct.pack("i", sum(center_w_s[0:c*epc])))
                fb.write(struct.pack("i", sum(center_w_s[0:(c+1)*epc])))

                h4 += (sum(center_w_s[0:(c+1)*epc]) - sum(center_w_s[0:c*epc]))
                h4 += 3*npe[c][i]

        
        ind = 0
        for i in range(MLP_E):
            fb.write(struct.pack("i", ind))
            fb.write(struct.pack("i", ind + center_w_s[i]))
            fb.write(struct.pack("i", i))
            fb.write(struct.pack("i", sum(center_w_s[0:int(i/epc)*epc])))
            fb.write(struct.pack("i", sum(center_w_s[0:(int(i/epc)+1)*epc])))
            

            ind = ind + center_w_s[i]

        count = 0
        for c in range(CC_C):
            n_range = sum(center_w_s[0:(c+1)*epc]) - sum(center_w_s[0:c*epc])
            for e in range(CC_E):
                b = 0
                for n in range(n_range):
                    fb.write(struct.pack("i", b))
                    count = count + 1
                    b = b + len(de[c][n][e])

                for n in range(n_range):
                    for j in dei[c][n][e]:
                        fb.write(struct.pack("i", j))
                        count = count + 1

                for n in range(n_range):
                    for j in de[c][n][e]:
                        fb.write(struct.pack("i", j))
                        count = count + 1

                for n in range(n_range):
                    for j in range(len(we[c][n][e])):
                        fb.write(struct.pack("f", we[c][n][e][j]))
                        count = count + 1

        fb.write(struct.pack("i", MLP_H))
        fb.write(struct.pack("i", MLP_L))
        fb.write(struct.pack("i", MLP_P))

        fp = open("params.txt", 'r')
        for i in range(MLP_P):
            p = fp.readline()
            fb.write(struct.pack("f", float(p)))

        fp.close()
        fb.close()

        write_size = int(os.path.getsize("Data/config_hybrid.bin")/4)
        
        fb = open("Data/config_hybrid.bin", 'ab')

        fb.write(struct.pack("i", write_size))

        for _ in range(2):
            fb.write(struct.pack("i", CC_E))
            fb.write(struct.pack("i", CC_C))
            fb.write(struct.pack("i", MLP_E))
            fb.write(struct.pack("i", N))
            fb.write(struct.pack("i", M))
            fb.write(struct.pack("i", CMI))
            fb.write(struct.pack("i", CMO))
            fb.write(struct.pack("f", speed))
            fb.write(struct.pack("i", struct.unpack('<I', struct.pack('<f', speed))[0]))
            fb.write(struct.pack("f", dt))
            fb.write(struct.pack("i", struct.unpack('<I', struct.pack('<f', dt))[0]))
            fb.write(struct.pack("i", int(tf/dt)))
            fb.write(struct.pack("i", num_param))

            for i in range(N*M):
                fb.write(struct.pack("f", initial_states[i]))

            fb.write(struct.pack("i", ((N*CC_E) + (3*sum([sum(p) for p in npe])))))

            for c in range(CC_C):
                for i in range(CC_E):
                    fb.write(struct.pack("i", npe[c][i]))
            

            h4 = 0
            for c in range(CC_C):
                for i in range(len(d_borders[c])-1):
                    fb.write(struct.pack("i", d_borders[c][i]))
                    fb.write(struct.pack("i", d_borders[c][i+1]))
                    fb.write(struct.pack("i", i))
                    fb.write(struct.pack("i", h4))
                    fb.write(struct.pack("i", ((N*CC_E) + (3*sum([sum(p) for p in npe])))))
                    fb.write(struct.pack("i", sum(center_w_s[0:c*epc])))
                    fb.write(struct.pack("i", sum(center_w_s[0:(c+1)*epc])))

                    h4 += (sum(center_w_s[0:(c+1)*epc]) - sum(center_w_s[0:c*epc]))
                    h4 += 3*npe[c][i]

            
            ind = 0
            for i in range(MLP_E):
                fb.write(struct.pack("i", ind))
                fb.write(struct.pack("i", ind + center_w_s[i]))
                fb.write(struct.pack("i", i))
                fb.write(struct.pack("i", sum(center_w_s[0:int(i/epc)*epc])))
                fb.write(struct.pack("i", sum(center_w_s[0:(int(i/epc)+1)*epc])))
                

                ind = ind + center_w_s[i]

            count = 0
            for c in range(CC_C):
                n_range = sum(center_w_s[0:(c+1)*epc]) - sum(center_w_s[0:c*epc])
                for e in range(CC_E):
                    b = 0
                    for n in range(n_range):
                        fb.write(struct.pack("i", b))
                        count = count + 1
                        b = b + len(de[c][n][e])

                    for n in range(n_range):
                        for j in dei[c][n][e]:
                            fb.write(struct.pack("i", j))
                            count = count + 1

                    for n in range(n_range):
                        for j in de[c][n][e]:
                            fb.write(struct.pack("i", j))
                            count = count + 1

                    for n in range(n_range):
                        for j in range(len(we[c][n][e])):
                            fb.write(struct.pack("f", we[c][n][e][j]))
                            count = count + 1

            fb.write(struct.pack("i", MLP_H))
            fb.write(struct.pack("i", MLP_L))
            fb.write(struct.pack("i", MLP_P))

            fp = open("params.txt", 'r')
            for i in range(MLP_P):
                p = fp.readline()
                fb.write(struct.pack("f", float(p)))

            fp.close()
        
        
        fb.close()

        print("Finished writing the config .bin file. size: ", os.path.getsize("Data/config_hybrid.bin"), "Bytes / ", write_size, "Values")



