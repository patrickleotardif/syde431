import random
from dataProcessing import *  #see dataProcessing.py

#constants
MAXLEVEL = 13
MINLEVEL = 1
MINFLOW = 0
MAXFLOW= 20
MAXPRODUCTIVEFLOW = 6
AMIN = 2
NUMBEROFDAYS = 366 #(2012)
INITIAL_LEVEL = 3

#scaling parameters
IRRIGATION_SCALE = 0.5   #0.1-2 [0.1 and 1]
COST_SCALE = 1   #0.5-5  [max is 4.986] c1 1 c2 2 c3 3 c5 5 c05 0.5
FLOW_SCALE = 0.08  #0.03 - 0.15 [max is 136]

#Given a single scenario, find perfect, stochastic, and deterministic solutions		
def getAllResults():
	scenario = generateScenario()
	costs = costData()
	perfect = perfectDecisionMatrix(scenario)
	scenario = [int(round(FLOW_SCALE*x)) for x in scenario] #rescale for further calculations
	stochastic = stochasticDecisionMatrix()
	deterministic = deterministicDecisionMatrix()
	perfect_decisions = []
	stochastic_decisions = []
	deterministic_decisions = []
	perfect_value = 0
	stochastic_value = 0
	deterministic_value = 0
	
	perfect_prevState = 3
	stochastic_prevState = 3
	deterministic_prevState = 3
	for t in range(NUMBEROFDAYS):
		perfect_decisions.append(perfect[t][perfect_prevState-1][1])
		perfect_value += perfect[t][perfect_prevState-1][2]
		perfect_prevState = perfect_prevState  + scenario[t] - perfect[t][perfect_prevState-1][1]
		
		stochastic_decisions.append(stochastic[t][stochastic_prevState-1][1])
		stochastic_value += stochastic[t][stochastic_prevState-1][2]
		stochastic_prevState = stochastic_prevState  + scenario[t] - stochastic[t][stochastic_prevState-1][1]
		
		deterministic_decisions.append(deterministic[t][deterministic_prevState-1][1])		
		deterministic_value += deterministic[t][deterministic_prevState-1][2]
		deterministic_prevState = deterministic_prevState  + scenario[t] - deterministic[t][deterministic_prevState-1][1]
		
		
	return [(perfect_value,stochastic_value,deterministic_value),(perfect_decisions,stochastic_decisions,deterministic_decisions),scenario]	

#Based on flow data, generate a random scenario of flow rates
def generateScenario():
	inflows = flowData()
	scenario = []
	for inflow in inflows:
		r = random.random()
		if r < inflow[0][1]:
			value = inflow[0][0]
		elif r < (inflow[1][1] + inflow[0][1]):
			value = inflow[1][0]
		else:
			value = inflow[2][0]
		scenario.append(value)
	return scenario

#Create of matrix of optimal decisions based on perfect information of given scenario
def perfectDecisionMatrix(scenario):
	allDecisions = {}
	prevStateValues = [(0,0)]*13
	costs = costData()
	inflows = [[(x,1.0)] for x in scenario]
	irrigations = irrigationData()
	
	for t in range(NUMBEROFDAYS):
		
		inflow = [(FLOW_SCALE*x[0],x[1]) for x in inflows[-(t+1)]] 
		cost = COST_SCALE*costs[-(t+1)]
		irrigation = IRRIGATION_SCALE*irrigations[-(t+1)]
		
		prevStateValues = singleTimeStep(prevStateValues, inflow, cost, irrigation)
		allDecisions[NUMBEROFDAYS-(t+1)] = prevStateValues
	
	return allDecisions

#Create a matrix of optimal decisions for deterministic DP based on flow mean
def deterministicDecisionMatrix():
	allDecisions = {}
	prevStateValues = [(0,0)]*13
	costs = costData()
	inflows = flowDataMeans()
	irrigations = irrigationData()
	
	for t in range(NUMBEROFDAYS):
		
		inflow = [(FLOW_SCALE*x[0],x[1]) for x in inflows[-(t+1)]] 
		cost = COST_SCALE*costs[-(t+1)]
		irrigation = IRRIGATION_SCALE*irrigations[-(t+1)]
		
		prevStateValues = singleTimeStep(prevStateValues, inflow, cost, irrigation)
		allDecisions[NUMBEROFDAYS-(t+1)] =  prevStateValues
	
	return allDecisions

#Create a matrix of optimal decisions for SDP
def stochasticDecisionMatrix():
	allDecisions = {}
	prevStateValues = [(0,0)]*13
	costs = costData()
	inflows = flowData()
	irrigations = irrigationData()
	
	for t in range(NUMBEROFDAYS):
		
		inflow = [(FLOW_SCALE*x[0],x[1]) for x in inflows[-(t+1)]] 
		cost = COST_SCALE*costs[-(t+1)]
		irrigation = IRRIGATION_SCALE*irrigations[-(t+1)]
		
		prevStateValues = singleTimeStep(prevStateValues, inflow, cost, irrigation)
		allDecisions[NUMBEROFDAYS-(t+1)] =  prevStateValues
	
	return allDecisions

#Solve a single time step		
def singleTimeStep(prevStateValues, inflows, cost, irrigation): 
	nextStateValues = []

	for state in range(MINLEVEL, MAXLEVEL+1):
		initialFeasibleDecisions = [] 
		for decision in range(MINFLOW,MAXFLOW):   
			if not ((state - decision + max(map(lambda x: x[0],inflows)) > MAXLEVEL) or 
					(state - decision + min(map(lambda x: x[0],inflows)) < MINLEVEL)):
				initialFeasibleDecisions.append(decision)
	
		wqCompliantDecisions = []		
		for decision in initialFeasibleDecisions:				
			if (decision - irrigation) >= AMIN:
				wqCompliantDecisions.append(decision)
	
		feasibleDecisions = []
	
		if len(wqCompliantDecisions) == 0:
			feasibleDecisions.append(max(initialFeasibleDecisions))
		else:
			feasibleDecisions = wqCompliantDecisions
	
		objFunctionValues = []
		for decision in feasibleDecisions:
			value = 0	
			
			#fixed cost
			static_value = cost*state*min(decision,MAXPRODUCTIVEFLOW)
			value += static_value
				
			#variable future states
			for inflow in inflows:
				value += inflow[1]*prevStateValues[int(round(state - decision + inflow[0] - 1))][0]
			
			objFunctionValues.append((1/(1+value),decision,static_value))  #so tuple sorting works
	
		optimum = min(objFunctionValues)
		optimum = ((1/optimum[0]) - 1,optimum[1],optimum[2]) #undo tuple sorting from above
		nextStateValues.append(optimum)
	
	return nextStateValues

def main():
	r = getAllResults()
	print('''
Stochastic Dynamic Programming for Maximizing 
Hydropower under Irrigation Constraint in a Reservoir System
	   
Patrick Leo Tardif (20296683) - 4B SYDE 2013
	   
-----Simulation of single scenario-------
	   
EVPI : %s %%
EVSS : %s %%
	   
Scenario
#################################
%s
	   
Perfect Information u(t) [Objective Function = %s]
#################################
%s
	   
Stochastic Solution u(t) [Objective Function = %s]
#################################
%s
	   
Deterministic Solution u(t) [Objective Function = %s]
#################################
%s  
	 ''' % (
	 (r[0][0] - r[0][1])*100/float(r[0][1]),
	 (r[0][1] - r[0][2])*100/float(r[0][2]),
	 r[2],
	 r[0][0],
	 r[1][0],
	 r[0][1],
	 r[1][1],
	 r[0][2],
	 r[1][2]
	 ))

if __name__ == "__main__":
    main()


		

	