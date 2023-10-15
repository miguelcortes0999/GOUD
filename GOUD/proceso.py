from typing import List, Tuple, Dict, Optional, Union
from openpyxl.styles import Font, Alignment
from itertools import combinations
from itertools import permutations
import matplotlib.pyplot as plt
from gurobipy import *
import networkx as nx
import pandas as pd
import numpy as np
from pulp import *
import openpyxl
import os

# Deshabilitar todas las advertencias de tipo UserWarning a nivel global
warnings.filterwarnings("ignore", category=UserWarning)

class BalanceoLineaProgramacionLineal():
    def __init__(self, tareas, tiempoCiclo : int, objetivo = 'Numeros estaciones'):
        '''
        BalanceoLineaProgramacionLineal(tareas: dict[str, list[float, str]], tiempoCiclo: int, objetivo : str = 'Numeros estaciones')\n
        El objetivo es distribuir las tareas de manera equilibrada entre las estaciones de trabajo disponibles, con el fin de minimizar 
        los tiempos de espera y maximizar la eficiencia de la línea de producción.
        Argumentos:\n
        tareas : dict
            Enviar diccionario con nombre de cada tarea como llave, y cada valor debe ser una lista en la cual el primer valor debe ser
            un valor tipo int o float que representara el tiempo en SEGUNDOS de la tarea, y en la siguiente posicion de la lista un str
            con el nombre del predecesor, en caso de ser mas de un predecesor separarlos con el simbolo '-', es decir es un simbolo reservado 
            para su uso, y evitar el uso usar espacios
        tiempoCiclo: int
            Para el segundo argumento se debe enviar el timepo de ciclo, es el timepo necesario para completar una unidad de producción desde el incio hasta el final
        objetivo: str
            Función objetivo por la cual se resolvera el modelo, estan disponibles ['Numeros estaciones', ]
        Ejemplo:\n
            tareas={'A' : [12   , '-'],\n
                    'B' : [24   , '-'],\n
                    'C' : [42   , 'A'] ,\n
                    'D' : [6    , 'A-B'],\n
                    'E' : [18   , 'B'],\n
                    'F' : [6.6  , 'C'],\n
                    'G' : [19.2 , 'C'],\n
                    'H' : [36   , 'C-D'],\n
                    'I' : [16.2 , 'F-G-H'],\n
                    'J' : [22.8 , 'E-H'],\n
                    'K' : [30   , 'I-J'] }\n
            tiempo_ritmo =  60\n
            BalnceoLinea = BalanceoLineaProgramacionLineal(tareas, tiempo_ritmo, objetivo = 'Tiempo muerto')\n
            print( BalnceoLinea.DiccionarioEstaciones())\n
            BalnceoLinea.Grafo(estaciones=True)
        '''
        self.funcion_objetivo = objetivo
        self.modelo = LpProblem("modelo_balanceo_linea", sense=LpMinimize)
        self.tareas = tareas
        self.tiempo_ritmo = tiempoCiclo
        self.EstacionesMinimas()
        self.CrearVariables()
        self.RestriccionPredecesores()
        self.RestriccionActivaciones()
        self.RestriccionTiempoCiclo()
        self.RestriccionTiempoMuerto()
        self.FuncionObjetivo()
        self.Solucionar()
    
    # Calcular minimo de estaciones sugeridas, mas un margen
    def EstacionesMinimas(self):
        if self.funcion_objetivo == 'Numeros estaciones':
            self.estaciones = sum([self.tareas[tarea][0] for tarea in self.tareas.keys()])/self.tiempo_ritmo
            self.estaciones = int((self.estaciones//1)+1)+1 # + 1 Extra para descartar infactibilidad del modelo
        else:
            self.estaciones = len(self.tareas)
    
    # Crear vairbales modelo
    def CrearVariables(self):
        self.binaria_estacion = LpVariable.dicts('BinariaEstacion', (estacion for estacion in range(self.estaciones)) , cat='Binary')
        self.binaria_tarea_estacion = LpVariable.dicts('BinariaTareaEstacion', ((tarea,estacion) for estacion in range(self.estaciones) for tarea in self.tareas.keys()) , cat='Binary')
        self.tiempo_ciclo = LpVariable('TiempoCiclo', lowBound=0, cat='Continuos')
        self.tiempo_ciclo_estacion = LpVariable.dicts('TiempoCicloEstacion', (estacion for estacion in range(self.estaciones)) , lowBound=0, cat='Continuos')
        self.tiempo_muerto_estacion = LpVariable.dicts('TiempoMuerto', (estacion for estacion in range(self.estaciones)) , lowBound=0, cat='Continuos')

    # Restriccion de predecesores
    def RestriccionPredecesores(self):
        for tarea in self.tareas.keys():
            if self.tareas[tarea][1] != '-':
                predecesores = self.tareas[tarea][1].split('-')
                for estacion in range(self.estaciones):
                    self.modelo += lpSum(self.binaria_tarea_estacion[predecesor,estacionacu] for predecesor in predecesores for estacionacu in range(0,estacion+1)) >= self.binaria_tarea_estacion[tarea,estacion]*len(predecesores) 

    # Restriccion Activaciones de estaciones y tareas por estacion
    def RestriccionActivaciones(self):
        for estacion in range(self.estaciones):
            self.modelo += lpSum(self.binaria_tarea_estacion[tarea,estacion]*self.tareas[tarea][0] for tarea in self.tareas.keys()) <= self.tiempo_ritmo*self.binaria_estacion[estacion]
            self.modelo += -(self.binaria_estacion[estacion]*1000000) + self.tiempo_ciclo_estacion[estacion] <= 0
        for tarea in self.tareas.keys():
            self.modelo += lpSum(self.binaria_tarea_estacion[tarea,estacion] for estacion in range(self.estaciones)) == 1

    # Calculo de tiempo de ciclo
    def RestriccionTiempoCiclo(self):
        for estacion in range(self.estaciones):
            self.modelo += lpSum(self.binaria_tarea_estacion[tarea,estacion]*self.tareas[tarea][0] for tarea in self.tareas.keys()) <= self.tiempo_ciclo 
            self.modelo += lpSum(self.binaria_tarea_estacion[tarea,estacion]*self.tareas[tarea][0] for tarea in self.tareas.keys()) == self.tiempo_ciclo_estacion[estacion] 

    # Calculo de tiempo muerto
    def RestriccionTiempoMuerto(self):
        for estacion in range(self.estaciones):
            self.modelo += self.tiempo_ciclo_estacion[estacion] + self.tiempo_muerto_estacion[estacion] >= self.tiempo_ciclo - (1-self.binaria_estacion[estacion])*1000000
    
    # Declaracion de Funcion objetivo
    def FuncionObjetivo(self):
        if self.funcion_objetivo == 'Numeros estaciones':
            self.modelo += lpSum(self.binaria_estacion[estacion] for estacion in range(self.estaciones))
        elif self.funcion_objetivo == 'Tiempo ciclo':
            self.modelo += self.tiempo_ciclo
        elif self.funcion_objetivo == 'Tiempo muerto':
            self.modelo += lpSum(self.tiempo_muerto_estacion[estacion] for estacion in range(self.estaciones))
        else:
            raise ValueError('Funcion objetivo no valida.')

    # Diccionario tareas por estacion
    def DiccionarioEstaciones(self):
        self.activacion_estacion = {}
        for v in self.modelo.variables():
            if 'BinariaTareaEstacion' in str(v) and v.varValue>0:
                nombre = str(v)
                nombre = nombre.replace('BinariaTareaEstacion_','').replace('(','').replace(')','').replace('_','').replace("'",'')
                nombre = nombre.split(',')
                self.activacion_estacion[nombre[0]] = 'Estacion '+ str(int(nombre[1])+1)
            elif 'BinariaTareaEstacion' not in str(v):
                print(v, v.varValue)
        return self.activacion_estacion

    # Solucionar modelo multiobjetivo
    def Solucionar(self):
        if self.funcion_objetivo == 'Numeros estaciones':
            # Modelo Uso minimo de estaciones
            self.status = self.modelo.solve(solver=GUROBI(msg = False))
            if 'Optimal'== LpStatus[self.modelo.status]:
                self.horizonteTemporal = round(value(self.modelo.objective),0)
            else:
                raise 'Porblema en factibilidad del modelo'
            estaciones = 0
            # Asignacion de Restriccion Minima de Estaciones
            for v in self.modelo.variables():
                if 'BinariaEstacion' in str(v):
                    estaciones += v.varValue
            self.maximo_tiempo_estacion = LpVariable('MaximoTiempoEstacion', lowBound=0, cat='Continuous')
            for estacion in range(self.estaciones):
                self.modelo += lpSum(self.binaria_tarea_estacion[tarea,estacion]*self.tareas[tarea][0] for tarea in self.tareas.keys()) <= self.maximo_tiempo_estacion
            self.modelo += lpSum(self.binaria_estacion[estacion] for estacion in range(self.estaciones)) == estaciones 
            self.modelo += (1/sum([self.tareas[tarea][0] for tarea in self.tareas.keys()]))*(estaciones*self.maximo_tiempo_estacion)
        # Asignacion Maximizar Eficiencia de Linea en modelo
        self.status = self.modelo.solve(solver=GUROBI(msg = False))
        if 'Optimal'== LpStatus[self.modelo.status]:
            #print('-'*5+' Modelo solucionado correctamente '+'-'*5)
            self.horizonteTemporal = round(value(self.modelo.objective),0)
            self.DiccionarioEstaciones()
        else:
            raise 'Porblema en factibilidad del modelo'

    def Grafo(self, estaciones=False):
        # Crear un grafo dirigido
        G = nx.DiGraph()
        # Agregar nodos al grafo
        for tarea, datos in self.tareas.items():
            duracion, dependencias = datos
            G.add_node(tarea, duracion=duracion)
        # Agregar arcos entre las tareas dependientes
        for tarea, datos in self.tareas.items():
            dependencias = datos[1]
            if dependencias != '-':
                dependencias = dependencias.split('-')
                for dependencia in dependencias:
                    G.add_edge(dependencia, tarea)
        # Calcular el orden topológico
        orden_topologico = list(nx.topological_sort(G))
        nuevo_diccionario = {clave: valor[1].split('-') for clave, valor in self.tareas.items()}
        orden_topologico.reverse()
        # Crear un grafo dirigido con las dependencias
        Gaux = nx.DiGraph(nuevo_diccionario)
        # Crear un diccionario para agrupar los nodos por capa
        nodos_por_capa = {}
        for nodo in orden_topologico:
            predecesores = list(Gaux.predecessors(nodo))
            capa = max([nodos_por_capa[pre] for pre in predecesores], default=0) + 1
            nodos_por_capa[nodo] = capa
        # Organizar los nodos en listas por capa
        listas_por_capa = {}
        for nodo, capa in nodos_por_capa.items():
            if capa not in listas_por_capa:
                listas_por_capa[capa] = []
            listas_por_capa[capa].append(nodo)
        # Crear un nuevo gráfico ordenado con spring layout
        pos = {t: (c * -1500, p*-500) for c in listas_por_capa.keys() for p,t in enumerate(listas_por_capa[c])}
        # Dibujar el grafo ordenado
        if estaciones == True:
            # Crear diccionario de estaciones si no ha sido creado
            self.DiccionarioEstaciones()
            # Crear dicionario de colores
            colores_aleatorios = {nodo: "#{:02x}{:02x}{:02x}".format(np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255)) for nodo in set(self.activacion_estacion.values())}
            diccionario_colores = {t: colores_aleatorios[self.activacion_estacion[t]] for t in self.activacion_estacion.keys()}
            node_colors = [diccionario_colores[nodo] for nodo in G.nodes]
            nx.draw(G, pos=pos, with_labels=True, node_size=1000, node_color=node_colors, font_size=8, font_color='black')
        else:
            nx.draw(G, pos=pos, with_labels=True, node_size=1000, node_color='lightblue', font_size=8, font_color='black')
        # Mostrar el gráfico ordenado
        plt.show()

tareas={'A' : [12   , '-'],
        'B' : [24   , '-'],
        'C' : [42   , 'A'] ,
        'D' : [6    , 'A-B'],
        'E' : [18   , 'B'],
        'F' : [6.6  , 'C'],
        'G' : [19.2 , 'C'],
        'H' : [36   , 'C-D'],
        'I' : [16.2 , 'F-G-H'],
        'J' : [22.8 , 'E-H'],
        'K' : [30   , 'I-J'] }
tiempo_ritmo =  60
BalnceoLinea = BalanceoLineaProgramacionLineal(tareas, tiempo_ritmo, objetivo = 'Tiempo muerto')
print(BalnceoLinea.DiccionarioEstaciones())
BalnceoLinea.Grafo(estaciones=True)