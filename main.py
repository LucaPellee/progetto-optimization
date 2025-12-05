import random
import time

from mip import *

#random.seed(7)

# Funzione per calcolo Total Tardiness
def calcolaTotalTardiness(seq, pTimes, dueDates):

    numJobs = len(seq)
    numMachines = len(pTimes[0])

    # Creo la matrice dei completion time piena di 0
    C = []
    for m in range(numJobs):
        row = []
        for j in range(numMachines):
            row.append(0)
        C.append(row)

    C[0][0] = pTimes[seq[0]][0]  # il primo elemento della matrice è il pTime del job in posizione 0

    # Popolo la prima colonna
    for i in range(1, numJobs):
        C[i][0] = C[i-1][0] + pTimes[seq[i]][0]

    # Popolo la prima riga
    for j in range(1, numMachines):
        C[0][j] = C[0][j-1] + pTimes[seq[0]][j]

    # Riempio l'intera matrice
    for i in range(1, numJobs):
        for j in range(1, numMachines):
            C[i][j] = max(C[i-1][j], C[i][j-1]) + pTimes[seq[i]][j]

    t = [0] * numJobs  # vettore delle tardiness per ogni job

    tTot = 0  # Total Tardiness

    # Calcolo la tardiness per ogni job e le sommo ottenendo tTot
    for i in range(numJobs):
        t[i] = max(0, C[i][numMachines-1] - dueDates[seq[i]])
        tTot += t[i]

    return tTot



# Modello MIP
def ModelloMIP(pTimes,dueDates):

    numJobs = len(pTimes)
    numMachines = len(pTimes[0])
    numPos = numJobs
    model = mip.Model(sense=MINIMIZE, solver_name='CBC')
    x = [[model.add_var(var_type=BINARY) for j in range(numPos)] for i in range(numJobs)]
    C = [[model.add_var(var_type=CONTINUOUS, lb=0.0) for m in range(numMachines)] for j in range(numPos)]
    T = [model.add_var(var_type=CONTINUOUS, lb=0.0) for j in range(numPos)]

    for i in range(numJobs):
        model += xsum(x[i][j] for j in range(numPos)) == 1

    for j in range(numPos):
        model += xsum(x[i][j] for i in range(numJobs)) == 1

    model += C[0][0] == xsum(pTimes[i][0] * x[i][0] for i in range(numJobs))

    for m in range(1, numMachines):
        model += C[0][m] == C[0][m-1] + xsum(pTimes[i][m] * x[i][0] for i in range(numJobs))

    for j in range(1, numPos):
        model += C[j][0] == C[j-1][0] + xsum(pTimes[i][0] * x[i][j] for i in range(numJobs))

    for m in range(1, numMachines):
        for j in range(1, numPos):
            model += C[j][m] >= C[j-1][m] + xsum(pTimes[i][m] * x[i][j] for i in range(numJobs))
            model += C[j][m] >= C[j][m-1] + xsum(pTimes[i][m] * x[i][j] for i in range(numJobs))

    for j in range(numPos):
        model += T[j] >= C[j][numMachines-1] - xsum(dueDates[i] * x[i][j] for i in range(numJobs))

    model.objective = xsum(T[j] for j in range(numPos))
    model.verbose = 0
    model.optimize(max_seconds=60)

    print("Tardiness=", model.objective_value,)
    print()

    for i in range(numJobs):
        for j in range(numPos):
            if x[i][j].x >= 0.5:
                print("job ", i, " in posizione", j)
    print()

    for j in range(numPos):
        for m in range(numMachines):
            print(C[j][m].x, " ")
        print()


# Funzione di lettura e somma dati da file in input
def leggiDatiInput(filename):
    ptimes_raw = []
    stimes_raw = []
    due_dates = []

    reading_ptimes = False
    reading_stimes = False
    reading_duedates = False

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip(

                )
                if not line: continue

                if line.startswith("ptimes:"):
                    reading_ptimes = True
                    reading_stimes = False
                    reading_duedates = False
                    continue
                elif line.startswith("stimes:"):
                    reading_ptimes = False
                    reading_stimes = True
                    reading_duedates = False
                    continue
                elif line.startswith("due_dates:"):
                    reading_ptimes = False
                    reading_stimes = False
                    reading_duedates = True
                    continue
                elif line.startswith("heur_tardiness:"):
                    break

                if reading_ptimes:
                    row = [int(x) for x in line.split(',') if x]
                    ptimes_raw.append(row)
                elif reading_stimes:
                    row = [int(x) for x in line.split(',') if x]
                    stimes_raw.append(row)
                elif reading_duedates:
                    due_dates = [int(x) for x in line.split(',') if x]
    except FileNotFoundError:
        print(f"ERRORE: Non trovo il file '{filename}'")
        return None, None

    # Trasposizione e Somma: da [Macchina][Job] a [Job][Macchina]
    if not ptimes_raw:
        print("ERRORE: Non ho trovato dati ptimes nel file.")
        return None, None

    num_machines = len(ptimes_raw)
    num_jobs = len(ptimes_raw[0])

    combined_pTimes = []
    for j in range(num_jobs):
        job_times = []
        for m in range(num_machines):
            # Somma Processing + Setup
            total_time = ptimes_raw[m][j] + stimes_raw[m][j]
            job_times.append(total_time)
        combined_pTimes.append(job_times)

    return combined_pTimes, due_dates


# Funzione che genera una soluzione iniziale prendendo la migliore tra 100.000 sequenze random
def generaSolInizialeRandom(pTimes, due_dates):
    nTest = 100_000
    seq = [i for i in range(len(pTimes))]
    bestTT = calcolaTotalTardiness(seq, pTimes, due_dates)
    bestSeq = seq.copy()

    for i in range(nTest):
        random.shuffle(seq)
        tmpTT = calcolaTotalTardiness(seq, pTimes, due_dates)
        if tmpTT < bestTT:
            bestTT = tmpTT
            bestSeq = seq.copy()

    return bestSeq, bestTT


# Funziona che genera una soluzione iniziale ordinando i job per earliest due date
def generaSolInizialeEDD(pTimes, dueDates):

    seq = [i for i in range(len(pTimes))]  # lista vuota che rappresenta la sequenza

    seq.sort(key=lambda x: dueDates[x])  # ordino in EDD

    tt = calcolaTotalTardiness(seq, pTimes, dueDates)  # calcolo la TT per la sequenza ottenuta

    return seq, tt


# Funzione che a partire dalla soluzione iniziale effettua il best swap tra tutti possibili swap per ogni posizione
def miglioraSolSwap(seq, TT, pTimes, dueDates):
    migliorato = True
    num_jobs = len(seq)

    while migliorato:
        migliorato = False

        # Variabili per memorizzare la mossa migliore
        best_neighbor_tt = TT
        best_move_indices = None

        # Doppio ciclo per testare tutte le coppie (i, j)
        for i in range(num_jobs - 1):
            for j in range(i + 1, num_jobs):

                # SCAMBIO CON VARIABILE TEMPORANEA (TEMP)
                temp = seq[i]  # Salvo il valore di i in temp
                seq[i] = seq[j]  # Metto il valore di j in i
                seq[j] = temp  # Metto il valore temp (ex i) in j

                # 2. Valuto la soluzione
                current_neighbor_tt = calcolaTotalTardiness(seq, pTimes, dueDates)

                # 3. Controllo se è la migliore trovata finora
                if current_neighbor_tt < best_neighbor_tt:
                    best_neighbor_tt = current_neighbor_tt
                    best_move_indices = (i, j)

                # ---------------------------------------------------------
                # 4. ANNULLO SCAMBIO (UNDO) CON VARIABILE TEMP
                # ---------------------------------------------------------
                temp = seq[i]
                seq[i] = seq[j]
                seq[j] = temp

                # Fine del ciclo: se ho trovato una mossa che migliora
        if best_move_indices is not None:
            # Applico definitivamente la mossa migliore usando TEMP
            i_best, j_best = best_move_indices

            temp = seq[i_best]
            seq[i_best] = seq[j_best]
            seq[j_best] = temp

            TT = best_neighbor_tt
            migliorato = True
            #print(f"   >>> Miglioramento: Scambio ({i_best}, {j_best}) -> Nuova Tardiness: {TT}")
        #else:
            #print("   --- Ottimo Locale Raggiunto (Nessun miglioramento possibile).")

    return seq, TT


def miglioraSol2opt(seq, TT, pTimes, dueDates, n_iter):
    """
    Esegue n_iter tentativi di inversione (2-opt).
    Il segmento invertito deve avere una lunghezza di almeno 'min_dist',
    ma non c'è limite alla lunghezza massima.
    """
    #print(f"--- Avvio 2-Opt (Iter: {n_iter}, Min Dist: {min_dist}) ---")
    min_dist = 2
    num_jobs = len(seq)
    curr_seq = list(seq)
    curr_tt = TT

    # Controllo di sicurezza: se la lista è troppo corta per il min_dist, usciamo
    if num_jobs < min_dist + 1:
        print("Errore: Sequenza troppo corta per questa distanza minima.")
        return curr_seq, curr_tt

    for k in range(n_iter):

        # 1. Scelta di 'i' (inizio segmento)
        # Deve lasciare abbastanza spazio alla fine per 'min_dist'
        max_start_i = num_jobs - min_dist - 1
        i = random.randint(0, max_start_i)

        # 2. Scelta di 'j' (fine segmento)
        # Deve essere almeno 'min_dist' passi dopo 'i', fino alla fine della lista
        lower_bound_j = i + min_dist
        j = random.randint(lower_bound_j, num_jobs - 1)

        # 3. Crea il vicino invertendo il segmento i...j
        neighbor = list(curr_seq)
        # Python slicing: inverte la porzione da i a j inclusi
        neighbor[i: j + 1] = reversed(neighbor[i: j + 1])

        # 4. Valuta
        new_tt = calcolaTotalTardiness(neighbor, pTimes, dueDates)

        # 5. Accettazione (Hill Climbing / First Improvement)
        if new_tt < curr_tt:
            #print(f"   >>> [Iter {k}] Miglioramento (Segmento {j - i}): {curr_tt} -> {new_tt}")
            curr_tt = new_tt
            curr_seq = list(neighbor)

    return curr_seq, curr_tt

def calcolaListaTardiness(seq, pTimes, dueDates):
    numJobs = len(seq)
    numMachines = len(pTimes[0])

    # Creo la matrice dei completion time piena di 0
    C = []
    for m in range(numJobs):
        row = []
        for j in range(numMachines):
            row.append(0)
        C.append(row)

    C[0][0] = pTimes[seq[0]][0]  # il primo elemento della matrice è il pTime del job in posizione 0

    # Popolo la prima colonna
    for i in range(1, numJobs):
        C[i][0] = C[i-1][0] + pTimes[seq[i]][0]

    # Popolo la prima riga
    for j in range(1, numMachines):
        C[0][j] = C[0][j-1] + pTimes[seq[0]][j]

    # Riempio l'intera matrice
    for i in range(1, numJobs):
        for j in range(1, numMachines):
            C[i][j] = max(C[i-1][j], C[i][j-1]) + pTimes[seq[i]][j]

    t = [0] * numJobs  # vettore delle tardiness per ogni job

    # Calcolo la tardiness per ogni job e le sommo ottenendo tTot
    for i in range(numJobs):
        t[i] = max(0, C[i][numMachines-1] - dueDates[seq[i]])

    return t

def miglioraSolSmartSwap(seq, TT, pTimes, dueDates, max_iter):
    """
    Invece di scambiare a caso, identifica il job con il ritardo maggiore (Critical Job)
    e prova a scambiarlo con posizioni precedenti per anticiparlo.
    """
    #print(f"--- Avvio Smart Swap (Focus sui ritardi critici) ---")

    num_jobs = len(seq)
    curr_seq = list(seq)
    curr_tt = TT

    for i in range(max_iter):

        # 1. Identifica il Job Critico
        tardiness_values = calcolaListaTardiness(curr_seq, pTimes, dueDates)
        if sum(tardiness_values) == 0:
            print("   >>> Ottimo raggiunto (Tardiness 0). Stop.")
            break

        # Trova l'indice nella sequenza del job con ritardo massimo
        max_t = max(tardiness_values)
        idx_critico = tardiness_values.index(max_t)

        # Se il job critico è già primo, prendiamo il secondo peggiore, ecc.
        # (Semplificazione: se è primo proviamo a scambiarlo col successivo)
        if idx_critico == 0:
            target_swap = 1
        else:
            # Proviamo a scambiarlo con un job precedente a caso (per anticiparlo)
            target_swap = random.randint(0, idx_critico - 1)

        # 2. Esegui lo Swap (Critico <-> Target)
        neighbor = list(curr_seq)

        # Swap con variabile TEMP
        temp = neighbor[idx_critico]
        neighbor[idx_critico] = neighbor[target_swap]
        neighbor[target_swap] = temp

        # 3. Valuta
        next_tt = calcolaTotalTardiness(neighbor, pTimes, dueDates)

        # 4. Accetta se migliora (Hill Climbing)
        if next_tt < curr_tt:
            #print(f"   >>> [Iter {i}] Miglioramento Smart (Spostato Job {curr_seq[idx_critico]}): {curr_tt} -> {next_tt}")
            curr_tt = next_tt
            curr_seq = list(neighbor)
        else:
            # Se la mossa intelligente fallisce, proviamo una mossa casuale per diversificare
            # altrimenti rischiamo di provare sempre a spostare lo stesso job bloccato
            i = random.randint(0, num_jobs - 1)
            j = random.randint(0, num_jobs - 1)

            neighbor_rand = list(curr_seq)
            temp = neighbor_rand[i]
            neighbor_rand[i] = neighbor_rand[j]
            neighbor_rand[j] = temp

            cost_rand = calcolaTotalTardiness(neighbor_rand, pTimes, dueDates)

            if cost_rand < curr_tt:
                curr_tt = cost_rand
                curr_seq = list(neighbor_rand)
                #print(f"   >>> [Iter {i}] Miglioramento Random di supporto: {cost_rand}")

    #print(f"--- Fine Smart Swap. Risultato: {curr_tt}")
    return curr_seq, curr_tt


# MODULO: BLOCK INSERT (Spostamento a Blocchi)
# =============================================================================
def miglioraSolBlockInserte(seq, TT, pTimes, dueDates, max_iter):
    """
    Sposta interi blocchi di job (invece di singoli job) per preservare
    le sequenze parziali efficienti (setup bassi) ma migliorare la posizione globale.
    """
    #print(f"--- Avvio Block Insert (Iter: {max_iter}, BlockSize: {min_block}-{max_block}) ---")
    min_block = 4
    max_block = 20
    num_jobs = len(seq)
    curr_seq = list(seq)
    curr_tt = TT

    # Se la sequenza è troppo corta per fare blocchi, esci subito
    #if num_jobs < min_block + 1:
        #print("Errore: Sequenza troppo corta per Block Insert.")
        #return curr_seq, curr_tt

    # Assicuriamo che max_block non superi la lunghezza reale (meno 1 per lasciare spazio allo spostamento)
    #real_max_block = min(max_block, num_jobs - 1)

    for it in range(max_iter):

        # 1. Determina la dimensione del blocco
        block_size = random.randint(min_block, max_block)

        # 2. Scegli l'indice di INIZIO del blocco (idx_from)
        # Deve esserci spazio sufficiente per il blocco: max index = N - block_size
        max_start_index = num_jobs - block_size
        idx_from = random.randint(0, max_start_index)

        # 3. Estrai il blocco
        neighbor = list(curr_seq)

        # Salviamo il blocco da spostare
        block_to_move = neighbor[idx_from: idx_from + block_size]

        # Rimuoviamo il blocco dalla lista (del elimina la fetta)
        del neighbor[idx_from: idx_from + block_size]

        # 4. Scegli DOVE inserirlo (idx_to)
        # La lista ora è più corta di 'block_size' elementi
        remaining_len = len(neighbor)
        idx_to = random.randint(0, remaining_len)  # Può inserire anche alla fine (append)

        # Nota: Se idx_to == idx_from, rimetteremmo il blocco dov'era.
        # In quel caso è una mossa nulla, ma per semplicità la lasciamo valutare (costo identico).

        # 5. Inserisci il blocco nella nuova posizione
        # Slicing assignment: inseriamo la lista 'block_to_move' alla posizione 'idx_to'
        neighbor[idx_to:idx_to] = block_to_move

        # 6. Valuta
        cost = calcolaTotalTardiness(neighbor, pTimes, dueDates)

        # 7. Accetta se migliora (Hill Climbing)
        if cost < curr_tt:
            #print(f"   >>> [Iter {it}] Miglioramento Block (Size {block_size}): {curr_tt} -> {cost}")
            curr_tt = cost
            curr_seq = list(neighbor)

    #print(f"--- Fine Block Insert. Risultato: {curr_tt}")
    return curr_seq, curr_tt

pt, dd = leggiDatiInput("instance_0_with_stimes.txt")

start_time = time.time()

seq, tt = generaSolInizialeRandom(pt, dd)
print(tt)

max_seconds = 60
inTime = True

while inTime:
    if time.time() - start_time > max_seconds:
        inTime = False
        break

    seq2, tt2 = miglioraSol2opt(seq, tt, pt, dd,10000)
    print(tt2)

    if time.time() - start_time > max_seconds:
        inTime = False
        break

    seq3, tt3 = miglioraSolSmartSwap(seq2, tt2, pt, dd,10000)
    print(tt3)

    if time.time() - start_time > max_seconds:
        inTime = False
        break

    seq4, tt4 = miglioraSolBlockInserte(seq3, tt3, pt, dd,10000)
    print(f"{tt4}\n")

    seq = list(seq4)
    tt = tt4

print(time.time() - start_time)
