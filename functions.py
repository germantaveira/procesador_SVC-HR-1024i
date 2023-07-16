import pandas as pd  # Importa la biblioteca pandas para el análisis de datos
import numpy as np  # Importa la biblioteca numpy para trabajar con matrices y vectores
import matplotlib.pyplot as plt  # Importa la biblioteca matplotlib para graficar datos
import os  # Importa la biblioteca os para interactuar con el sistema operativo
from datetime import datetime, timedelta  # Importa datetime y timedelta para trabajar con fechas y tiempos

# [!] Se requiere el módulo xlsxwriter para guardar las firmas en xlsx
#!pip install xlsxwriter 



##########################################
############# Manejo de .sig #############
##########################################

# Función para transformar el desplazamiento de horas en timedelta
def time_offset(hours_offset):
    return  timedelta(hours=hours_offset)


# Función para listar rutas de los .sig
def list_sig(path):
    """
    Función que recibe una ruta y devuelve una lista con las rutas de archivos que terminan con la extensión '.sig'
    que se encuentran en dicha ruta y en sus subdirectorios.

    Args:
    - path (str): Ruta de directorio a analizar.

    Returns:
    - sig_list (list): Lista de rutas de archivo que terminan con la extensión '.sig'.
    """

    sig_list = []  # Crea una lista vacía llamada sig_list para almacenar las rutas de archivo.

    # Recorre cada directorio, subdirectorio y archivo en la ruta 'path'.
    for dir,subdir,files in os.walk(path):

        # Recorre cada archivo en el directorio actual 'dir'.
        for firma in os.listdir(dir):

            # Divide el nombre de archivo en 'name' y la extensión en 'ext'.
            name, ext = os.path.splitext(firma)

            # Si la extensión del archivo es '.sig', agrega la ruta completa del archivo a la lista 'sig_list'.
            if ext == '.sig':
                sig_list.append(dir+'/'+firma)

    return sig_list  # Devuelve la lista 'sig_list' con las rutas de archivo que terminan con la extensión '.sig'


# Función para abrir el archivo de texto con los datos de la señal SIG
def open_sig(sig_list, hours_offset):
    """
    Abre el archivo de texto con los datos de la señal SIG y los convierte a un diccionario de pandas.DataFrame.
    
    Parameters:
    -----------
    sig_list : list
        Lista de strings con la ubicación y nombre del archivo de texto con los datos de la señal SIG.
    
    Returns:
    --------
    dict_list : list
        Lista de diccionarios con los datos de la señal SIG en pandas.DataFrame.
    """
    dict_list = []
    for file in sig_list:
        with open(file, 'r') as firma:
            # Crear un diccionario vacío
            data_dict = {}
            data_list = []
            # Leer cada línea del archivo
            for line in firma:
                # Verificar si la línea contiene un signo igual
                if '=' in line:
                    # Dividir la línea en el signo igual
                    name, value = line.strip().split('=')
                    # Agregar la entrada de diccionario
                    data_dict[name.strip()] = value.strip()
                    # print(line)
                elif '/*** Spectra Vista SIG Data ***/' in line:
                    None
                elif line.strip():

                    # Dividir la línea en espacios en blanco
                    data = line.strip().split()
                    # Crear una fila de datos para el DataFrame (cambiando las comas por puntos)
                    row = {
                        'longitud_onda': float(data[0].replace(',','.')),
                        'radiancia_original': float(data[1].replace(',','.')),
                        'target_original': float(data[2].replace(',','.')),
                        'reflectancia': float(data[3].replace(',','.'))
                    }
                    # Agregar la fila de datos a la lista
                    data_list.append(row)

        # Se convierten los valores del diccionario a tabla
        for k in data_dict:
            data_dict[k] = data_dict[k].split(',')

        # Le agrego las keys 'date_refere' con la fecha en datetime
        data_dict['date_radiancia'] = pd.to_datetime(data_dict['time'][0][0:19], format='%d/%m/%Y %H:%M:%S') + time_offset(hours_offset=hours_offset)
        data_dict['date_target'] = pd.to_datetime(data_dict['time'][1][1:20], format='%d/%m/%Y %H:%M:%S') + time_offset(hours_offset=hours_offset)
        data_dict['date_dt'] = datetime.strptime(data_dict['time'][1][1:11], '%d/%m/%Y').date() + time_offset(hours_offset=hours_offset)
        data_dict['time_target'] = data_dict['date_target'].strftime("%H:%M:%S")
        data_dict['id_date'] = data_dict['date_dt'].strftime('%Y%m%d')
        # Se crea un dataframe con los valores de reflectancias y se incluye en el diccionario en el key 'data'
        data = pd.DataFrame(data_list)
        data['radiancia'] = (data.radiancia_original)*10**(-3) # Escalado de radiancias
        data['target'] = (data.target_original)*10**(-3) # Escalado de radiancias

        data = data.reindex(columns=['longitud_onda','radiancia_original','target_original','radiancia','target','reflectancia'])

        data_dict['data'] = data
        
        dict_list.append(data_dict)

    return dict_list


# Función para obtener una lista con las fechas de las firmas.
def obtener_fechas(dic_firmas_por_fecha):

    # Crear una lista para almacenar las fechas
    fechas = []

    # Iterar sobre el diccionario 'dic_firmas_por_fecha' y extraer las fechas
    for key in dic_firmas_por_fecha.keys():
        fechas.append(key)

    # Ordenar las fechas de manera ascendente
    fechas = sorted(fechas)

    return fechas

##########################################
########### Manejo de metadatos ##########
##########################################

def coods_converter(longitude, latitude):
    """
    Convierte las coordenadas de grados, minutos y segundos a decimal y devuelve una lista de coordenadas.

    Args:
    longitude (list): lista de dos cadenas de caracteres que representan la longitud de la coordenada. Ejemplo: ['05854.5700W     ', ' 05854.5408W']
    latitude (list): lista de dos cadenas de caracteres que representan la latitud de la coordenada. Ejemplo: ['24843.5608S    ', ' 24843.5682S']

    Returns:
    list: Una lista de dos sublistas, la primera representa las coordenadas de referencia y la segunda representa las coordenadas objetivo. Cada sublista tiene dos elementos, la longitud y la latitud.
    """

    # Calculo de la coordenada de referencia ej:  # longitude	= ['05854.5700W     ', ' 05854.5408W']
    if longitude[0] == '':
        longitude_0 = '00000.0000W     '
    else: 
        longitude_0 = longitude[0]

    grados = int(longitude_0[0:3])
    minutos = int(longitude_0[3:5])
    segundos = float('0.'+longitude_0[6:10])
    segundos = segundos*60

    long =  - (grados + (minutos/60) + (segundos/3600))

    if latitude[0] == '':
        latitude_0 = '0000.0000S      '
    else: 
        latitude_0 = latitude[0]
    
    grados = int(latitude_0[0:2])
    minutos = int(latitude_0[2:4])
    segundos = float('0.'+latitude_0[5:9])

    lat =  - (grados + (minutos/60) + (segundos/3600))

    coord_ref = [long,lat]

    # Cordenada target # ej: longitude	= ['05854.5700W     ', ' 05854.5408W']

    grados = int(longitude[1][1:4])
    minutos = int(longitude[1][4:6])
    segundos = float('0.'+longitude[1][7:11])
    segundos = segundos*60

    long =  - (grados + (minutos/60) + (segundos/3600))

    latitude[0]
    grados = int(latitude[1][1:3])
    minutos = int(latitude[1][3:5])
    segundos = float('0.'+latitude[1][6:10])

    lat =  - (grados + (minutos/60) + (segundos/3600))
        
    coord_sample = [long,lat]

    coords = [coord_ref, coord_sample]

    return coords

def agregar_coordenadas(dic_firmas_por_fecha):
    '''
    Se agregan las coordenadas en grados decimales en coordenadas_radiancia y coordenadas_target como metadato de cada firma
    '''
    for fecha in obtener_fechas(dic_firmas_por_fecha):    
        for firma in dic_firmas_por_fecha[fecha]:
            try:
                res = coods_converter(firma['longitude'],firma['latitude'])
                firma['coordenadas_radiancia'] = res[0]
                firma['coordenadas_target'] = res[1]
            except:
                print(f"[!] error el convertir las coordenadas de los metadatos de {firma['name']}.")

    return dic_firmas_por_fecha


# Función para agregar metadatos a cada firma en base a la tabla de datos de campo
def agregar_metadatos(dic_firmas_por_fecha, cobertura, tabla_campo):
    
    # Se crea una lista para almacenar las fechas. Estas servirán para iterar en el diccionario que agrupa las por fechas.
    fechas = obtener_fechas(dic_firmas_por_fecha)
    
    # Iterar sobre cada fecha en la lista 'fechas'

    for fecha in fechas:
        # Inicializar un contador en cero
        n = 0
        # Iterar sobre cada firma en la lista de firmas correspondiente a la fecha actual
        for firma in dic_firmas_por_fecha[fecha]:
            # Incrementar el contador en 1 y almacenar el valor en la firma actual
            n += 1
            firma['n_firma'] = n
            # Filtrar la tabla 'tabla_campo' para obtener la información correspondiente a la firma actual
            filtro_date = tabla_campo.loc[(tabla_campo.id_date == firma['id_date'])]
            filtro_id = filtro_date.loc[(filtro_date.n_firma == firma['n_firma'])]
            # Verificar si el filtro devuelve algún resultado
            if filtro_id.any()[0]:
                # Si se encontraron resultados, almacenar la información correspondiente en la firma actual
                firma['zona'] = int(filtro_id.zona.values[0])
                firma['nombre_zona'] = filtro_id.nombre_zona.values[0]
                firma['distancia'] = filtro_id.distancia.values[0]
                firma['cobertura'] = cobertura
            else:
                # Si no se encontraron resultados, almacenar valores nulos en la firma actual
                firma['zona'] = None
                firma['nombre_zona'] = None
                firma['distancia'] = None
                firma['cobertura'] = None
            ## Generar una ID única para cada firma
            # Obtener los valores necesarios para construir la ID
            n_firma = firma['n_firma']
            zona = firma['zona']
            distancia = firma['distancia']
            date = firma['date_dt'].strftime('%Y%m%d')
            # Almacenar la ID en la firma actual
            firma['id_firma'] = '{fecha}_{zona}_{distancia}_{num_firma:02}'.format(fecha=date, num_firma=n_firma, zona=zona, distancia=distancia)

    return dic_firmas_por_fecha

# Agrupa las firmas por fecha. Se genera un diccionario nuevo, cada key es la fecha de cada día y apunta a una lista con las firmas de ese día.
def agrupar_firmas(firmas, hours_offset):
    '''
    Las firmas son agrupadas por día. Ahora las firmas se se agrupan en un diccionario,
    donde cada key es la fecha del día en la que se tomaron las firmas.
    Las firmas dentro de cada fecha se agrupan en listas.
    '''
    firmas = sorted(firmas, key=lambda x: datetime.strptime(x['time'][1][1:20], '%d/%m/%Y %H:%M:%S'))

    # Crear un diccionario vacío para cada día
    dic_firmas_por_fecha = {}

    # Agrupar los diccionarios por fecha
    for firma in firmas:

        # Extrae la fecha de la firma, elimina las horas/minutos/segundos y ajusta la zona horaria (UTC -5) para
        # obtener la fecha correspondiente al huso horario de Colombia.
        fecha = datetime.strptime(firma['time'][1][1:11], '%d/%m/%Y').date() + time_offset(hours_offset=hours_offset)

        # Si la fecha ya existe en el diccionario 'dic_firmas_por_fecha', agrega la firma a la lista correspondiente.
        if fecha in dic_firmas_por_fecha:
            dic_firmas_por_fecha[fecha].append(firma)

        # Si la fecha no existe en el diccionario 'dic_firmas_por_fecha', crea una nueva entrada con la fecha y una lista
        # que contiene la firma actual.
        else:
            dic_firmas_por_fecha[fecha] = [firma]

    return dic_firmas_por_fecha


def procesar_firmas_ind(firmas, hours_offset, cobertura, tabla_campo):
    # Las firmas se agrupan por día en un diccionario
    # Cada key del diccionario es la fecha del día en el que se tomaron las firmas
    # Las firmas dentro de cada fecha se agrupan en listas
    dic_firmas_por_fecha = agrupar_firmas(firmas, hours_offset)

    # A cada firma se le agregan metadatos en base a la tabla de datos de zonas tomadas en campo
    dic_firmas_por_fecha = agregar_metadatos(dic_firmas_por_fecha, cobertura, tabla_campo)

    dic_firmas_por_fecha = agregar_coordenadas(dic_firmas_por_fecha)

    return dic_firmas_por_fecha

##########################################
############# Exportr en xlsx ############
##########################################

# Función para exportar todos los metadatos y firmas en una misma hoja de excel

def export_xlsx(path_out, dic_firmas, cobertura, prom=False):
    ''' Función para exportar todos los metadatos y firmas en una misma hoja de excel '''
    if prom == True:
        tipo = 'promedio'
    else:
        tipo = 'individuales'

    fechas = obtener_fechas(dic_firmas)
    year = fechas[0].year
    file_name = f'firmas_{cobertura}_{tipo}_{year}.xlsx'

    with pd.ExcelWriter(path_out+file_name) as writer:
        for fecha in fechas:
            for firma in dic_firmas[fecha]:  
                
                metadata = pd.DataFrame([[key, firma[key]] for key in firma.keys()], columns=['metadata_item', 'value'])
                ubic_data = metadata.loc[metadata.metadata_item == 'data'].index[0]
                metadata = metadata.drop([ubic_data], axis=0)
                metadata = metadata.set_index('metadata_item')
                sheet_name = firma['id_firma']

                metadata.to_excel(writer, sheet_name=sheet_name, startrow=0, startcol=0)
                
                data = firma['data'].set_index('longitud_onda')
                data.to_excel(writer, sheet_name=sheet_name, startrow=1+len(metadata)+3, startcol=0)

##########################################
############# Visualización ##############
##########################################

def plot_firmas_individuales(dic_firmas_por_fecha, num_zona, distancia):

    for fecha in obtener_fechas(dic_firmas_por_fecha):
        diccionarios_seleccionados = []

        try:
            diccionarios_seleccionados = [diccionario for diccionario in dic_firmas_por_fecha[fecha] if diccionario['zona'] == num_zona and 
                                diccionario['distancia'] == distancia]
        except:
            None

        fig, ax = plt.subplots(figsize=(10,6))

        if diccionarios_seleccionados != []:
            for firma in diccionarios_seleccionados:
                
                nombre_firma = firma['id_firma']
                longitud_onda = firma['data'].longitud_onda
                espectro_target = firma['data'].target
                espectro_radiancia = firma['data'].radiancia
                espectro_reflectancia = firma['data'].reflectancia

                fecha = firma['date_radiancia'].date()
                nombre_zona = firma['nombre_zona']
                
                ax.plot(longitud_onda, espectro_reflectancia, label=nombre_firma)
                # ax.plot(longitud_onda, espectro_target, label=nombre_firma)
                # ax.plot(longitud_onda, espectro_radiancia, label='E')

                # ax.set_xlim(750,780)
                ax.set_xlabel('Longitud de onda')
                ax.set_ylabel('Reflectancia')
                ax.set_title(f'Firmas espectrales del día {fecha} // {nombre_zona}')
                ax.legend()

            plt.show()
            
        else:
            for firma in diccionarios_seleccionados:
                longitud_onda = firma['data'].longitud_onda
                espectro_tagret = [0]*len(longitud_onda)
                espectro_radiancia = [0]*len(longitud_onda)
                espectro_reflectancia = [0]*len(longitud_onda)

                fecha = firma['date_radiancia'].date()
                nombre_zona = 'no data'
                
                ax.plot(longitud_onda, espectro_reflectancia, label='nodata')
                # ax.plot(longitud_onda, espectro_referencia, label='E')

                ax.set_xlabel('Longitud de onda')
                ax.set_ylabel('Reflectancia')
                ax.set_title(f'{fecha} // {nombre_zona}')
                ax.legend()

                plt.show()


# Función de ploteo de firmas individuales
def plot_firmas(firmas_fecha, zona, distancia, plot, x_lim):

    fechas = list(firmas_fecha.keys())

    for fecha in fechas:
        diccionarios_seleccionados = []

        try:
            diccionarios_seleccionados = [diccionario for diccionario in firmas_fecha[fecha] if str(diccionario['zona']) == str(zona) and 
                                str(diccionario['distancia']) == str(distancia)]
        except:
            None

        fig, ax = plt.subplots(figsize=(10,6))

        if diccionarios_seleccionados != []:
            for firma in diccionarios_seleccionados:
                
                nombre_firma = firma['id_firma']
                longitud_onda = firma['data'].longitud_onda
                espectro_target = firma['data'].target
                espectro_radiancia = firma['data'].radiancia
                espectro_reflectancia = firma['data'].reflectancia

                try:
                    fecha = firma['date_radiancia'].date()
                    # nombre_zona = firma['nombre_zona']
                except:
                    fecha = datetime.strptime(firma['id_firma'].split('_')[0], '%Y%m%d').date()
                    # nombre_zona = None

                if plot == 'rad':
                    ax.plot(longitud_onda, espectro_target, label=nombre_firma)
                    ax.plot(longitud_onda, espectro_radiancia, label='E')
                    eje_y = 'W/m²µm¹sr¹'
                    titulo = 'Radiancia'
                else:
                    ax.plot(longitud_onda, espectro_reflectancia, label=nombre_firma)
                    eje_y = '%'
                    titulo = 'Reflectancia'
                
                nombre_zona = firma['nombre_zona']

                ax.set_xlim(x_lim)
                ax.set_xlabel('Longitud de onda (nm)')
                ax.set_ylabel(f'{eje_y}')
                ax.set_title(f'{titulo} del día {fecha} // {nombre_zona}')
                ax.legend()
                
                plt.grid()
                plt.show()
            
        else:
            
            for firma in diccionarios_seleccionados:

                longitud_onda = firma['data'].longitud_onda
                espectro_tagret = [0]*len(longitud_onda)
                espectro_radiancia = [0]*len(longitud_onda)
                espectro_reflectancia = [0]*len(longitud_onda)
                
                try:
                    fecha = firma['date_radiancia'].date()
                except:
                    fecha = datetime.strptime(firma['id_firma'].split('_')[0], '%Y%m%d').date()

                nombre_zona = 'no data'
                
                ax.plot(longitud_onda, espectro_reflectancia, label='nodata')
                # ax.plot(longitud_onda, espectro_referencia, label='E')

                ax.set_xlabel('Longitud de onda (nm)')
                ax.set_ylabel('Reflectancia')
                ax.set_title(f'{fecha} // {nombre_zona}')
                ax.legend()
                
                plt.grid()
                plt.show()

##########################################
########## Promedio de firmas ############
##########################################
def promediar_firmas(dic_firmas_por_fecha):
    firmas_prom = []

    for fecha in obtener_fechas(dic_firmas_por_fecha):

        zonas_dia = []
        distancias = []

        for firma in dic_firmas_por_fecha[fecha]:
            if firma["zona"] != None:
                distancias.append(firma['distancia'])
            if firma["zona"] != None:
                zonas_dia.append(int(firma["zona"]))

        distancias = list(dict.fromkeys(distancias))
        zonas = list(dict.fromkeys(zonas_dia))
        
        for zona in zonas:
            for distancia in distancias:
                df = pd.DataFrame()
                df_prom = pd.DataFrame()
                col_radiancias = []
                col_targets = []
                col_reflectancias = []

                diccionarios_seleccionados = [diccionario for diccionario in dic_firmas_por_fecha[fecha] if
                                            diccionario['zona'] == zona and diccionario['distancia'] == distancia]
                # firmas_zona = None
                
                for firmas_zona in diccionarios_seleccionados:
                    name = firmas_zona['name']
                    df_prom['longitud_onda'] = firmas_zona["data"].longitud_onda
                    df[f'rad_{name}'] = firmas_zona["data"].radiancia
                    col_radiancias.append(f'rad_{name}')
                    df[f'targ_{name}'] = firmas_zona["data"].target
                    col_targets.append(f'targ_{name}')
                    df[f'ref_{name}'] = firmas_zona["data"].reflectancia
                    col_reflectancias.append(f'ref_{name}')

                    df_prom['radiancia'] = df[col_radiancias].mean(axis=1)
                    df_prom['target'] = df[col_targets].mean(axis=1)
                    df_prom['reflectancia'] = df[col_reflectancias].mean(axis=1)
                    
                firma_prom = diccionarios_seleccionados[0].copy()
                firma_prom['data'] = df_prom
                firma_prom['zona'] = zona

                # Genero una ID para cada promedio de firma
                zona = firma_prom['zona']
                distancia = firma_prom['distancia']
                date = firma_prom['date_dt'].strftime('%Y%m%d')
                firma_prom['id_firma'] = '{fecha}_{zona}_{distancia}'.format(fecha=date, zona=zona, distancia=distancia)

                firmas_prom.append(firma_prom)

    return firmas_prom


# Vinculo con dataset de datos ambientales

def vincular_amb_data(path_tabla_amb,firmas_prom):

    # Lee el archivo CSV y omite la primera fila
    tabla_campo_amb = pd.read_csv(path_tabla_amb, skiprows=1)

    # Agrupa los datos por fecha y zona, calculando el valor medio de cada grupo
    tabla_campo_amb = tabla_campo_amb.groupby([tabla_campo_amb['fecha'], 'zona']).mean()

    # Crea una lista de columnas únicas de la tabla
    cols = list(set(tabla_campo_amb.columns))

    # Reinicia el índice para convertir las columnas de fecha y zona en columnas regulares
    tabla_campo_amb = tabla_campo_amb.reset_index()

    # Convierte la columna de fecha de formato de cadena de caracteres a formato de fecha y extrae el año, mes y día de la fecha
    tabla_campo_amb['id_date'] = pd.to_datetime(tabla_campo_amb['fecha'], format='%d/%m/%Y').dt.strftime('%Y%m%d')

    # Convierte la columna de zona de formato numérico a formato de cadena de caracteres
    tabla_campo_amb['zona'] = tabla_campo_amb['zona'].astype(str)

    # Crea una nueva columna "id_zona" concatenando la columna de fecha y la columna de zona
    tabla_campo_amb['id_zona'] = tabla_campo_amb['id_date'] +  '_' + tabla_campo_amb['zona']

    # Completa y arregla los metadatos para cada firma en firmas_prom
    for firma in firmas_prom:
        # Obtiene la id de zona de la firma actual
        id_firma = firma['id_firma'][0:-2]

        # Itera a través de todas las columnas en la tabla
        for i in range(len(cols)):
            col = cols[i]
            # Comprueba si la columna actual está en la tabla para la zona actual de la firma
            if tabla_campo_amb.loc[(tabla_campo_amb.id_zona == id_firma)][f'{col}'].any():
                # Si la columna está en la tabla, extrae el valor de la celda correspondiente y lo agrega al diccionario de firma
                ncol = tabla_campo_amb.loc[(tabla_campo_amb.id_zona == id_firma)][f'{col}'].values[0]
                firma[f'{col}_zona'] = ncol
        
        # Agrega otros metadatos
        firma['id_units'] = 'W/m²µm¹sr¹'

        # Borra los metadatos que no se necesitan
        keys_borrar = ['name', 'external data set1','external data set2','external data dark','temp','battery','error','comm','memory slot']
        for key_borrar in keys_borrar:
            del firma[key_borrar]
    return firmas_prom

# Función para agrupar
def agrupar_firmas_prom(firmas_prom):
    # Se agrupan las firmas por día

    # Se crea un diccionario vacío para cada día
    dic_firmas_por_fecha_prom = {}

    # Se itera a través de cada firma en la lista de firmas_prom y se agrupan por fecha
    for firma in firmas_prom:
        fecha = firma['date_dt']
        if fecha in dic_firmas_por_fecha_prom:
            dic_firmas_por_fecha_prom[fecha].append(firma)
        else:
            dic_firmas_por_fecha_prom[fecha] = [firma]
    return dic_firmas_por_fecha_prom

# Promedio de medidas por zona y vínculo con datos ambientales de campo
def promediar_firmas_amb(dic_firmas_por_fecha, path_tabla_amb):
    # Calcula el promedio de las firmas por zona
    firmas_prom = promediar_firmas(dic_firmas_por_fecha)

    # Vincula los datos ambientales de campo a las firmas promediadas
    firmas_prom = vincular_amb_data(path_tabla_amb, firmas_prom)

    # Agrupa las firmas promediadas por fecha
    dic_firmas_por_fecha_prom = agrupar_firmas_prom(firmas_prom)
    
    return dic_firmas_por_fecha_prom
