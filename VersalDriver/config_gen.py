from tvb_algo import data
from math import *
import random
import struct
import time

def get_model(model):
    if model == 'tvb76':
        return data.tvb76_weights_lengths()
    else:
        return data.tvb192_weights_lengths()


def config_gen(model, speed=4.0):

    W, D = get_model(model) #data.tvb76_weights_lengths()
    BIN_OUTPUT = True
    GEN_UNI_DELAY_DIST = False

    N = W.shape[0]
    # N = 10 # 473 works but not 474 at speed 40.0 / when connectivity sizes are 0, 475 works but 476 not working
    M = 2
    CC_E = 40
    CC_C = 1
    MLP_E = 32
    CMI = 1
    CMO = 0
    # speed = 4.0 # for 474 at speed below around 25 works !
    dt = 0.05
    tf = 150.0
    num_param = 7

    initial_states = [-1.0]*(N*M)

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

    cpe_min = floor(N/MLP_E)
    cpe_max = ceil(N/MLP_E)

    center_w_s = [cpe_min]*MLP_E
    cpe_max_no = N - cpe_min*MLP_E

    for i in range(cpe_max_no):
        center_w_s[i] = cpe_max

    random.shuffle(center_w_s)


    epc = int(MLP_E/CC_C)
    for c in range(CC_C):
        nnz[c] = 0
        d_max[c] = 0
        # i_start = sl_index[c][0] 
        # i_end = sl_index[c][1]
        i_start = sum(center_w_s[0:c*epc])
        i_end = sum(center_w_s[0:((c+1)*epc)])
        for i in range(i_start, i_end):
            t = []
            ti = []
            twi = []
            for j in range(N):
                # W[i][j] = 0.0
                if W[i][j] > 0:
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


    avg_d_u = []
    avg_d_d = []
    for c in range(CC_C):
        dm = d_max[c] + 1
        avg_d_u.append(ceil(dm/CC_E)) # balanced memory distribution among the engines
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
        # d_borders[c].append(d_borders[c][-1]+2)


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

                det.append(te)
                deti.append(tei)
                wet.append(wtei)
                npe[c][e-1] = npe[c][e-1] + len(te)

            de[c].append(det)
            dei[c].append(deti)
            we[c].append(wet)

    print("N:", N, "| M:", M, "| CC_C:", CC_C, "| CC_E:", CC_E)
    print("Maximum Delay: ", max(d_max))
    print("History Memory Requirement: ", 4 * max(avg_d_u) * N, " Bytes")
    print("Maximum Connectivity Memory Requirement: ", 4*(4*N + (3*max([max(p) for p in npe]))), " Bytes")
    # print("Total Connectivity Memory Requirement: ", 4*(N + (3*sum(npe))), " Bytes (" + str((4*(N + (3*sum(npe))))/CC_E) + ")")
    print("Total Memory Requirement: ", 4 * ((max(avg_d_u) * N) + (4*N + (3*max([max(p) for p in npe])))), " Bytes")
    print("Sparsity: ", 100*(sum(nnz)/(N**2)), '% (# of Calculations: ', sum(nnz), ")")
    print("Average Calculation per CC Engine: ", (sum(nnz)/(CC_E*CC_C)), " | Maximum Calculation per CC Engine: ", max([max(p) for p in npe]))



    #########################################################
    ########## GENERATING CONFIGURATION HEADER FILE #########

    fb = open("Data/config.bin", 'wb')
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

    for c in range(CC_C):
        n_range = sum(center_w_s[0:(c+1)*epc]) - sum(center_w_s[0:c*epc])
        for e in range(CC_E):
            b = 0
            for n in range(n_range):
                fb.write(struct.pack("f", float(b)))
                b = b + len(de[c][n][e])

            for n in range(n_range):
                for j in dei[c][n][e]:
                    fb.write(struct.pack("f", float(j)))

            for n in range(n_range):
                for j in de[c][n][e]:
                    fb.write(struct.pack("f", float(j)))

            for n in range(n_range):
                for j in range(len(we[c][n][e])):
                    fb.write(struct.pack("f", we[c][n][e][j]))


    fb.close()



