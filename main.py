import mip

#assegno dati fittizi per verificare risultato, per i job indicati i ptime, d sono le due date
num_machines = 3
num_jobs = 4
j0 = [2, 1, 2]
j1 = [3, 3, 2]
j2 = [2, 1, 2]
j3 = [3, 2, 2]
d = [4, 8, 13, 14]
p = [j0,j1,j2,j3]       #  p = [
                        #       [2,1,2],
                        #       [3,3,2],
                        #       [2,1,2],
                        #       [3,2,2]
                        #       ]

#costruisco matrice completion time
c = []

for m in range(num_jobs):
    row = []
    for j in range(num_machines):
        row.append(0)
    c.append(row)



#calcolo i completion time di tutti i job sulla prima macchina
c[0][0] = p[0][0]
for i in range(1,num_jobs):
    c[i][0] = c[i-1][0] + p[i][0]

#calcolo i completion time del job0 su tutte e tre le macchine
for j in range(1,num_machines):
    c[0][j] = c[0][j-1] + p[0][j]

#calcolo i completion time di tutti i job su tutte le macchine
for i in range(1,num_jobs):
    for j in range(1,num_machines):
        c[i][j] = max(c[i-1][j],c[i][j-1]) + p[i][j]

#calcolo la tardiness totale, dopo aver creato un vettore per inizializzare a 0 le singole tardiness
tTot = 0
t = [0] * num_jobs
for i in range(num_jobs):
    t[i] = max(0, c[i][num_machines-1]- d[i])
    tTot += t[i]

#prove per vedere a schermo se corretto
print(c)
print(tTot)

