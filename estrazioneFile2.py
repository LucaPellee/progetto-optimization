from mip import *

# --- 1. FUNZIONE DI LETTURA E SOMMA DATI ---
def leggi_e_somma_istanza(filename):
    ptimes_raw = []
    stimes_raw = []
    due_dates = []

    reading_ptimes = False
    reading_stimes = False
    reading_duedates = False

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
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
        print(f"Errore: Il file '{filename}' non è stato trovato.")
        return None, None

    # Trasposizione e Somma: da [Macchina][Job] a [Job][Macchina]
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


# --- 2. MODELLO MIP ---
def ModelloMIP(pTimes, dueDates):
    if not pTimes: return  # Esce se non ci sono dati

    numJobs = len(pTimes)
    numMachines = len(pTimes[0])
    numPos = numJobs

    # Creazione Modello
    model = mip.Model(sense=MINIMIZE, solver_name='CBC')

    # Variabili
    # x[i][j] = 1 se il job i è assegnato alla posizione j
    x = [[model.add_var(var_type=BINARY) for j in range(numPos)] for i in range(numJobs)]

    # C[j][m] = tempo di completamento alla posizione j sulla macchina m
    C = [[model.add_var(var_type=CONTINUOUS, lb=0.0) for m in range(numMachines)] for j in range(numPos)]

    # T[j] = Tardiness del job in posizione j
    T = [model.add_var(var_type=CONTINUOUS, lb=0.0) for j in range(numPos)]

    # Vincoli di assegnamento
    for i in range(numJobs):
        model += xsum(x[i][j] for j in range(numPos)) == 1  # Ogni job in una sola posizione

    for j in range(numPos):
        model += xsum(x[i][j] for i in range(numJobs)) == 1  # Ogni posizione ha un solo job

    # Calcolo tempi di completamento (C)
    # Prima posizione (j=0), Prima macchina (m=0)
    model += C[0][0] == xsum(pTimes[i][0] * x[i][0] for i in range(numJobs))

    # Prima posizione (j=0), Macchine successive
    for m in range(1, numMachines):
        model += C[0][m] == C[0][m - 1] + xsum(pTimes[i][m] * x[i][0] for i in range(numJobs))

    # Posizioni successive (j>0), Prima macchina
    for j in range(1, numPos):
        model += C[j][0] == C[j - 1][0] + xsum(pTimes[i][0] * x[i][j] for i in range(numJobs))

    # Posizioni successive (j>0), Macchine successive
    for m in range(1, numMachines):
        for j in range(1, numPos):
            model += C[j][m] >= C[j - 1][m] + xsum(pTimes[i][m] * x[i][j] for i in range(numJobs))
            model += C[j][m] >= C[j][m - 1] + xsum(pTimes[i][m] * x[i][j] for i in range(numJobs))

    # Calcolo Tardiness
    for j in range(numPos):
        # T[j] >= C_finale - DueDate_del_job_in_pos_j
        model += T[j] >= C[j][numMachines - 1] - xsum(dueDates[i] * x[i][j] for i in range(numJobs))

    # Obiettivo: Minimizzare somma Tardiness
    model.objective = xsum(T[j] for j in range(numPos))
    model.verbose = 1  # Imposta a 1 per vedere il log del solver

    print("Avvio ottimizzazione...")
    model.optimize(max_seconds=60)

    print("Valore Obiettivo (Total Tardiness):", model.objective_value)

    # Stampa risultati semplificata
    # for j in range(numPos):
    #     for i in range(numJobs):
    #         if x[i][j].x >= 0.99:
    #             print(f"Pos {j}: Job {i}")


# --- 3. ESECUZIONE ---
nome_file = 'instance0.txt'  # Assicurati che il file sia nella stessa cartella
print(f"Lettura file: {nome_file}...")

pTimes, dueDates = leggi_e_somma_istanza(nome_file)

if pTimes:
    print(f"Dati caricati: {len(pTimes)} jobs, {len(pTimes[0])} macchine.")
    print(pTimes)
    print(dueDates)
    ModelloMIP(pTimes, dueDates)