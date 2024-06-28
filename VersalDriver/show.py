import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import struct
import numpy as np



def show_h(N, M, tf, CMO, dt, tN=-1):

    f = open('Output/output_h.bin', 'rb')
    fc = f.read()
    f.close()

    X = np.zeros((tf, N))

    for n in range(N):
        X[0, n] = -1.0

    format_str = str(N*M*tf) + 'f'
    fc = struct.unpack(format_str, fc)

    fi = CMO
    for t in range(1, tf):
        for n in range(N):
            X[t, n] = fc[fi]
            fi = fi + M

    t = np.arange(0, tf, 1)

    if tN == -1:
        plt.plot(t[::5] * dt , X[::5, :], 'k', alpha=0.3)
    else:
        plt.plot(t[::5] * dt , X[::5, tN], 'k', alpha=1.0)
    plt.grid(True, axis='x')
    plt.xlim([0, t[-1] * dt])
    plt.savefig("Output/output_h.png")
    plt.close()

def show_a(N, M, tf, CMO, dt, tN=-1):
    f = open('Output/output_a.bin', 'rb')
    fc = f.read()
    f.close()

    X = np.zeros((tf, N))

    for n in range(N):
        X[0, n] = -1.0

    format_str_i = str(((N*M) + 32)*tf) + 'i'
    fc_i = struct.unpack(format_str_i, fc)
    format_str_f = str(((N*M) + 32)*tf) + 'f'
    fc_f = struct.unpack(format_str_f, fc)

    fc_f_index = []
    fd = {}
    for i in range(len(fc_i)):
        if (fc_i[i] >= 0) and (fc_i[i] <= 32):
            fc_f_index.append(i)
            fd[fc_i[i]] = []
    fc_f_index.append(len(fc_i))

    for (i_start, i_end) in zip(fc_f_index[:-1], fc_f_index[1:]):
        fd[fc_i[i_start]].append(fc_f[(i_start+1):i_end])
    
    fc = []
    for t in range(tf):
        for i in range(32):
            for v in fd[i][t]:
                fc.append(v)

    fi = CMO
    for t in range(1, tf):
        for n in range(N):
            X[t, n] = fc[fi]
            fi = fi + M

    t = np.arange(0, tf, 1)

    if tN == -1:
        plt.plot(t[::5] * dt , X[::5, :], 'k', alpha=0.3)
    else:
        plt.plot(t[::5] * dt , X[::5, tN], 'k', alpha=1.0)
    plt.grid(True, axis='x')
    plt.xlim([0, t[-1] * dt])
    plt.savefig("Output/output_a.png")
    plt.close()

