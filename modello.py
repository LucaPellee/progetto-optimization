from mip import *
j0 = [2, 1, 2]
j1 = [3, 3, 2]
j2 = [2, 1, 2]
j3 = [3, 2, 2]
dueDates = [4, 8, 13, 14]
pTimes = [j0, j1, j2, j3]

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

    print(model.objective_value)
    for i in range(numJobs):
        for j in range(numPos):
            if x[i][j].x >= 0.5:
                print("job ",i, " in posizione",j,"")

    for j in range(numPos):
        for m in range(numMachines):
            print(C[j][m].x, " ")
        print()

ModelloMIP(pTimes,dueDates)
