import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Union
from pulp import *
import matplotlib.pyplot as plt
import os

class PlaneacionAgregada():
    def   init  (self):
        pass

    def CrearExcel(self, numero_prodcutos: int = 2, periodos: list = True, 
                   porcen_ampli_tiem_extra: float = 0.25,
                   operarios_iniciales: int = 1, ruta_excel : str = True):
        # Verificar nombres periodos
        if periodos==True:
            self.periodos = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
                             'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        else:
            self.periodos = periodos
        # Verificar ruta excel
        if ruta_excel:
            self.ruta_excel = str(os.getcwd()).replace('\\','/')+'/Base GOUD Modelo Planeacion Agregada.xlsx'
        else:
            if ruta_excel[-5::] == '.xlsx':
                self.ruta_excel = ruta_excel
            else:
                raise 'Ruta no valida, no contiene la extension del archivo (<Nombre>.xlsx)'
        self.operarios_iniciales = operarios_iniciales
        self.p_t_extra = porcen_ampli_tiem_extra
        # Crear DataFrame datos unicos
        columnas = ['Dias produccion(Dias)', 'Turnos dia(Turno/Dia)', 'Horas turno(Horas/Turno)',
                    'Costo contratar(Costo/Operario)', 'Costo despedir(Costo/Operario)', 
                    'Max Operarios contratar(Operario)', 'Max Operarios despedir(Operario)', 
                    'Costo normal(Costo/Hora)']
        unicos = pd.DataFrame(index=self.periodos, columns=columnas)
        unicos.to_excel(self.ruta_excel, sheet_name='Datos planeacion')
        # Crear DataFrames datos prodcutos
        columnas = ['Demanda pronosticada(Unidad)', 'Tiempo normal produccion(Hora/Unidad)', 'Costo extra(Costo/Hora)',
                    'Costo subcontratar(Costo/Unidad)', 'Capacidad subcontratar(Unidad/Periodo)', 'Costo inventario(Costo/Unidad)', 'Capacidad inventario(Unidad/Periodo)']
        producto = pd.DataFrame(index=self.periodos, columns=columnas)
        # Agregar DataFrames prodcutos a excel
        for n in range(1,numero_prodcutos+1):
            with pd.ExcelWriter(self.ruta_excel, engine='openpyxl', mode='a') as writer:
                producto.to_excel(writer, sheet_name=str('Producto '+str(n)))
        return '\nExcel creado exitosamente en al ruta...\n(Puede ser remplazado arhcivo con el mismo nombre)\n'

    def CargarDatosExcel(self, ruta_excel: str, hoja_datos_planeacion: str ):
        excel = pd.ExcelFile(ruta_excel)
        self.productos = list(excel.sheet_names)
        self.productos.remove(hoja_datos_planeacion)
        self.df_datos_planeacion = pd.read_excel(ruta_excel, index_col=0, sheet_name=hoja_datos_planeacion)
        self.df_producto = {}
        for producto in self.productos:
            self.df_producto[producto] = pd.read_excel(ruta_excel, index_col=0, sheet_name=producto)

    def Modelo(self, inventario = True, horas_extra = True, subcontratacion = True, contratacion_despido = True):
        self.modelo = LpProblem("Modelo Planeacion Agregada", sense=LpMinimize)
        self.OpeCon = LpVariable.dicts("OperariosContratados", self.periodos , lowBound=0, cat='Integer')
        self.OpeDes = LpVariable.dicts("OperariosDespedidos", self.periodos , lowBound=0, cat='Integer')
        self.Ope = LpVariable.dicts("Operarios", self.periodos , lowBound=0, cat='Integer')
        self.ProduccionNor = LpVariable.dicts("ProduccionNormal", ((pr, pe) for pe in self.periodos for pr in self.productos) ,
                                                 lowBound=0, cat='Continuos')
        self.ProduccionExt = LpVariable.dicts("ProduccionExtra", ((pr, pe) for pe in self.periodos for pr in self.productos) , 
                                                lowBound=0, cat='Continuos')
        self.ProduccionSub = LpVariable.dicts("ProduccionSubcontratacion", ((pr, pe) for pe in self.periodos for pr in self.productos) ,
                                                          lowBound=0, cat='Integer')
        self.Inventario = LpVariable.dicts("Inventario", ((pr, pe) for pe in self.periodos for pr in self.productos) , 
                                           lowBound=0, cat='Integer')
        self.ResBalanceOperarios()

    def ResBalanceOperarios(self):
        self.modelo += self.Ope[self.periodos[0]] == self.operarios_iniciales + self.OpeCon[self.periodos[0]] - self.OpeDes[self.periodos[0]]
        for i, pe in enumerate(self.periodos[1::]):
            self.modelo += self.Ope[pe] == self.Ope[self.periodos[i]] + self.OpeCon[pe] - self.OpeDes[pe]



    #def RestriccionesTiempoNormal(self):
    #    for pe in self.periodos:
    #        self.modelo += lpSum(self.ProduccionNormal[pr,pe] for pr in self.productos) <= 

modelo = PlaneacionAgregada()
#print(modelo.CrearExcel(periodos = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio']))
modelo.CargarDatosExcel('Base GOUD Modelo Planeacion Agregada.xlsx', 'Datos planeacion')
print(modelo.df_producto['Producto 1'])