import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional, Union
from pulp import *
import matplotlib.pyplot as plt
import gurobipy as grb
import os

class PlaneacionAgregada():
    def __init__ (self):
        pass

    def CrearExcel(self, numero_prodcutos: int = 2, periodos: list = True, ruta_excel : str = True):
        # Verificar nombres periodos
        if periodos==True:
            self.periodos = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
                             'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        else:
            self.periodos = periodos
        # Verificar ruta excel
        if ruta_excel==True:
            self.ruta_excel_datos_iniciales = str(os.getcwd()).replace('\\','/')+'/Base GOUD Modelo Planeacion Agregada.xlsx'
        else:
            if ruta_excel[-5::] == '.xlsx':
                self.ruta_excel_datos_iniciales = ruta_excel
            else:
                raise 'Ruta no valida, no contiene la extension del archivo (<Nombre>.xlsx)'
        # Crear DataFrame datos unicos
        columnas = ['Dias produccion(Dias)', 'Turnos dia(Turno/Dia)', 'Horas turno(Horas/Turno)',
                    'Costo contratar(Costo/Operario)', 'Costo despedir(Costo/Operario)', 
                    'Max Operarios contratar(Operario)', 'Max Operarios despedir(Operario)', 
                    'Costo normal(Costo/Hora)']
        unicos = pd.DataFrame(index=self.periodos, columns=columnas)
        unicos.to_excel(self.ruta_excel_datos_iniciales, sheet_name='Datos planeacion')
        # Crear DataFrames datos prodcutos
        columnas = ['Demanda pronosticada(Unidad)', 'Tiempo normal produccion(Hora/Unidad)', 
                    'Costo extra(Costo/Hora)', 'Costo subcontratar(Costo/Unidad)', 
                    'Capacidad subcontratar(Unidad/Periodo)', 'Costo inventario(Costo/Unidad)', 
                    'Capacidad inventario(Unidad/Periodo)']
        producto = pd.DataFrame(index=self.periodos, columns=columnas)
        # Agregar DataFrames prodcutos a excel
        for n in range(1,numero_prodcutos+1):
            with pd.ExcelWriter(self.ruta_excel_datos_iniciales, engine='openpyxl', mode='a') as writer:
                producto.to_excel(writer, sheet_name=str('Producto '+str(n)))
        return '\nExcel creado exitosamente en al ruta...\n(Puede ser remplazado arhcivo con el mismo nombre)\n'

    def CargarDatosExcel(self, ruta_excel: str, hoja_datos_planeacion: str = 'Datos planeacion', porcen_ampli_tiem_extra: float = 0.25,
                        operarios_iniciales: int = 1, inventario_inicial : Union[List, Tuple, Dict] = None):
        # Cargar datos de Excel
        excel = pd.ExcelFile(ruta_excel)
        self.productos = list(excel.sheet_names)
        self.productos.remove(hoja_datos_planeacion)
        self.df_planeacion = pd.read_excel(ruta_excel, index_col=0, sheet_name=hoja_datos_planeacion)
        self.periodos = list(self.df_planeacion.index)
        self.df_producto = {}
        for producto in self.productos:
            self.df_producto[producto] = pd.read_excel(ruta_excel, index_col=0, sheet_name=producto)
        # Crear variables unicas
        self.operarios_iniciales = operarios_iniciales
        self.p_t_extra = porcen_ampli_tiem_extra
        if inventario_inicial == None:
            self.inventario_inicial = dict(zip([pr for pr in self.productos],[0 for pr in self.productos]))
        else:
            if isinstance(inventario_inicial, (list, tuple)):
                if len(inventario_inicial) == len(self.productos):
                    self.inventario_inicial = dict(zip([pr for pr in self.productos],list(inventario_inicial)))
                else:
                    raise TypeError("La cantidad de datos suministrados no corresponde a la cantidad de prodcutos.")
            elif isinstance(inventario_inicial, (dict)):
                self.inventario_inicial = inventario_inicial
            else:
                raise TypeError("El tipo de datos ingresado no es válido.")

    # Crear variables generales para modelo de progrmación lineal
    def CrearVariablesModelo(self):
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
                                           lowBound=0, cat='Continuos')

    # Restriciones basicas de modelo de planeación agregada completo
    def RestriccionesDemanda(self):
        for pr in self.productos:
            unidades = self.inventario_inicial[pr] - self.Inventario[pr,self.periodos[0]]
            unidades += self.ProduccionNor[pr,self.periodos[0]] + self.ProduccionExt[pr,self.periodos[0]]
            unidades += self.ProduccionSub[pr,self.periodos[0]] 
            self.modelo += unidades == self.df_producto[pr].loc[self.periodos[0], 'Demanda pronosticada(Unidad)']
            for i, pe in enumerate(self.periodos[1::]):
                unidades = self.Inventario[pr,self.periodos[i]] - self.Inventario[pr,pe]
                unidades += self.ProduccionNor[pr,pe] + self.ProduccionExt[pr,pe] + self.ProduccionSub[pr,pe] 
                self.modelo += unidades == self.df_producto[pr].loc[pe, 'Demanda pronosticada(Unidad)']

    def RestriccionesBalanceOperarios(self):
        self.modelo += self.Ope[self.periodos[0]] == self.operarios_iniciales + self.OpeCon[self.periodos[0]] - self.OpeDes[self.periodos[0]]
        for i, pe in enumerate(self.periodos[1::]):
            self.modelo += self.Ope[pe] == self.Ope[self.periodos[i]] + self.OpeCon[pe] - self.OpeDes[pe]

    def RestriccionesContratacionOperarios(self):
        for pe in self.periodos:
            self.modelo += self.OpeCon[pe] <= self.df_planeacion.loc[pe,'Max Operarios contratar(Operario)']

    def RestriccionesDespidoOperarios(self):
        for pe in self.periodos:
            self.modelo += self.OpeCon[pe] <= self.df_planeacion.loc[pe,'Max Operarios despedir(Operario)']

    def RestriccionesTiempoNormal(self):
        for pe in self.periodos:
            capacidad = self.df_planeacion.loc[pe,'Dias produccion(Dias)'] * self.df_planeacion.loc[pe,'Turnos dia(Turno/Dia)']
            capacidad *= self.df_planeacion.loc[pe,'Horas turno(Horas/Turno)'] * self.Ope[pe]
            self.modelo += lpSum(self.ProduccionNor[pr,pe] * self.df_producto[pr].loc[pe,'Tiempo normal produccion(Hora/Unidad)'] for pr in self.productos) <= capacidad 
    
    def RestriccionesTiempoExtra(self):
        for pe in self.periodos:
            capacidad = self.df_planeacion.loc[pe,'Dias produccion(Dias)'] * self.df_planeacion.loc[pe,'Turnos dia(Turno/Dia)']
            capacidad *= self.df_planeacion.loc[pe,'Horas turno(Horas/Turno)'] * self.Ope[pe] * self.p_t_extra
            self.modelo += lpSum(self.ProduccionExt[pr,pe] * self.df_producto[pr].loc[pe,'Tiempo normal produccion(Hora/Unidad)'] for pr in self.productos) <= capacidad 

    def RestriccionesMaximasSubcontratacion(self):
        for pr in self.productos:
            for pe in self.periodos:
                self.modelo += self.ProduccionSub[pr,pe] <= self.df_producto[pr].loc[pe,'Capacidad subcontratar(Unidad/Periodo)']
    
    # Restriciones generación de modelos de planeación agregada
    def RestriccionManoObraConstante(self):
        for pe in self.periodos:
            self.modelo += self.OpeCon[pe] == 0
            self.modelo += self.OpeDes[pe] == 0

    def RestriccionInventarioCero(self):
        for pr in self.productos:
            for pe in self.periodos:
                self.modelo += self.Inventario[pr,pe] == 0

    def RestriccionTiempoSuplementario(self):
        for pr in self.productos:
            for pe in self.periodos:
                self.modelo += self.ProduccionExt[pr,pe] == 0

    def RestriccionSubcontratar(self):
        for pr in self.productos:
            for pe in self.periodos:
                self.modelo += self.ProduccionSub[pr,pe] == 0
    
    # Compilación de modelo especifico de planeación agregada
    def CompilarModelo(self, res_demanda = True, res_balanceo_operarios = True, res_contratacion_operarios = True,
                              res_despido_operarios = True, res_unidades_t_normal = True, res_unidades_t_extra = True, 
                              res_unidades_maximas_subcontratacion = True, res_mano_obra_constante = False, res_inventario_cero = False,
                              res_subcontratacion = False, res_tiempo_suplementario = False):
        self.CrearVariablesModelo()
        if res_demanda:
            self.RestriccionesDemanda()
        if res_balanceo_operarios:
            self.RestriccionesBalanceOperarios()
        if res_contratacion_operarios:
            self.RestriccionesContratacionOperarios()
        if res_despido_operarios:
            self.RestriccionesDespidoOperarios()
        if res_unidades_t_normal:
            self.RestriccionesTiempoNormal()
        if res_unidades_t_extra:
            self.RestriccionesTiempoExtra()
        if res_unidades_maximas_subcontratacion:
            self.RestriccionesMaximasSubcontratacion()
        # Restricciones de modelos
        if res_mano_obra_constante:
            self.RestriccionManoObraConstante()
        if res_inventario_cero:
            self.RestriccionInventarioCero()
        if res_tiempo_suplementario:
            self.RestriccionTiempoSuplementario()
        if res_subcontratacion:
            self.RestriccionSubcontratar()
        # Generar función objetivo
        objetivo = 0
        for pr in self.productos:
            # Costos tiempo normal
            objetivo += lpSum(self.df_planeacion.loc[pe,'Dias produccion(Dias)'] * self.df_planeacion.loc[pe,'Turnos dia(Turno/Dia)'] *
                                self.df_planeacion.loc[pe,'Horas turno(Horas/Turno)'] * self.Ope[pe] * 
                                self.df_planeacion.loc[pe,'Costo normal(Costo/Hora)'] for pe in self.periodos)
            # Costos tiempo extra
            objetivo += lpSum(self.ProduccionExt[pr,pe] * self.df_producto[pr].loc[pe,'Costo extra(Costo/Hora)']*
                              self.df_producto[pr].loc[pe,'Tiempo normal produccion(Hora/Unidad)'] for pe in self.periodos)
            # Costos subcontratacion
            objetivo += lpSum(self.ProduccionSub[pr,pe] * self.df_producto[pr].loc[pe,'Costo subcontratar(Costo/Unidad)'] for pe in self.periodos)
            # Costos inventario
            objetivo += lpSum(self.Inventario[pr,pe] * self.df_producto[pr].loc[pe,'Costo inventario(Costo/Unidad)'] for pe in self.periodos)
        # Costo contratar
        objetivo += lpSum(self.OpeCon[pe] * self.df_planeacion.loc[pe,'Costo contratar(Costo/Operario)'] for pe in self.periodos)
        # Costo despedir 'Costo contratar(Costo/Operario)', 'Costo despedir(Costo/Operario)'
        objetivo += lpSum(self.OpeDes[pe] * self.df_planeacion.loc[pe,'Costo despedir(Costo/Operario)'] for pe in self.periodos)
        self.modelo += objetivo 
    
    # Generar infrome de unidades compilado
    def GenerarInformeUnidades(self):
        self.UnidadesGeneralResultado = pd.DataFrame(index=self.periodos)
        self.UnidadesProductosResultado = {producto: pd.DataFrame(index=self.periodos) for producto in self.productos}
        for var in self.modelo.variables():
            if str(var)[-1] == ')':
                var_name = str(var).replace('_', ' ').replace("'", '').replace("(", ',').replace(")", '').replace(",", ' ')
                nombre_auxiliar = var_name.split('  ')
            else:
                var_name = str(var).replace('_', ' ')
                nombre_auxiliar = var_name.split(' ')
            # Agregar a DataFrame correspondiente
            if len(nombre_auxiliar)==3:
                if nombre_auxiliar[1] in self.productos:
                    self.UnidadesProductosResultado[nombre_auxiliar[1]].loc[nombre_auxiliar[2],nombre_auxiliar[0]] = 0 if var.varValue <= 0 else round(var.varValue,2)
            else:
                self.UnidadesGeneralResultado.loc[nombre_auxiliar[1],nombre_auxiliar[0]] = round(var.varValue,2)

    # Generar infrome de costos compilado
    def GenerarInformeCostos(self):
        base = pd.DataFrame([], index = self.periodos)
        # Crear DataFrames de costos generales
        self.CostosGeneralResultado = base.copy()
        self.CostosGeneralResultado['Costo de contratación operarios'] = self.UnidadesGeneralResultado['OperariosContratados']*self.df_planeacion['Costo contratar(Costo/Operario)']
        self.CostosGeneralResultado['Costo despido operarios'] = self.UnidadesGeneralResultado['OperariosDespedidos']*self.df_planeacion['Costo despedir(Costo/Operario)']
        self.CostosGeneralResultado['Salario constante'] = self.UnidadesGeneralResultado['OperariosDespedidos']*0
        # Crear diccioanrio de DataFrames costos por productos
        self.CostosProductosResultado = {}
        for pr in self.productos:
            self.CostosProductosResultado[pr] = base.copy()
            self.CostosProductosResultado[pr]['Costo mantenimiento inventario'] = self.UnidadesProductosResultado[pr]['Inventario'] * self.df_producto[pr]['Costo inventario(Costo/Unidad)']
            self.CostosProductosResultado[pr]['Costo producción tiempo normal'] = self.UnidadesProductosResultado[pr]['ProduccionNormal'] * self.df_planeacion['Costo normal(Costo/Hora)'] * self.df_producto[pr]['Tiempo normal produccion(Hora/Unidad)']
            self.CostosProductosResultado[pr]['Costo producción tiempo extra'] = self.UnidadesProductosResultado[pr]['ProduccionExtra'] * self.df_producto[pr]['Costo extra(Costo/Hora)'] * self.df_producto[pr]['Tiempo normal produccion(Hora/Unidad)']
            self.CostosProductosResultado[pr]['Costo subcontratación'] = self.UnidadesProductosResultado[pr]['ProduccionSubcontratacion'] * self.df_producto[pr]['Costo subcontratar(Costo/Unidad)']
        return self.CostosGeneralResultado, self.CostosProductosResultado

    # Solucionar modelo de progrmación lineal de planeación agregada
    def SolucionarModelo(self, excel = False):
        self.modelo.solve( solver = GUROBI())
        #self.modelo.solve( )
        if LpStatus[self.modelo.status] != 'Optimal':
            raise ValueError('Modelo en estado: '+LpStatus[self.modelo.status])
        else:
            self.GenerarInformeUnidades()
            self.GenerarInformeCostos()
            if excel == True:
                self.ruta_excel_resultado = str(os.getcwd()).replace('\\','/')+'/Resultado Modelo Planeacion Agregada.xlsx'
                self.UnidadesGeneralResultado.to_excel(self.ruta_excel_resultado, sheet_name='Und General')
                with pd.ExcelWriter(self.ruta_excel_resultado, engine='openpyxl', mode='a') as writer:
                    self.CostosGeneralResultado.to_excel(writer, sheet_name='Cos General')
                # Agregar DataFrames prodcutos a excel
                for pr in self.productos:
                    with pd.ExcelWriter(self.ruta_excel_resultado, engine='openpyxl', mode='a') as writer:
                        self.UnidadesProductosResultado[pr].to_excel(writer, sheet_name = 'Und '+pr)
                        self.CostosProductosResultado[pr].to_excel(writer, sheet_name = 'Cos '+pr)
                print('\nExcel creado exitosamente en al ruta...\n(Puede ser remplazado arhcivo con el mismo nombre)\n')
        return self.UnidadesGeneralResultado, self.UnidadesProductosResultado, self.CostosGeneralResultado, self.CostosProductosResultado
            
    # Graficar valores de unidades estimados por modelo
    def GraficarUnidades(self):
        # Agregar barras apiladas de cada columna
        ax = self.UnidadesGeneralResultado.plot(kind='bar', width=0.6)
        # Agregar la línea de la suma de cada fila
        self.UnidadesGeneralResultado.T.sum().plot(kind='line', ax=ax, color='grey')
        ax.set_title('Cantidades generales')
        for pr in self.UnidadesProductosResultado.keys():
            # Agregar barras apiladas de cada columna
            ax = self.UnidadesProductosResultado[pr].plot(kind='bar', width=0.6)
            # Agregar la línea de la suma de cada fila
            self.UnidadesProductosResultado[pr].T.sum().plot(kind='line', ax=ax, color='grey')
            plt.title('Cantidades de '+pr)
        plt.show()

    # Graficar costos estimados por modelo
    def GraficarCostos(self):
        # Agregar barras apiladas de cada columna
        ax = self.CostosGeneralResultado.plot(kind='bar', width=0.6)
        # Agregar la línea de la suma de cada fila
        self.CostosGeneralResultado.T.sum().plot(kind='line', ax=ax, color='grey')
        ax.set_title('Costos generales')
        for pr in self.CostosProductosResultado.keys():
            # Agregar barras apiladas de cada columna
            ax = self.CostosProductosResultado[pr].plot(kind='bar', width=0.6)
            # Agregar la línea de la suma de cada fila
            self.CostosProductosResultado[pr].T.sum().plot(kind='line', ax=ax, color='grey')
            plt.title('Costos de '+pr)
        plt.show()


modelo = PlaneacionAgregada()
modelo.CrearExcel(periodos = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio'])
modelo.CargarDatosExcel('Base GOUD Modelo Planeacion Agregada.xlsx', 'Datos planeacion', operarios_iniciales=9, porcen_ampli_tiem_extra = 0.3)
modelo.CompilarModelo(res_mano_obra_constante = False, res_inventario_cero = False, res_subcontratacion = False, res_tiempo_suplementario = False)
var1, var2, var3, var4 = modelo.SolucionarModelo(excel=True)
modelo.GraficarCostos()
modelo.GraficarUnidades()


print('-'*150)
print(var1)
print('-'*150)
for pr in var2.keys():
    print(var2[pr])

print('-'*150)
print(var3)
print('-'*150)
for pr in var4.keys():
    print(var4[pr])