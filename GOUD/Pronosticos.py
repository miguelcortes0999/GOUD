import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Union
import matplotlib.pyplot as plt

class PromedioMovil():
    '''
    PromedioMovil(datos(df,list,tuple), periodos_promediados:int, periodos:int(1))\n
    Calcula el promedio móvil simple de una serie de datos.\n
    Argumentos:\n
    datos : List, Tuple, pd.DataFrame
        Una lista, tupla o DataFrame con los datos de la serie.
    periodos_promediados: un entero que indica el tamaño de la periodos_promediados de promedio móvil.\n
    Ejemplo:\n
        pm = PromedioMovil(df)
        print(pm.Calcular())
        print(pm.Pronosticar(horizonte_pronostico=5))
    '''
    def __init__(self, datos: Union[List, Tuple, pd.DataFrame], periodos_promediados: int = 2):
        self.datos = datos
        self.periodos_promediados = periodos_promediados
        self.nombre_modelo = 'Promedio movil'

    # Calcular histórico
    def Calcular(self):
        # Comprobar el tipo de dato de usuario
        if isinstance(self.datos, pd.DataFrame):
            self.historico = self.datos.copy()
        elif isinstance(self.datos, (list, tuple)):
            self.historico = pd.DataFrame(self.datos)
        else:
            raise TypeError("El tipo de datos ingresado no es válido.")
        # Calcular el promedio movil el numero suministrado
        pronostico = self.historico.copy()
        pronostico.iloc[:,0] = pronostico.iloc[:,0].shift(1).rolling(window=self.periodos_promediados ,
                                                                    min_periods=self.periodos_promediados ).mean()
        # Devolver el resultado
        self.pronostico = pronostico.copy()
        self.pronostico_historico = pronostico.copy()
        self.titulo_grafico = f'Promedio móvil (Periodos promediados={self.periodos_promediados})'
        return self.pronostico_historico

    # Calcular pronóstico
    def Pronosticar(self, horizonte_pronostico: int = 1):
        self.pronostico_periodos = horizonte_pronostico
        # Agregar pronsoticos
        n = len(self.pronostico_historico)
        for i in range(self.pronostico_periodos):
            self.pronostico.loc[n+i,0] = np.mean(list(self.pronostico.iloc[:,0])[-self.periodos_promediados::])
        self.pronostico = self.pronostico[self.pronostico.index > self.pronostico_historico.index.max()]
        return self.pronostico

class PromedioMovilPonderado():
    '''
    PromedioMovilPonderado(datos(df,list,tuple), periodos_promediados:int, periodos:None, importancia_periodos:List[float] = None)\n
    Calcula el promedio móvil ponderado de una serie de datos.\n
    Argumentos:\n
    datos : List, Tuple, pd.DataFrame
        Una lista, tupla o DataFrame con los datos de la serie.
    periodos_promediados : int
        Un entero que indica el tamaño de la periodos_promediados de promedio móvil.
    importancia_periodos : List[float]
        Una lista opcional de flotantes que indica los importancia_periodos correspondientes a cada valor en la periodos_promediados.
        Si no se especifica, se utilizará un promedio móvil simple.\n
    Ejemplo:\n
        pmp = PromedioMovilPonderado(df, periodos_promediados=4, importancia_periodos=[0.1, 0.2, 0.3, 0.4])
        print(pmp.Calcular())
        print(pmp.Pronosticar(horizonte_pronostico=5))
    '''
    def __init__(self, datos: Union[List, Tuple, pd.DataFrame], periodos_promediados: int = None, importancia_periodos: List[float] = None):
        self.datos = datos
        # Comprobar el tipo de dato de usuario
        if isinstance(self.datos, pd.DataFrame):
            self.historico = self.datos.copy()
        elif isinstance(self.datos, (list, tuple)):
            self.historico = pd.DataFrame(self.datos)
        else:
            raise TypeError("El tipo de datos ingresado no es válido.")
        # Comprobación de longitudes y tamaños similares
        if periodos_promediados is None and importancia_periodos is None:
            raise TypeError("No ingreso importancia_periodos ni tamaño de la periodos_promediados válido.")
        if periodos_promediados is not None and importancia_periodos is not None:
            if periodos_promediados != len(importancia_periodos):
                raise TypeError("Tamaño de importancia_periodos y periodos_promediados distintos.")
            else:
                self.periodos_promediados = periodos_promediados  
                self.importancia_periodos = importancia_periodos 
        else:
            if periodos_promediados is None:
                if sum(importancia_periodos)!=1:
                    raise TypeError("Suma de los importancia_periodos es diferente de 1.")
                self.periodos_promediados = len(importancia_periodos)
                self.importancia_periodos = importancia_periodos 
            if importancia_periodos is None:
                if periodos_promediados<1:
                    raise TypeError("La periodos_promediados no es posible, debe ser >= 1.")
                if periodos_promediados>len(datos):
                    raise TypeError("La periodos_promediados es mas grande que los datos historicos.")
                self.periodos_promediados = periodos_promediados
                self.importancia_periodos = [1/periodos_promediados]*periodos_promediados
        self.nombre_modelo = 'Promedio movil ponderado'
    
    # Calcular histórico
    def Calcular(self):            
        # Calcular el promedio móvil ponderado para el número de periodos suministrados
        pronostico_pmp = np.array(self.historico.iloc[:, 0])[0:self.periodos_promediados]
        vector_importancia_periodos = np.array(self.importancia_periodos)
        for i in range(self.periodos_promediados, len(self.historico)):
            vector_historico = np.array(self.historico.iloc[:, 0])[i-self.periodos_promediados:i]
            producto_punto = np.dot(vector_historico, vector_importancia_periodos)
            pronostico_pmp = np.append(pronostico_pmp, producto_punto)
        pronostico_pmp = [None for _ in range(self.periodos_promediados)] + list(pronostico_pmp[self.periodos_promediados::])
        self.pronostico_historico = pd.DataFrame(pronostico_pmp)
        self.titulo_grafico = f'Promedio móvil ponderado (importancia_periodos={self.importancia_periodos})'
        return self.pronostico_historico
    
    # Calcular pronóstico
    def Pronosticar(self, horizonte_pronostico: int=1):
        self.pronostico = self.historico.iloc[-self.periodos_promediados::,:]
        pronostico_pmp = np.array(self.historico.iloc[:, 0])[-self.periodos_promediados::]
        vector_importancia_periodos = np.array(self.importancia_periodos)
        for i in range(self.periodos_promediados, self.periodos_promediados+horizonte_pronostico):
            vector_pronostico = pronostico_pmp[i-self.periodos_promediados:i]
            producto_punto = np.dot(vector_pronostico, vector_importancia_periodos)
            pronostico_pmp = np.append(pronostico_pmp, producto_punto)
        self.pronostico = pd.DataFrame(pronostico_pmp, columns=[0])
        self.pronostico = self.pronostico.iloc[self.periodos_promediados::,:]
        self.pronostico.index = [i for i in range(len(self.historico), len(self.historico)+horizonte_pronostico)]
        return self.pronostico

class RegresionLinealSimple():
    '''
    RegresionLienalSimple(datos(df,list,tuple))\n
    Calcula la regresion lineal para una serie de datos.\n
    Argumentos:\n
    datos : List, Tuple, pd.DataFrame
        Una lista, tupla o DataFrame con los datos de la serie (el inidce del data frame sera tomado como eje x).\n
    Ejemplo:\n
        reg = RegresionLinealSimple(df)
        print(reg.Calcular())
        print(reg.Ecuacion())
        print(reg.Pronosticar([25,26,28,29,30]))
    '''
    def __init__(self, datos: Union[List, Tuple, pd.DataFrame]):
        self.datos = datos
        # Comprobar el tipo de dato de usuario
        if isinstance(self.datos, pd.DataFrame):
            self.historico = self.datos.copy()
        elif isinstance(self.datos, (list, tuple)):
            self.historico = pd.DataFrame(self.datos)
        else:
            raise TypeError("El tipo de datos ingresado no es válido.")
        self.x = np.array(list(self.historico.index))
        self.y = np.array(list(self.historico.iloc[:,0]))
        self.titulo_grafico = 'Regresión lineal simple'
        self.nombre_modelo = 'Regresion lineal'
    
    # Calcular histórico
    def Calcular(self):
        self.b = None
        self.m = None
        x_mean = np.mean(self.x)
        y_mean = np.mean(self.y)
        s_xy = np.sum((self.x - x_mean) * (self.y - y_mean))
        s_xx = np.sum((self.x - x_mean) ** 2)
        self.m = s_xy / s_xx
        self.b = y_mean - (self.m * x_mean)
        self.pronostico_historico = pd.DataFrame(index=self.x)
        for x in self.pronostico_historico.index:
            self.pronostico_historico.loc[x,0] = self.b + self.m * x
        return self.pronostico_historico
    
    # Calcular pronóstico
    def Pronosticar(self, x_nuevos: np.array):
        for i in x_nuevos:
            if i < 0:
                raise ValueError("Valor negativo ingresado, no se admiten valores negativos.")
        if self.b is None or self.m is None:
            raise ValueError("La regresión aún no se ha calculado.")
        resultado = pd.DataFrame([None for x in x_nuevos],index=x_nuevos)
        for xs in x_nuevos:
            resultado.loc[xs,0] = self.b + self.m * xs
        self.pronostico = resultado
        return self.pronostico

    # Retornar ecuación
    def Ecuacion(self):
        return {'m':self.m, 'b':self.b}

class SuavizacionExponencialSimple():
    '''
    SuavizacionExponencialSimple(datos(df,list,tuple), alfa:float, nivel_inicial:float)\n
    Clase que implementa el modelo de suavización exponencial simple para horizonte_pronostico valores futuros de una serie temporal.\n
    Argumentos:\n
    datos : List, Tuple, pd.DataFrame 
        Serie temporal de datos.
    alfa : float
        Parámetro de suavización para la serie.
    nivel_inicial : float 
        Valor inicial para la serie.\n
    Ejemplo:\n
        ses = SuavizacionExponencialSimple(df, alfa=0.2)
        print(ses.Calcular())
        print(ses.Pronosticar(horizonte_pronostico=5))
    '''
    def __init__(self, datos: Union[List, Tuple, pd.DataFrame], alfa: float = None, nivel_inicial: float = None):
        self.datos = datos
        # Comprobar el tipo de dato de usuario
        if isinstance(self.datos, pd.DataFrame):
            self.historico = self.datos.copy()
        elif isinstance(self.datos, (list, tuple)):
            self.historico = pd.DataFrame(self.datos)
        else:
            raise TypeError("El tipo de datos ingresado no es válido.")
        self.x = self.historico.index
        self.alfa = alfa
        self.nivel_inicial = nivel_inicial
        self.resultado = None
        if self.alfa is None:
            self.alfa = 2/(len(self.datos)+1)
        elif self.alfa < 0 or self.alfa > 1:
            raise TypeError("El valor de alfa debe estar entre 0 y 1.")
        self.nombre_modelo = 'Suvizacion exponencial simple'

    # Calcular histórico
    def Calcular(self):
        # Inicializar la suavización exponencial simple
        if self.nivel_inicial is not None :
            nivel_t = self.nivel_inicial
        else:
            nivel_t = self.historico.iloc[0,0]
        self.nivel_inicial = nivel_t
        # Calcular la suavización exponencial simple para el número de periodos suministrados
        self.se_simple = [self.nivel_inicial]
        for i in range(len(self.historico)-1):
            nivel_t_1 = nivel_t
            nivel_t = self.alfa * self.historico.iloc[i,0] + (1-self.alfa) * nivel_t_1
            self.se_simple.append(nivel_t)
        self.pronostico_historico = pd.DataFrame(self.se_simple)
        self.titulo_grafico = f'Suavizacion Exponencial Simple (Alfa={self.alfa} y Niv. inicial={self.nivel_inicial})'
        return self.pronostico_historico

    # Calcular pronóstico 
    def Pronosticar(self, horizonte_pronostico: int = 1):
        self.se_simple_pronosticado = [self.se_simple[-1]]
        indice = []
        for i in range(len(self.historico), len(self.historico)+horizonte_pronostico):
            indice.append(i)
            nivel_t_1 = self.se_simple_pronosticado[-1]
            nivel_t = self.alfa * self.historico.iloc[len(self.historico)-1,0] + (1-self.alfa) * nivel_t_1
            self.se_simple_pronosticado.append(nivel_t)
        self.pronostico = pd.DataFrame(self.se_simple_pronosticado[1::], index=indice)
        return self.pronostico

class SuavizacionExponencialDoble():
    '''
    SuavizacionExponencialDoble(datos(df,list,tuple), alfa:float, beta:float, tendencia_inicial:float, nivel_inicial:float)\n
    Clase que implementa el modelo de suavización exponencial doble para horizonte_pronostico valores futuros de una serie temporal.\n
    Argumentos:\n
    datos : List, Tuple, pd.DataFrame
        Serie temporal de datos.
    alfa : float)
        Parámetro de suavización para el nivel de la serie.
    beta : float
        Parámetro de suavización para la tendencia de la serie.
    nivel_inicial : float
        Valor inicial para el nivel de la serie.
    tendencia_inicial : float
        Valor inicial para la tendencia de la serie.\n
    Ejemplo:\n
        sed = SuavizacionExponencialDoble(df, alfa=0.8, beta=0.5, nivel_inicial=4, tendencia_inicial=2)\n
        print(sed.Calcular())\n
        print(sed.Pronosticar(horizonte_pronostico=5))\n
    '''
    def __init__(self, datos: Union[List, Tuple, pd.DataFrame], alfa: float = None, beta: float = None,
                nivel_inicial: float = None, tendencia_inicial: float = None):
        self.datos = datos
        # Comprobar el tipo de dato de usuario
        if isinstance(self.datos, pd.DataFrame):
            self.historico = self.datos.copy()
        elif isinstance(self.datos, (list, tuple)):
            self.historico = pd.DataFrame(self.datos)
        else:
            raise TypeError("El tipo de datos ingresado no es válido.")
        self.x = self.historico.index
        self.alfa = alfa
        self.beta = beta
        self.nivel_inicial = nivel_inicial
        self.tendencia_inicial = tendencia_inicial
        self.resultado = None
        if self.alfa is None or self.beta is None:
            raise TypeError("No se ha especificado los valores de alfa y beta.")
        elif self.alfa < 0 or self.alfa > 1 or self.beta < 0 or self.beta > 1:
            raise TypeError("Los valores de alfa y beta deben estar entre 0 y 1.")
        self.nombre_modelo = 'Suvizacion exponencial doble'
    
    # Calcular histórico
    def Calcular(self):
        # Inicializar la suavización exponencial doble
        if self.nivel_inicial is not None :
            nivel_t = self.nivel_inicial
        else:
            nivel_t = self.historico.iloc[1,0]
        if self.tendencia_inicial is not None:
            tendencia_t = self.tendencia_inicial
        else:
            tendencia_t = self.historico.iloc[1,0] - self.historico.iloc[0,0]
        self.titulo_grafico = f'Suavización exponencial doble (Alfa={self.alfa}, Beta={self.beta}, Tend. inicial={self.tendencia_inicial} y  Niv. incial={self.nivel_inicial})'
        # Calcular la suavización exponencial doble para el número de periodos suministrados
        self.nivel = [nivel_t]
        self.tendencia = [tendencia_t]
        self.valores_pronostico = []
        self.nivel_inicial = nivel_t
        self.tendencia_inicial = tendencia_t
        for i in range(0, len(self.historico)):
            nivel_t = (self.alfa * self.historico.iloc[i,0]) + (1 - self.alfa) * (self.nivel[-1] + self.tendencia[-1])
            tendencia_t = self.beta * (nivel_t - self.nivel[-1]) + (1 - self.beta) * self.tendencia[-1]
            pronostico_sed = nivel_t + tendencia_t
            self.nivel.append(nivel_t)
            self.tendencia.append(tendencia_t)
            self.valores_pronostico.append(pronostico_sed)
        self.pronostico_historico = pd.DataFrame(self.valores_pronostico, index=self.x)
        self.pronostico_historico = self.pronostico_historico.head(len(self.historico))
        return self.pronostico_historico
    
    # Calcular pronóstico
    def Pronosticar(self, horizonte_pronostico: int = 1):
        self.periodos = horizonte_pronostico
        if self.nivel is None or self.tendencia is None:
            raise ValueError("La regresión aún no se ha calculado.")
        self.pronostico = self.pronostico_historico.copy()
        # Calcular los valores de la serie suavizada para los períodos futuros
        for i in range (2, horizonte_pronostico + 2):
            self.pronostico.loc[len(self.pronostico), 0] = self.nivel[-1] + i * self.tendencia[-1]
        self.pronostico = self.pronostico.tail(horizonte_pronostico)
        return self.pronostico

class SuavizacionExponencialTriple():
    '''
    SuavizacionExponencialTriple(datos(df,list,tuple), alfa:float, beta:float, gamma float, ciclo: int, tipo_nivel:'add' or 'mul', tipo_estacionalidad:'add' or 'mul',
    nivel_inicial=float, tendencia_inicial:float, estacionalidad_inicial: [float])\n
    Clase para implementar un modelo de suavización exponencial triple para la realización de pronósticos.\n
    Argumentos:\n
    datos : list, tuple, pd.DataFrame
        Datos para realizar el pronóstico. Puede ser una lista, tupla o DataFrame de pandas.
    alfa : float
        Parámetro de suavización para el nivel. Debe estar entre 0 y 1.
    beta : float
        Parámetro de suavización para la tendencia. Debe estar entre 0 y 1.
    gamma : float
        Parámetro de suavización para la estacionalidad. Debe estar entre 0 y 1.
    tipo_nivel : str, optional
        Tipo de suavización para el nivel, puede ser 'adi' para aditiva o 'mul' para multiplicativa.
        El valor por defecto es 'adi'.
    tipo_estacionalidad : str, optional
        Tipo de suavización para la estacionalidad, puede ser 'adi' para aditiva o 'mul' para multiplicativa.
        El valor por defecto es 'adi'.
    ciclo : int, optional
        Cantidad de períodos que conforman un ciclo estacional. Si no se especifica, se asume que el ciclo
        es la longitud de los datos. El valor por defecto es None.
    nivel_inicial : float, optional
        Valor inicial del nivel. Si no se especifica, se calcula automáticamente como el primer valor de los datos.
        El valor por defecto es None.
    tendencia_inicial : float, optional
        Valor inicial de la tendencia. Si no se especifica, se calcula automáticamente como la diferencia entre
        el segundo y el primer valor de los datos.
        El valor por defecto es None.
    estacionalidad_inicial : float, optional
        Valor inicial de la estacionalidad. Si no se especifica, se calcula automáticamente como la media de
        los valores de los datos en el primer ciclo.
        El valor por defecto es None.\n
    Ejemplo:\n
        set = SuavizacionExponencialTriple(df, alfa=0.9, beta=0.3, gamma=0.3, nivel_inicial=4, tendencia_inicial=2, tipo_nivel='mul', tipo_estacionalidad='mul')
        print(set.Calcular())
        print(set.Pronosticar(horizonte_pronostico=5))
    '''
    def __init__(self, datos: Union[List, Tuple, pd.DataFrame], alfa: float, beta: float, gamma: float,
                 tipo_nivel: str = 'adi', tipo_estacionalidad: str = 'adi', ciclo: int = None,
                 nivel_inicial: Optional[float] = None, tendencia_inicial: Optional[float] = None,
                 estacionalidad_inicial: Optional[float] = None):
        self.datos = datos
        # Comprobar el tipo de dato de usuario
        if isinstance(self.datos, pd.DataFrame):
            self.historico = self.datos.copy()
        elif isinstance(self.datos, (list, tuple)):
            self.historico = pd.DataFrame(self.datos)
        else:
            raise TypeError("El tipo de datos ingresado no es válido.")
        self.y = np.array(self.historico.iloc[:,0])
        self.x = np.array(self.historico.index)
        self.alfa = alfa
        self.beta = beta
        self.gamma = gamma
        self.nivel_inicial = nivel_inicial
        self.tendencia_inicial = tendencia_inicial
        self.estacionalidad_inicial = estacionalidad_inicial
        self.nivel = None
        self.tendencia = None
        self.estacionalidad = None
        self.m = 0
        self.tipo_nivel = tipo_nivel
        self.tipo_estacionalidad = tipo_estacionalidad
        if ciclo == None:
            self.ciclo = len(datos)
        else:
            if len(datos) % ciclo == 0:
                self.ciclo = ciclo
            else:
                raise ('No es posible agrupar los datos en la cantidad de ciclos suministrado.')
        self.nombre_modelo = 'Suvizacion exponencial triple'

    # Calcular histórico
    def Calcular(self):
        n = len(self.y)
        # Inicializar los valores de nivel, tendencia y estacionalidad
        nivel = []
        tendencia = []
        estacionalidad = [np.mean(self.y[i::self.ciclo]) / np.mean(self.y) for i in range(self.ciclo)] if self.estacionalidad_inicial is None else self.estacionalidad_inicial.copy()
        # Calcular los valores de nivel, tendencia y estacionalidad para cada período
        for i in range(n):
            # Calcular los valores suavizados
            if i == 0:
                nivel_actual = self.y[0] if self.nivel_inicial is None else self.nivel_inicial
                tendencia_actual = (self.y[1] - self.y[0]) if self.tendencia_inicial is None else self.tendencia_inicial
            else:
                if self.tipo_nivel == 'adi':
                    nivel_actual = self.alfa * (self.y[i] - estacionalidad[-self.ciclo]) + (1 - self.alfa) * (nivel[-1] + tendencia[-1]) 
                elif self.tipo_nivel == 'mul':
                    nivel_actual = self.alfa * (self.y[i] / estacionalidad[-self.ciclo]) + (1 - self.alfa) * (nivel[-1] + tendencia[-1])
                else:
                    raise TypeError('El tipo de nivel no es permitido, elija entre "adi" o "mul".')    
                tendencia_actual = self.beta * (nivel_actual - nivel[-1]) + (1 - self.beta) * tendencia[-1]
            if self.tipo_estacionalidad == 'adi':
                estacionalidad_actual = self.gamma * (self.y[i] - nivel_actual) + (1 - self.gamma) * estacionalidad[-self.ciclo]
            elif self.tipo_estacionalidad == 'mul':
                estacionalidad_actual = self.gamma * (self.y[i] / nivel_actual) + (1 - self.gamma) * estacionalidad[-self.ciclo] 
            else:
                raise TypeError('El tipo de estacionalidad no es permitido, elija entre "adi" o "mul".')      
            # Agregar los valores suavizados a las listas correspondientes
            nivel.append(nivel_actual)
            tendencia.append(tendencia_actual)
            estacionalidad.append(estacionalidad_actual)
        # Asignar valores iniciales para modelo
        self.nivel_inicial = nivel[0]
        self.tendencia_inicial = tendencia[0]
        self.estacionalidad_inicial = f"{estacionalidad[0]:.2f}"
        # Crear leyenda grafico
        self.titulo_grafico = f"Suavización exponencial triple (Alfa={self.alfa}, Beta={self.beta}, Gamma={self.gamma},Tend. inicial={self.tendencia_inicial}, Niv. incial={self.nivel_inicial}, Est. inicial={self.estacionalidad_inicial}, Tipo Nivel={self.tipo_nivel} y Tipo Estacionalidad={self.tipo_estacionalidad})"
        # Guardar los valores de nivel, tendencia y estacionalidad como atributos de la clase
        self.nivel = np.array(nivel)
        self.tendencia = np.array(tendencia)
        self.estacionalidad = np.array(estacionalidad)
        # Calcular valor entrenado
        multiplicacion = np.multiply(np.ones(len(self.y)), self.tendencia )
        suma = np.add(multiplicacion, self.nivel)
        y_suavizado_real = np.multiply(self.estacionalidad[0:-self.ciclo],suma)
        self.pronostico_historico = pd.DataFrame(y_suavizado_real)
        return self.pronostico_historico

    # Calcular pronóstico
    def Pronosticar(self, horizonte_pronostico: int):
        if self.nivel is None or self.tendencia is None or self.estacionalidad is None:
            raise ValueError("La regresión aún no se ha calculado.")
        # Calcular los valores de la serie suavizada para los períodos futuros
        multiplicacion = np.multiply(np.arange(1, horizonte_pronostico + 1), self.tendencia[-1] )
        suma = np.add(multiplicacion, self.nivel[-1])
        y_suavizado_pronostico = np.multiply(suma, self.estacionalidad[-horizonte_pronostico::])
        self.pronostico = pd.DataFrame(y_suavizado_pronostico, index=np.arange(self.x[-1] + 1, self.x[-1] + horizonte_pronostico + 1))
        return self.pronostico

class GraficarModelos():
    '''
    GraficarModelos( modelos:[list, tuple] )\n
    Clase que permite visualizar gráficamente los resultados de varios modelos de pronóstico junto con la serie histórica real.\n
    Argumentos:\n
    modelos : List, Tuple
        Lista o tupla de modelos de pronóstico, cada uno de ellos debe tener atributos 'historico', 'pronostico' y 'pronostico_historico'.\n
    Ejemplo:\n
        modelos = [modelo1, modelo2, modelo3]
        graficador = GraficarModelos(modelos)
        graficador.mostrar_grafico()
    '''
    def __init__(self, modelos: Union[List, Tuple]):
        self.modelos = modelos
        fig, ax = plt.subplots()
        historico = self.modelos[0].historico
        colores = plt.cm.get_cmap('Set2',len(modelos)) # Set4 
        ax.plot(historico.index, historico[historico.columns[0]], linewidth=1.3, label='Historico', color='black')
        for o,modelo in enumerate(self.modelos):
            if modelo.nombre_modelo == 'Regresion lineal':
                min = modelo.historico.index.max()+1
                try:
                    max = modelo.pronostico.index.max()
                except:
                    max = modelo.historico.index.max()
                #ax.plot(np.arange(min,max), modelo.b + modelo.m * np.arange(min,max), label=modelo.nombre_modelo, color=colores.colors[o+1])
                ax.plot(np.arange(min,max), modelo.b + modelo.m * np.arange(min,max), color=colores.colors[o])
                ax.plot(np.arange(0,min), modelo.b + modelo.m * np.arange(0,min), label='Pron. '+modelo.titulo_grafico, linestyle='-.', linewidth=0.95, color=colores.colors[o])               
            else:
                #ax.plot(modelo.pronostico.index,modelo.pronostico[modelo.pronostico.columns[0]], label=modelo.nombre_modelo, color=colores.colors[o])    
                try:
                    ax.plot(modelo.pronostico.index,modelo.pronostico[modelo.pronostico.columns[0]], color=colores.colors[o])    
                    ax.plot(modelo.pronostico_historico.index,modelo.pronostico_historico[modelo.pronostico_historico.columns[0]], linestyle='-.', linewidth=0.95, label='Pron. '+modelo.titulo_grafico, color=colores.colors[o])
                except:
                    ax.plot(modelo.pronostico_historico.index,modelo.pronostico_historico[modelo.pronostico_historico.columns[0]], linestyle='-.', linewidth=0.95, label='Pron. '+modelo.titulo_grafico, color=colores.colors[o])
        fig.legend(fontsize='small')
        plt.show()

class ErroresModelos():
    '''
    ErroresModelos( modelos:[list, tuple] )\n  
    Clase que calcula diversas métricas de error para modelos de pronóstico comparando sus resultados con la demanda histórica real.\n
    Métricas calculadas:\n
    Error Absoluto Total (EAT): La suma de los valores absolutos de las diferencias entre las demandas pronosticadas y las demandas históricas.
    Error Absoluto Medio (EAM): El promedio de los valores absolutos de las diferencias entre las demandas pronosticadas y las demandas históricas.
    Error Absoluto Máximo (EAMX): El valor absoluto más grande de las diferencias entre las demandas pronosticadas y las demandas históricas.
    Error Cuadrático Medio (ECM): El promedio de los errores al cuadrado entre las demandas pronosticadas y las demandas históricas.
    Error Porcentual Medio (EPM): El promedio de los errores porcentuales entre las demandas pronosticadas y las demandas históricas.
    Error Porcentual Absoluto Medio (EPAM): El promedio de los valores absolutos de los errores porcentuales entre las demandas pronosticadas y las demandas históricas.
    Desviación Absoluta Media (DAM): La mediana de las diferencias entre las demandas pronosticadas y las demandas históricas.
    Señal de Rastreo (SR): La relación entre el promedio de los errores absolutos y la desviación estándar de los errores absolutos.\n
    Argumentos:\n
    modelos : List, Tuple 
        Lista o tupla de modelos de pronóstico, cada uno de ellos debe tener atributos 'historico' y 'pronostico_historico'.
    Ejemplo:\n
        modelos = [modelo1, modelo2, modelo3]
        errores = ErroresModelos(modelos)
        resultados = errores.Calcular()
        print(resultados)
    '''
    def __init__(self, modelos: Union[List, Tuple]):
        self.modelos = modelos
        self.diccioanrio = {
            'EAT':'Error Absoluto Total',
            'EAM':'Error Absoluto Medio',
            'EAMX':'Error Absoluto Maximo',
            'ECM':'Error Cuadratico Medio',
            'EPM':'Error Porcentual Medio',
            'EPAM':'Error Porcentual Absoluto Medio',
            'DAM':'Desviacion Absoluta Media',
            'SR':'Señal de Rastreo'
        }
        self.Calcular()

    # Calcular errores
    def Calcular(self):
        self.metricas = pd.DataFrame()
        demanda_historica = np.array(self.modelos[0].historico[self.modelos[0].historico.columns[0]])
        for modelo in self.modelos:
            demanda_pronsoticada = np.array(modelo.pronostico_historico[modelo.pronostico_historico.columns[0]])
            # Error Absoluto Total (EAT)
            EAT = np.round(np.nansum(np.abs(demanda_pronsoticada - demanda_historica)),2) 
            self.metricas.loc[modelo.titulo_grafico,"EAT"] = EAT
            # Error Absoluto Medio (EAM)
            EAM = np.round(np.nanmean(np.abs(demanda_pronsoticada - demanda_historica)),2) 
            self.metricas.loc[modelo.titulo_grafico,"EAM"] = EAM
            # Error Absoluto Maximo (EAMX)
            EAMX = np.round(np.nanmax(np.abs(demanda_pronsoticada - demanda_historica)),2) 
            self.metricas.loc[modelo.titulo_grafico,"EAMX"] = EAMX
            # Error Cuadratico Medio (ECM)
            ECM = np.round(np.nanmean((demanda_pronsoticada - demanda_historica)**2),2) 
            self.metricas.loc[modelo.titulo_grafico,"ECM"] = ECM
            # Error Porcentual Medio (EPM)
            EPM = np.round(np.nanmean((demanda_pronsoticada - demanda_historica)/demanda_pronsoticada),2) 
            self.metricas.loc[modelo.titulo_grafico,"EPM"] = EPM
            # Error Porcentual Absoluto Medio (EPAM)
            EPAM = np.round(np.nanmean(np.abs((demanda_pronsoticada - demanda_historica)/demanda_pronsoticada)),2) 
            self.metricas.loc[modelo.titulo_grafico,"EPAM"] = EPAM
            # Desviacion Absoluta Media (DAM)
            DAM = np.round(np.nanmedian(demanda_pronsoticada - demanda_historica),2) 
            self.metricas.loc[modelo.titulo_grafico,"DAM"] = DAM
            # Señal de Rastreo (SR)
            errores_absolutos = np.abs(demanda_pronsoticada - demanda_historica)
            SR = np.round(np.nanmean(errores_absolutos) / np.nanstd(errores_absolutos),2)
            self.metricas.loc[modelo.titulo_grafico,"SR"] = SR
        return self.metricas