from typing import List, Tuple, Dict, Optional, Union
from openpyxl.styles import Font, Alignment
from itertools import combinations
from itertools import permutations
import matplotlib.pyplot as plt
from gurobipy import *
import pandas as pd
import numpy as np
from pulp import *
import openpyxl
import os

class ReglasSecuenciacion():
    def __init__(self, tareas : Dict, importancia : pd.DataFrame = None):
        '''
        Clase para aplicar diferentes reglas de secuenciación a un conjunto de tareas.\n
        Argumentos:\n
        tareas : dict
            Diccionario que contiene las tareas a ser secuenciadas. Cada tarea se representa mediante un diccionario que incluye: duración, tiempo de inicio, tiempo de entrega y costos de retraso.\n
        importancia : DataFrame
            DataFrame que contiene el indice como cada tarea y una unica columnas con las importancias de cada tarea qy esta debe sumar 1.\n
        Ejmplo:\n
            tareas={'T1' : {'duraciones':1, 'timpos inicio':4  , 'tiempo entrega':8,  'costos retraso':1},\n
                    'T2' : {'duraciones':5, 'timpos inicio':1  , 'tiempo entrega':12, 'costos retraso':8},\n
                    'T3' : {'duraciones':1, 'timpos inicio':2  , 'tiempo entrega':29, 'costos retraso':7},\n
                    'T4' : {'duraciones':2, 'timpos inicio':3  , 'tiempo entrega':15, 'costos retraso':5},\n
                    'T5' : {'duraciones':1, 'timpos inicio':5  , 'tiempo entrega':28, 'costos retraso':3},\n
                    'T6' : {'duraciones':7, 'timpos inicio':10 , 'tiempo entrega':19, 'costos retraso':1},\n
                    'T7' : {'duraciones':3, 'timpos inicio':6  , 'tiempo entrega':15, 'costos retraso':9},\n
                    'T8' : {'duraciones':2, 'timpos inicio':8  , 'tiempo entrega':9,  'costos retraso':4}}\n
            importancias = pd.DataFrame([0.05,0.30,0.15,0.1,0.1,0.1,0.1,0.1], index=list(tareas.keys()))\n
            rs = ReglasSecuenciacion(tareas, importancias)\n
            print(rs.TiempoProcesamientoCorto())\n
            print(rs.TiempoProcesamientoLargo())\n
            print(rs.TiempoFinalizacionTemprano())\n
            print(rs.TiempoFinalizacionTardio())\n
            print(rs.RelacionProcesameintoEntregaCorto())\n
            print(rs.RelacionProcesameintoEntregaLargo())\n
            print(rs.CostoRestrasoAlto())\n
            for nom, val in rs.ReglasSecuenciacion().items():\n
                print(nom, '\n', val)\n
            print(rs.MetricasGeneralesSecuenciacion())\n
            print(rs.GraficarMetricas())\n
        '''
        self.tareas = tareas
        self.data = pd.DataFrame(tareas).T
        self.importancia = pd.DataFrame(index = self.data.index)
        if importancia is None:
            print('aca')
            self.importancia['importancia'] = 1/len(self.data.index)
            print(self.importancia)
        else:
            # Ordenar los índices de ambos DataFrames
            dfaux1 = self.data.sort_index()
            dfaux2 = importancia.sort_index()
            if dfaux1.index.equals(dfaux2.index):
                if importancia[importancia.columns[0]].sum() != 1:
                    raise("Las sumatoria de las importancias no es igual a 1")
            else:
                raise("Los índices de los DataFrames son diferentes")
            self.importancia['importancia'] = importancia
        print(self.importancia)

    # Calcular metricas
    def Metricas(self, df : pd.DataFrame):
        df['inicio real'] = 0
        df['final real'] = 0
        tareas = list(df.index)
        for i, ind in enumerate(df.index):
            if i == 0:
                df.loc[ind,'inicio real'] = df.iloc[i,1]
                df.loc[ind,'final real'] = df.loc[ind,'inicio real'] + df.iloc[i,0]
            else:
                df.loc[ind,'inicio real'] = max(df.iloc[i,1], df.loc[tareas[i-1],'final real'])
                df.loc[ind,'final real'] = df.loc[ind,'inicio real'] + df.iloc[i,0]
        df['tiempo flujo'] = df['final real'] * df['importancia']
        for i, ind in enumerate(df.index):
            df.loc[ind,'anticipación'] = (df.iloc[i,2]-df.loc[ind,'final real'])*df.loc[ind,'importancia'] if df.iloc[i,2]-df.loc[ind,'final real']>0 else 0
            df.loc[ind,'tardanza'] = (df.loc[ind,'final real']-df.iloc[i,2])*df.loc[ind,'importancia'] if df.loc[ind,'final real']-df.iloc[i,2]>0 else 0
        return df
    
    #LIFO
    #FIFO

    # SPT: Tiempo de Procesamiento más Corto
    def TiempoProcesamientoCorto(self):
        self.tiempo_procesamiento_corto = self.data.copy().sort_values([self.data.columns[0]], ascending=True)
        self.tiempo_procesamiento_corto['importancia'] = self.importancia
        self.tiempo_procesamiento_corto = self.Metricas(self.tiempo_procesamiento_corto)
        return self.tiempo_procesamiento_corto
    
    # LPT: Tiempo de Procesamiento más Largo
    def TiempoProcesamientoLargo(self):
        self.tiempo_procesamiento_largo = self.data.copy().sort_values([self.data.columns[0]], ascending=False)
        self.tiempo_procesamiento_largo['importancia'] = self.importancia
        self.tiempo_procesamiento_largo = self.Metricas(self.tiempo_procesamiento_largo)
        return self.tiempo_procesamiento_largo

    # EFT: Tiempo de Finalización más Temprano
    def TiempoFinalizacionTemprano(self):
        self.tiempo_finalizacion_temprano = self.data.copy()
        self.tiempo_finalizacion_temprano['tiempo finalizacion'] = self.tiempo_finalizacion_temprano[self.tiempo_finalizacion_temprano.columns[1]] + self.tiempo_finalizacion_temprano[self.tiempo_finalizacion_temprano.columns[0]]
        self.tiempo_finalizacion_temprano = self.tiempo_finalizacion_temprano.sort_values([self.tiempo_finalizacion_temprano.columns[4]], ascending=True)
        self.tiempo_finalizacion_temprano['importancia'] = self.importancia
        self.tiempo_finalizacion_temprano = self.Metricas(self.tiempo_finalizacion_temprano)
        return self.tiempo_finalizacion_temprano
    
    # LFT: Tiempo de Finalización más Tardío
    def TiempoFinalizacionTardio(self):
        self.tiempo_finalizacion_tardio = self.data.copy()
        self.tiempo_finalizacion_tardio['tiempo finalizacion'] = self.tiempo_finalizacion_tardio[self.tiempo_finalizacion_tardio.columns[1]] + self.tiempo_finalizacion_tardio[self.tiempo_finalizacion_tardio.columns[0]]
        self.tiempo_finalizacion_tardio = self.tiempo_finalizacion_tardio.sort_values([self.tiempo_finalizacion_tardio.columns[4]], ascending=True)
        self.tiempo_finalizacion_tardio['importancia'] = self.importancia
        self.tiempo_finalizacion_tardio = self.Metricas(self.tiempo_finalizacion_tardio)
        return self.tiempo_finalizacion_tardio
    
    # EDD: Tiempo de Entrega (Earliest Due Date)
    def ProcesameintoEntregaCorto(self):
        self.procesamiento_entrega_corto = self.data.copy()
        self.procesamiento_entrega_corto = self.procesamiento_entrega_corto.sort_values([self.procesamiento_entrega_corto.columns[2]], ascending=True)
        self.procesamiento_entrega_corto['importancia'] = self.importancia
        self.procesamiento_entrega_corto = self.Metricas(self.procesamiento_entrega_corto)
        return self.procesamiento_entrega_corto

    # S/EDD: Relación Tiempo de Procesamiento-Tiempo de Entrega (Corto/Earliest Due Date)
    def RelacionProcesameintoEntregaCorto(self):
        self.relacion_procesamiento_entrega_corto = self.data.copy()
        self.relacion_procesamiento_entrega_corto['relacion procesamiento entrega'] = self.relacion_procesamiento_entrega_corto[self.relacion_procesamiento_entrega_corto.columns[0]]/self.relacion_procesamiento_entrega_corto[self.relacion_procesamiento_entrega_corto.columns[2]]
        self.relacion_procesamiento_entrega_corto = self.relacion_procesamiento_entrega_corto.sort_values([self.relacion_procesamiento_entrega_corto.columns[4]], ascending=True)
        self.relacion_procesamiento_entrega_corto['importancia'] = self.importancia
        self.relacion_procesamiento_entrega_corto = self.Metricas(self.relacion_procesamiento_entrega_corto)
        return self.relacion_procesamiento_entrega_corto
    
    # L/EDD: Relación Tiempo de Procesamiento-Tiempo de Entrega (Largo/Earliest Due Date)
    def RelacionProcesameintoEntregaLargo(self):
        self.relacion_procesamiento_entrega_largo = self.data.copy()
        self.relacion_procesamiento_entrega_largo['relacion procesamiento entrega'] = self.relacion_procesamiento_entrega_largo[self.relacion_procesamiento_entrega_largo.columns[0]]/self.relacion_procesamiento_entrega_largo[self.relacion_procesamiento_entrega_largo.columns[2]]
        self.relacion_procesamiento_entrega_largo = self.relacion_procesamiento_entrega_largo.sort_values([self.relacion_procesamiento_entrega_largo.columns[4]], ascending=False)
        self.relacion_procesamiento_entrega_largo['importancia'] = self.importancia
        self.relacion_procesamiento_entrega_largo = self.Metricas(self.relacion_procesamiento_entrega_largo)
        return self.relacion_procesamiento_entrega_largo

    # HLC: Costo de Retraso más Alto
    def CostoRestrasoAlto(self):
        self.costo_retraso_alto = self.data.copy().sort_values([self.data.columns[3]], ascending=False)
        self.costo_retraso_alto['importancia'] = self.importancia
        self.costo_retraso_alto = self.Metricas(self.costo_retraso_alto)
        return self.costo_retraso_alto
    
    # Todos las reglas de secuanciacion
    def ReglasSecuenciacion(self):
        self.diccionario_reglas_secuanciacion = {}
        try:
            self.diccionario_reglas_secuanciacion['SPT tiempo procesamiento mas corto'] = self.TiempoProcesamientoCorto()
        except:
            pass
        try:
            self.diccionario_reglas_secuanciacion['LPT tiempo procesamiento mas largo'] = self.TiempoProcesamientoLargo()
        except:
            pass
        try:
            self.diccionario_reglas_secuanciacion['EFT tiempo finalizacion mas temprano'] = self.TiempoFinalizacionTemprano()
        except:
            pass
        try:
            self.diccionario_reglas_secuanciacion['LFT tiempo finalizacion mas tardio'] = self.TiempoFinalizacionTardio()
        except:
            pass
        try:
            self.diccionario_reglas_secuanciacion['EDD tiempo entrega mas corto'] = self.ProcesameintoEntregaCorto()
        except:
            pass
        try:
            self.diccionario_reglas_secuanciacion['S/EDD relacion tiempo procesamiento con entrega mas corto'] = self.RelacionProcesameintoEntregaCorto()
        except:
            pass
        try:
            self.diccionario_reglas_secuanciacion['L/EDD relacion tiempo procesamiento con entrega mas largo'] = self.RelacionProcesameintoEntregaLargo()
        except:
            pass
        try:
            self.diccionario_reglas_secuanciacion['HLC costo retraso mas alto'] = self.CostoRestrasoAlto()
        except:
            pass
        return self.diccionario_reglas_secuanciacion
    
    # Todos las metricas reglas de secuanciacion
    def MetricasGeneralesSecuenciacion(self):
        self.metricas_generales = pd.DataFrame()
        try:
            self.metricas_generales.loc['SPT tiempo procesamiento mas corto','tiempo flujo'] = self.TiempoProcesamientoCorto()['tiempo flujo'].sum()
            self.metricas_generales.loc['SPT tiempo procesamiento mas corto','anticipación'] = self.TiempoProcesamientoCorto()['anticipación'].sum()
            self.metricas_generales.loc['SPT tiempo procesamiento mas corto','tardanza'    ] = self.TiempoProcesamientoCorto()['tardanza'].sum()    
        except:
            pass
        try:
            self.metricas_generales.loc['LPT tiempo procesamiento mas largo','tiempo flujo'] = self.TiempoProcesamientoLargo()['tiempo flujo'].sum()
            self.metricas_generales.loc['LPT tiempo procesamiento mas largo','anticipación'] = self.TiempoProcesamientoLargo()['anticipación'].sum()
            self.metricas_generales.loc['LPT tiempo procesamiento mas largo','tardanza'    ] = self.TiempoProcesamientoLargo()['tardanza'].sum()    
        except:
            pass
        try:
            self.metricas_generales.loc['EFT tiempo finalizacion mas temprano','tiempo flujo'] = self.TiempoFinalizacionTemprano()['tiempo flujo'].sum()
            self.metricas_generales.loc['EFT tiempo finalizacion mas temprano','anticipación'] = self.TiempoFinalizacionTemprano()['anticipación'].sum()
            self.metricas_generales.loc['EFT tiempo finalizacion mas temprano','tardanza'    ] = self.TiempoFinalizacionTemprano()['tardanza'].sum()    
        except:
            pass
        try:
            self.metricas_generales.loc['LFT tiempo finalizacion mas tardio','tiempo flujo'] = self.TiempoFinalizacionTardio()['tiempo flujo'].sum()
            self.metricas_generales.loc['LFT tiempo finalizacion mas tardio','anticipación'] = self.TiempoFinalizacionTardio()['anticipación'].sum()
            self.metricas_generales.loc['LFT tiempo finalizacion mas tardio','tardanza'    ] = self.TiempoFinalizacionTardio()['tardanza'].sum()    
        except:
            pass
        try:
            self.metricas_generales.loc['EDD tiempo entrega mas corto','tiempo flujo'] = self.ProcesameintoEntregaCorto()['tiempo flujo'].sum()
            self.metricas_generales.loc['EDD tiempo entrega mas corto','anticipación'] = self.ProcesameintoEntregaCorto()['anticipación'].sum()
            self.metricas_generales.loc['EDD tiempo entrega mas corto','tardanza'    ] = self.ProcesameintoEntregaCorto()['tardanza'].sum()    
        except:
            pass
        try:
            self.metricas_generales.loc['S/EDD relacion tiempo procesamiento con entrega mas corto','tiempo flujo'] = self.RelacionProcesameintoEntregaCorto()['tiempo flujo'].sum()
            self.metricas_generales.loc['S/EDD relacion tiempo procesamiento con entrega mas corto','anticipación'] = self.RelacionProcesameintoEntregaCorto()['anticipación'].sum()
            self.metricas_generales.loc['S/EDD relacion tiempo procesamiento con entrega mas corto','tardanza'    ] = self.RelacionProcesameintoEntregaCorto()['tardanza'].sum()    
        except:
            pass
        try:
            self.metricas_generales.loc['L/EDD relacion tiempo procesamiento con entrega mas largo','tiempo flujo'] = self.RelacionProcesameintoEntregaLargo()['tiempo flujo'].sum()
            self.metricas_generales.loc['L/EDD relacion tiempo procesamiento con entrega mas largo','anticipación'] = self.RelacionProcesameintoEntregaLargo()['anticipación'].sum()
            self.metricas_generales.loc['L/EDD relacion tiempo procesamiento con entrega mas largo','tardanza'    ] = self.RelacionProcesameintoEntregaLargo()['tardanza'].sum()    
        except:
            pass
        try:
            self.metricas_generales.loc['HLC costo retraso mas alto','tiempo flujo'] = self.CostoRestrasoAlto()['tiempo flujo'].sum()
            self.metricas_generales.loc['HLC costo retraso mas alto','anticipación'] = self.CostoRestrasoAlto()['anticipación'].sum()
            self.metricas_generales.loc['HLC costo retraso mas alto','tardanza'    ] = self.CostoRestrasoAlto()['tardanza'].sum()    
        except:
            pass
        return self.metricas_generales
    
    # Grafico de metricas
    def GraficarMetricas(self):
        df = self.MetricasGeneralesSecuenciacion()
        # Definir las categorías
        categorias = [x.split(' ')[0] for x in df.index]
        # Crear una lista de ángulos para el gráfico de telaraña
        angulos = [n / float(len(categorias)) * 2 * np.pi for n in range(len(categorias))]
        angulos += angulos[:1]
        # Crear subplots, uno para cada columna
        fig, axs = plt.subplots(1, 3, figsize=(12, 4), subplot_kw={'polar': True})  # 1 fila y 3 columnas de subplots
        # Iterar a través de las columnas y crear un gráfico de telaraña para cada una
        colores = ['#FFFF00','#008000','#FF0000']
        for i, columna in enumerate(df.columns):  # Ignorar la columna 'Categoria'
            puntuaciones = df[columna].tolist()
            puntuaciones += puntuaciones[:1]
            axs[i].fill(angulos, puntuaciones, alpha=0.25, color=colores[i])
            axs[i].set_xticks(angulos[:-1])
            axs[i].set_xticklabels(categorias)
            axs[i].set_title(columna)
        # Ajustar el espaciado entre los gráficos
        plt.tight_layout()
        # Mostrar los gráficos
        plt.show()

#tareas={'T1' : {'duraciones':1, 'tiempo inicio':4  , 'tiempo entrega':8,  'costo retraso':1},
#        'T2' : {'duraciones':5, 'tiempo inicio':1  , 'tiempo entrega':12, 'costo retraso':8},
#        'T3' : {'duraciones':1, 'tiempo inicio':2  , 'tiempo entrega':29, 'costo retraso':7},
#        'T4' : {'duraciones':2, 'tiempo inicio':3  , 'tiempo entrega':15, 'costo retraso':5},
#        'T5' : {'duraciones':1, 'tiempo inicio':5  , 'tiempo entrega':28, 'costo retraso':3},
#        'T6' : {'duraciones':7, 'tiempo inicio':10 , 'tiempo entrega':19, 'costo retraso':1},
#        'T7' : {'duraciones':3, 'tiempo inicio':6  , 'tiempo entrega':15, 'costo retraso':9},
#        'T8' : {'duraciones':2, 'tiempo inicio':8  , 'tiempo entrega':9,  'costo retraso':4}}
#importancias = pd.DataFrame([0.05,0.30,0.15,0.1,0.1,0.1,0.1,0.1], index=list(tareas.keys()))
#rs = ReglasSecuenciacion(tareas, importancias)
#print(rs.TiempoProcesamientoCorto())
#print(rs.TiempoProcesamientoLargo())
#print(rs.TiempoFinalizacionTemprano())
#print(rs.TiempoFinalizacionTardio())
#print(rs.RelacionProcesameintoEntregaCorto())
#print(rs.RelacionProcesameintoEntregaLargo())
#print(rs.CostoRestrasoAlto())
#for nom, val in rs.ReglasSecuenciacion().items():
#    print(nom, '\n', val)
#print(rs.MetricasGeneralesSecuenciacion())
#print(rs.GraficarMetricas())
